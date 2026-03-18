"""
============================================================================
Growify — Attendance Consolidation & Idempotency Logic (Python)
============================================================================

This is the SINGLE SOURCE OF TRUTH for all attendance processing.
It is called by n8n (via Execute Command node) and can also be used
standalone from the CLI or imported into any Python backend.

INPUT  : JSON array of { employee_id, name, date, time, status }
OUTPUT : JSON array of consolidated daily records with file_hash
============================================================================
"""

import json
import hashlib
import sys
from datetime import datetime, time

# ── Configuration ──────────────────────────────────────────────────────────
LATE_THRESHOLD_HOUR = 11   # 11:00 AM
LATE_THRESHOLD_MIN  = 0
TIMEZONE_OFFSET     = "+05:30"  # IST


# ── Helpers ────────────────────────────────────────────────────────────────

def generate_file_hash(items: list) -> str:
    """
    Generate a SHA-256 hash of the sorted input data for idempotency.
    If the same file is uploaded twice, the hash will match and the
    database layer (upload_log) will reject the duplicate.
    """
    sorted_data = sorted(
        items,
        key=lambda r: f"{r.get('employee_id', '')}_{r.get('date', '')}_{r.get('time', '')}"
    )
    raw = json.dumps(sorted_data, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_time(time_str):
    """Parse a time string ('HH:MM:SS' or 'HH:MM') into a time object."""
    if not time_str or not isinstance(time_str, str):
        return None
    try:
        parts = time_str.strip().split(":")
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def normalize_date(date_str):
    """Normalize a date value to YYYY-MM-DD string."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(str(date_str)).date().isoformat()
    except (ValueError, TypeError):
        try:
            return datetime.strptime(str(date_str), "%Y-%m-%d").date().isoformat()
        except ValueError:
            return None


def to_timestamp(date_str, time_obj):
    """Format date + time into ISO 8601 timestamp with IST offset."""
    if not date_str or not time_obj:
        return None
    return f"{date_str}T{time_obj.isoformat()}{TIMEZONE_OFFSET}"


# ── Core Logic ─────────────────────────────────────────────────────────────

def consolidate_attendance(items: list) -> list:
    """
    Consolidate raw biometric punch logs into one record per employee per day.

    Rules:
      - Earliest IN  → check_in
      - Latest  OUT  → check_out
      - check_in > 11:00 AM IST → late_flag = True
      - Missing IN or OUT       → missing_punch = True

    Returns a list of consolidated dicts including a file_hash for
    idempotency checks against the upload_log table.
    """
    file_hash = generate_file_hash(items)
    grouped   = {}
    warnings  = []

    # ── Step 1: Group punches by (employee_id, date) ──
    for item in items:
        employee_id = str(
            item.get("employee_id") or item.get("Employee_ID") or item.get("EmployeeID") or ""
        ).strip()
        name = str(
            item.get("name") or item.get("Name") or item.get("employee_name") or ""
        ).strip()
        date     = normalize_date(item.get("date") or item.get("Date"))
        raw_time = item.get("time") or item.get("Time")
        status   = str(
            item.get("status") or item.get("Status")
            or item.get("punch_status") or item.get("Punch_Status") or ""
        ).strip().upper()

        if not employee_id or not date:
            warnings.append(f"Skipped row: missing employee_id or date. Raw: {json.dumps(item)}")
            continue

        if status not in ("IN", "OUT"):
            warnings.append(f"Skipped row: invalid status '{status}' for {employee_id} on {date}")
            continue

        key = f"{employee_id}__{date}"
        if key not in grouped:
            grouped[key] = {
                "employee_id": employee_id,
                "name": name,
                "date": date,
                "in_times": [],
                "out_times": [],
                "total_punches": 0,
            }

        grouped[key]["total_punches"] += 1
        parsed_t = parse_time(raw_time)
        if parsed_t:
            if status == "IN":
                grouped[key]["in_times"].append(parsed_t)
            else:
                grouped[key]["out_times"].append(parsed_t)
        else:
            warnings.append(f"Invalid time '{raw_time}' for {employee_id} on {date}.")

    # ── Step 2: Consolidate each group into a single record ──
    results = []
    for group in grouped.values():
        group["in_times"].sort()
        group["out_times"].sort()

        check_in  = group["in_times"][0]  if group["in_times"]  else None
        check_out = group["out_times"][-1] if group["out_times"] else None

        late_flag = False
        if check_in:
            threshold = time(LATE_THRESHOLD_HOUR, LATE_THRESHOLD_MIN)
            late_flag = check_in > threshold

        missing_punch = not check_in or not check_out

        results.append({
            "employee_id":     group["employee_id"],
            "name":            group["name"],
            "date":            group["date"],
            "check_in":        to_timestamp(group["date"], check_in),
            "check_out":       to_timestamp(group["date"], check_out),
            "late_flag":       late_flag,
            "missing_punch":   missing_punch,
            "raw_punch_count": group["total_punches"],
            "month_year":      group["date"][:7],
            "file_hash":       file_hash,
            "_warnings":       [w for w in warnings if group["employee_id"] in w],
        })

    return results


# ── CLI Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Usage:
      cat data.json | python logic.py          (pipe JSON via stdin)
      python logic.py data.json                (pass file path as argument)
    """
    try:
        if len(sys.argv) > 1:
            # Read from file path argument
            with open(sys.argv[1], "r", encoding="utf-8") as f:
                data = json.load(f)
        elif not sys.stdin.isatty():
            # Read from piped stdin
            data = json.load(sys.stdin)
        else:
            print(json.dumps({"error": "No input provided. Pipe JSON or pass a file path."}))
            sys.exit(1)

        output = consolidate_attendance(data)
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
