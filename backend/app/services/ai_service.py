import uuid
from datetime import date, datetime, timezone, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.ai_client import ai_client
from app.core.prompts import (
    RISK_SCORING_SYSTEM, RISK_SCORING_USER,
    BEHAVIOR_ANALYSIS_SYSTEM, BEHAVIOR_ANALYSIS_USER,
    WARNING_GENERATION_SYSTEM, WARNING_GENERATION_USER,
    EXECUTIVE_REPORT_SYSTEM, EXECUTIVE_REPORT_USER,
)
from app.models.ai import RiskScore, AIReport, AIUsageLog, AIWarning
from app.models.attendance import DailyRecord, MonthlySummary, WarningLog
from app.models.employee import EmployeeProfile
from app.models.department import Department


class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _log_usage(self, feature: str, result: dict, employee_id: str | None = None):
        log = AIUsageLog(
            feature=feature, model=result.get("model", "gpt-4o-mini"),
            prompt_tokens=result.get("prompt_tokens", 0), completion_tokens=result.get("completion_tokens", 0),
            total_tokens=result.get("total_tokens", 0), cost_usd=result.get("cost", 0.0),
            latency_ms=result.get("latency", 0), status="error" if result.get("error") else "success",
            error_message=result.get("error"), employee_id=employee_id,
        )
        self.db.add(log)
        await self.db.flush()

    async def _compute_features(self, employee_id: str, days: int = 90) -> dict:
        cutoff_date = date.today() - timedelta(days=days)
        result = await self.db.execute(
            select(DailyRecord).where(and_(DailyRecord.employee_id == employee_id, DailyRecord.date >= cutoff_date)).order_by(DailyRecord.date)
        )
        records = list(result.scalars().all())
        if not records:
            return {"total_days": 0, "days_present": 0, "late_count": 0, "late_pct": 0, "missing_count": 0, "avg_checkin": "N/A", "checkin_trend": "stable", "max_streak": 0, "dow_pattern": {}, "monthly_history": "No data"}

        total_days = len(records)
        days_present = sum(1 for r in records if r.check_in)
        late_count = sum(1 for r in records if r.late_flag)
        missing_count = sum(1 for r in records if r.missing_punch)
        late_pct = round((late_count / total_days * 100), 1) if total_days > 0 else 0

        checkin_times = [r.check_in.hour * 60 + r.check_in.minute for r in records if r.check_in]
        avg_checkin_min = sum(checkin_times) // len(checkin_times) if checkin_times else 0
        avg_checkin = f"{avg_checkin_min // 60}:{avg_checkin_min % 60:02d}"

        max_streak = 0
        current_streak = 0
        for r in records:
            if r.late_flag:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dow_pattern = {}
        for r in records:
            if r.late_flag:
                dow = dow_names[r.date.weekday()]
                dow_pattern[dow] = dow_pattern.get(dow, 0) + 1

        if len(records) >= 14:
            recent_late = sum(1 for r in records[-14:] if r.late_flag)
            older_late = sum(1 for r in records[:-14] if r.late_flag) if len(records) > 14 else 0
            recent_rate = recent_late / min(14, len(records[-14:]))
            older_rate = older_late / max(1, len(records[:-14])) if len(records) > 14 else 0
            checkin_trend = "declining" if recent_rate > older_rate * 1.2 else "improving" if recent_rate < older_rate * 0.8 else "stable"
        else:
            checkin_trend = "insufficient_data"

        monthly = {}
        for r in records:
            month = r.date.strftime("%Y-%m")
            if month not in monthly:
                monthly[month] = {"total": 0, "late": 0}
            monthly[month]["total"] += 1
            if r.late_flag:
                monthly[month]["late"] += 1
        monthly_history = "\n".join([f"- {m}: {v['total']} days, {v['late']} late" for m, v in sorted(monthly.items())])

        return {"total_days": total_days, "days_present": days_present, "late_count": late_count, "late_pct": late_pct, "missing_count": missing_count, "avg_checkin": avg_checkin, "checkin_trend": checkin_trend, "max_streak": max_streak, "dow_pattern": dow_pattern, "monthly_history": monthly_history}

    def _rule_based_risk(self, features: dict) -> dict:
        score = min(100, features["late_count"] * 10 + features["max_streak"] * 5 + (20 if features["checkin_trend"] == "declining" else 0))
        level = "CRITICAL" if score >= 76 else "HIGH" if score >= 51 else "MEDIUM" if score >= 26 else "LOW"
        factors = []
        if features["late_pct"] > 20:
            factors.append(f"High late arrival rate: {features['late_pct']}% of days")
        elif features["late_pct"] > 10:
            factors.append(f"Moderate late arrival rate: {features['late_pct']}% of days")
        if features["max_streak"] >= 3:
            factors.append(f"Consecutive late streak of {features['max_streak']} days")
        if features["checkin_trend"] == "declining":
            factors.append("Attendance trend is declining")
        if features["missing_count"] > 0:
            factors.append(f"{features['missing_count']} missing punch records")
        if not factors:
            factors.append("Attendance pattern within acceptable range")
        recommendations = []
        if score >= 51:
            recommendations.append("Schedule a one-on-one meeting to discuss attendance")
        if score >= 26:
            recommendations.append("Monitor attendance closely for the next 2 weeks")
        if features["checkin_trend"] == "declining":
            recommendations.append("Investigate potential root causes for declining attendance")
        if not recommendations:
            recommendations.append("Continue monitoring - no immediate action needed")
        return {"score": score, "level": level, "reasoning": f"Rule-based scoring: {features['late_count']} late arrivals in {features['total_days']} days ({features['late_pct']}%), max streak {features['max_streak']}, trend {features['checkin_trend']}", "factors": {"late_rate": f"{features['late_pct']}%", "trend": features["checkin_trend"], "streak": str(features["max_streak"]), "details": factors}, "recommendations": recommendations}

    def _rule_based_behavior(self, features: dict) -> dict:
        patterns = []
        if features["dow_pattern"]:
            worst_day = max(features["dow_pattern"], key=features["dow_pattern"].get)
            patterns.append(f"Most late on {worst_day} ({features['dow_pattern'][worst_day]} times)")
        if features["avg_checkin"] != "N/A":
            patterns.append(f"Average check-in time: {features['avg_checkin']}")
        if features["max_streak"] > 1:
            patterns.append(f"Has {features['max_streak']}-day consecutive late streak")
        trends = [{"pattern": "Late arrivals", "frequency": f"{features['late_pct']}%", "direction": features["checkin_trend"]}]
        anomalies = []
        if features["missing_count"] > 0:
            anomalies.append({"description": f"{features['missing_count']} missing punch records detected", "severity": "medium"})
        causes = []
        if features["checkin_trend"] == "declining":
            causes.append("Potential schedule or commute issues")
        if features["max_streak"] >= 3:
            causes.append("Possible burnout or disengagement")
        recommendations = []
        if features["late_pct"] > 15:
            recommendations.append("Schedule attendance review meeting")
        if features["checkin_trend"] == "declining":
            recommendations.append("Investigate underlying causes")
        if not recommendations:
            recommendations.append("Continue monitoring attendance patterns")
        return {"behavior_summary": f"Employee has {features['late_count']} late arrivals in {features['total_days']} days ({features['late_pct']}%). Average check-in: {features['avg_checkin']}. Trend: {features['checkin_trend']}.", "patterns": patterns, "anomalies": anomalies, "trends": trends, "potential_causes": causes, "recommendations": recommendations, "confidence": "HIGH"}

    async def score_risk(self, employee_id: str) -> dict:
        emp_result = await self.db.execute(select(EmployeeProfile).where(EmployeeProfile.employee_id == employee_id))
        employee = emp_result.scalar_one_or_none()
        if not employee:
            return {"error": "Employee not found"}
        features = await self._compute_features(employee_id)
        dept_name = "Unknown"
        if employee.department_id:
            dept = await self.db.get(Department, employee.department_id)
            if dept:
                dept_name = dept.name

        user_prompt = RISK_SCORING_USER.format(name=employee.name or employee.employee_id, employee_id=employee.employee_id, department=dept_name, designation=employee.designation or "Unknown", days=90, **features)
        result = await ai_client.generate_json(system_prompt=RISK_SCORING_SYSTEM, user_prompt=user_prompt, temperature=0.3)
        await self._log_usage("risk_scoring", result, employee_id)

        if result.get("error") or not result.get("data"):
            data = self._rule_based_risk(features)
        else:
            data = result["data"]
            if not isinstance(data.get("score"), int) or not (0 <= data["score"] <= 100):
                data = self._rule_based_risk(features)

        risk = RiskScore(employee_id=employee_id, name=employee.name or employee.employee_id, score=data["score"], level=data["level"], reasoning=data.get("reasoning", ""), recommendations=data.get("recommendations", []), factors=data.get("factors", {}), model_used=result.get("model", "rule-based"), tokens_used=result.get("tokens", 0), cost_usd=result.get("cost", 0.0), latency_ms=result.get("latency", 0))
        self.db.add(risk)
        await self.db.flush()

        return {"employee_id": employee_id, "name": employee.name or employee.employee_id, "score": data["score"], "level": data["level"], "reasoning": data.get("reasoning", ""), "recommendations": data.get("recommendations", []), "factors": data.get("factors", {}), "calculated_at": risk.calculated_at}

    async def analyze_behavior(self, employee_id: str) -> dict:
        emp_result = await self.db.execute(select(EmployeeProfile).where(EmployeeProfile.employee_id == employee_id))
        employee = emp_result.scalar_one_or_none()
        if not employee:
            return {"error": "Employee not found"}
        features = await self._compute_features(employee_id, days=90)
        dept_name = "Unknown"
        if employee.department_id:
            dept = await self.db.get(Department, employee.department_id)
            if dept:
                dept_name = dept.name

        user_prompt = BEHAVIOR_ANALYSIS_USER.format(name=employee.name or employee.employee_id, employee_id=employee.employee_id, department=dept_name, designation=employee.designation or "Unknown", days=90, attendance_data=f"Total days: {features['total_days']}, Present: {features['days_present']}, Late: {features['late_count']} ({features['late_pct']}%), Missing: {features['missing_count']}", dow_distribution=", ".join([f"{k}: {v}" for k, v in features["dow_pattern"].items()]) or "No pattern", monthly_trend=features["monthly_history"])
        result = await ai_client.generate_json(system_prompt=BEHAVIOR_ANALYSIS_SYSTEM, user_prompt=user_prompt, temperature=0.4)
        await self._log_usage("behavior_analysis", result, employee_id)

        if result.get("error") or not result.get("data"):
            data = self._rule_based_behavior(features)
        else:
            data = result["data"]

        return {"employee_id": employee_id, "name": employee.name or employee.employee_id, "behavior_summary": data.get("behavior_summary", ""), "patterns": data.get("patterns", []), "anomalies": data.get("anomalies", []), "trends": data.get("trends", []), "potential_causes": data.get("potential_causes", []), "recommendations": data.get("recommendations", []), "confidence": data.get("confidence", "MEDIUM")}

    async def generate_warning(self, employee_id: str, strike_level: int, context: dict) -> dict:
        warning_types = {1: "friendly", 2: "formal", 3: "urgent"}
        warning_type = warning_types.get(strike_level, "friendly")
        extra_context = "This is the FINAL WARNING. A mandatory HR meeting has been scheduled." if strike_level == 3 else ""
        user_prompt = WARNING_GENERATION_USER.format(name=context.get("name", employee_id), employee_id=employee_id, warning_type=warning_type, strike_level=strike_level, date=context.get("date", str(date.today())), check_in=context.get("check_in", "N/A"), late_count=context.get("late_count", strike_level), extra_context=extra_context)
        result = await ai_client.generate_json(system_prompt=WARNING_GENERATION_SYSTEM, user_prompt=user_prompt, temperature=0.5)
        await self._log_usage("warning_generation", result, employee_id)

        if result.get("error") or not result.get("data"):
            subjects = {1: "Friendly Attendance Reminder", 2: "Formal Attendance Warning", 3: "Final Attendance Warning"}
            bodies = {1: f"Hi {context.get('name', 'Employee')}, this is a friendly reminder about your late arrival on {context.get('date', 'recent date')}.", 2: f"Hi {context.get('name', 'Employee')}, this is a formal warning regarding your repeated late arrivals this month.", 3: f"Hi {context.get('name', 'Employee')}, this is a FINAL WARNING. You have reached 3 late arrivals. A mandatory HR meeting is scheduled."}
            data = {"subject": subjects.get(strike_level, subjects[1]), "body": bodies.get(strike_level, bodies[1])}
        else:
            data = result["data"]

        warning = AIWarning(employee_id=employee_id, name=context.get("name", employee_id), strike_level=strike_level, warning_type=warning_type, subject=data.get("subject", ""), body=data.get("body", ""), tone=warning_type, model_used=result.get("model", "rule-based"), tokens_used=result.get("tokens", 0), cost_usd=result.get("cost", 0.0), latency_ms=result.get("latency", 0))
        self.db.add(warning)
        await self.db.flush()

        return {"employee_id": employee_id, "name": context.get("name", employee_id), "strike_level": strike_level, "warning_type": warning_type, "subject": data.get("subject", ""), "body": data.get("body", ""), "tone": warning_type}

    async def generate_executive_report(self, report_type: str = "weekly", generated_by: str = "System") -> dict:
        today = date.today()
        total_result = await self.db.execute(select(func.count(EmployeeProfile.id)))
        total_employees = total_result.scalar()
        today_records_result = await self.db.execute(select(DailyRecord).where(DailyRecord.date == today))
        today_records = list(today_records_result.scalars().all())
        late_today = sum(1 for r in today_records if r.late_flag)
        attendance_rate = round((len(today_records) / total_employees * 100), 1) if total_employees > 0 else 0

        dept_result = await self.db.execute(select(Department))
        departments = list(dept_result.scalars().all())
        dept_stats = []
        for dept in departments:
            emp_count_result = await self.db.execute(select(func.count(EmployeeProfile.id)).where(EmployeeProfile.department_id == dept.id))
            emp_count = emp_count_result.scalar()
            dept_stats.append(f"- {dept.name}: {emp_count} employees")

        current_month = today.strftime("%Y-%m")
        violators_result = await self.db.execute(select(MonthlySummary).where(and_(MonthlySummary.month_year == current_month, MonthlySummary.late_count > 0)).order_by(MonthlySummary.late_count.desc()).limit(5))
        violators = list(violators_result.scalars().all())
        violator_str = "\n".join([f"- {v.name}: {v.late_count} late arrivals" for v in violators]) or "None"

        warnings_result = await self.db.execute(select(func.count(WarningLog.id)).where(WarningLog.month_year == current_month))
        warnings_issued = warnings_result.scalar()

        user_prompt = EXECUTIVE_REPORT_USER.format(report_type=report_type, period=f"{today.strftime('%B %Y')}", generated_by=generated_by, total_employees=total_employees, attendance_rate=attendance_rate, late_count=late_today, late_pct=round((late_today / len(today_records) * 100), 1) if today_records else 0, missing_count=sum(1 for r in today_records if r.missing_punch), warnings_issued=warnings_issued, department_stats="\n".join(dept_stats) or "No departments", top_violators=violator_str, mom_comparison="Data available from previous months")
        result = await ai_client.generate_json(system_prompt=EXECUTIVE_REPORT_SYSTEM, user_prompt=user_prompt, temperature=0.4)
        await self._log_usage("executive_report", result)

        if result.get("error") or not result.get("data"):
            data = {"title": f"{report_type.title()} Attendance Report - {today.strftime('%B %Y')}", "executive_summary": f"Report generated for {total_employees} employees. {late_today} late arrivals today. Attendance rate: {attendance_rate}%.", "key_metrics": {"total_employees": total_employees, "attendance_rate": f"{attendance_rate}%", "late_rate": f"{round(late_today/max(1,len(today_records))*100, 1)}%", "total_violations": late_today, "warnings_issued": warnings_issued}, "department_insights": [{"department": d.name, "insight": f"{d.name} department"} for d in departments], "trends": [], "recommendations": ["Review attendance policies", "Monitor high-risk employees"], "risk_employees": []}
        else:
            data = result["data"]

        report = AIReport(report_type=report_type, title=data.get("title", f"{report_type.title()} Report"), content=str(data), model_used=result.get("model", "rule-based"), tokens_used=result.get("tokens", 0), cost_usd=result.get("cost", 0.0), latency_ms=result.get("latency", 0))
        self.db.add(report)
        await self.db.flush()

        return {"id": str(report.id), "report_type": report_type, "title": data.get("title", ""), "content": data, "created_at": report.created_at}

    async def get_reports(self, skip: int = 0, limit: int = 20) -> list[dict]:
        result = await self.db.execute(select(AIReport).order_by(AIReport.created_at.desc()).offset(skip).limit(limit))
        reports = list(result.scalars().all())
        return [{"id": str(r.id), "report_type": r.report_type, "title": r.title, "created_at": r.created_at} for r in reports]

    async def get_report(self, report_id: str) -> dict | None:
        result = await self.db.execute(select(AIReport).where(AIReport.id == uuid.UUID(report_id)))
        report = result.scalar_one_or_none()
        if not report:
            return None
        return {"id": str(report.id), "report_type": report.report_type, "title": report.title, "content": report.content, "created_at": report.created_at}

    async def get_usage_summary(self, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(select(AIUsageLog).where(AIUsageLog.created_at >= cutoff))
        logs = list(result.scalars().all())
        if not logs:
            return {"total_requests": 0, "total_tokens": 0, "total_cost_usd": 0, "avg_latency_ms": 0, "by_feature": {}}
        by_feature = {}
        for log in logs:
            if log.feature not in by_feature:
                by_feature[log.feature] = {"requests": 0, "tokens": 0, "cost": 0}
            by_feature[log.feature]["requests"] += 1
            by_feature[log.feature]["tokens"] += log.total_tokens
            by_feature[log.feature]["cost"] += log.cost_usd
        return {"total_requests": len(logs), "total_tokens": sum(l.total_tokens for l in logs), "total_cost_usd": round(sum(l.cost_usd for l in logs), 4), "avg_latency_ms": round(sum(l.latency_ms for l in logs) / len(logs)), "by_feature": by_feature}
