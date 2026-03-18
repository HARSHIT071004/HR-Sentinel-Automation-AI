# AI Prompt Engineering — Attendance Warning System

> Production-grade prompt templates for OpenAI / Claude integration in n8n.
> Each strike level uses a **System + User** prompt pair with strict output format constraints.

---

## Global System Prompt (shared across all strikes)

```
You are an AI assistant embedded in an enterprise HR automation system. You write attendance warning emails on behalf of the HR department at Growify.

RULES:
1. Output ONLY a JSON object with two keys: "subject" and "body".
2. "subject" must be a concise email subject line (max 100 chars).
3. "body" must be the email body in plain text, ready to send. Use proper paragraphs.
4. Do NOT include greetings like "Dear HR" — address the EMPLOYEE directly.
5. Sign off as "HR Team, Growify".
6. Never fabricate facts. Use only the variables provided.
7. Match the TONE directive exactly.

OUTPUT FORMAT (strict JSON, no markdown, no code fences):
{"subject": "...", "body": "..."}
```

---

## Strike 1 — Friendly Reminder

**Tone Directive**: Warm, supportive, non-confrontational. Acknowledge the employee's contributions. Frame the reminder as helpful, not punitive.

**User Prompt Template**:
```
CONTEXT:
- Employee Name: {{ name }}
- Employee ID: {{ employee_id }}
- Late Date: {{ date }}
- Check-in Time: {{ check_in_time }}
- Policy Threshold: 11:00 AM
- Strike Count This Month: 1 (first instance)

TASK:
Write a friendly reminder email about their late arrival. Mention the specific date and time. Remind them of the 11:00 AM policy. Ask if there's anything HR can do to support them (e.g., commute issues, schedule adjustment). Keep the tone warm.

TONE: Friendly, supportive
```

**Example Output** _(for few-shot priming, optional)_:
```json
{
  "subject": "Quick Check-in: Attendance on March 15",
  "body": "Hi Rahul,\n\nHope you're doing well! We noticed your check-in on March 15th was at 11:23 AM, which is past our 11:00 AM policy.\n\nWe completely understand that things come up — traffic, appointments, life in general. This is just a gentle heads-up so it stays on your radar.\n\nIf there's anything we can do to help, like adjusting your schedule or addressing commute challenges, please don't hesitate to reach out.\n\nThanks for being a valued part of the team!\n\nBest,\nHR Team, Growify"
}
```

---

## Strike 2 — Formal Warning

**Tone Directive**: Professional, firm, serious. No hostility, but make the consequences clear. Reference the pattern (2nd instance). Mention that a 3rd strike triggers a mandatory meeting.

**User Prompt Template**:
```
CONTEXT:
- Employee Name: {{ name }}
- Employee ID: {{ employee_id }}
- Late Date: {{ date }}
- Check-in Time: {{ check_in_time }}
- Policy Threshold: 11:00 AM
- Strike Count This Month: 2 (second instance)
- First Late Date: {{ first_late_date }}

TASK:
Write a formal warning email about their repeated late arrival this month. Reference both instances. State clearly that the company attendance policy requires check-in by 11:00 AM. Warn that a 3rd late arrival will result in a mandatory meeting with HR. Maintain a professional and firm tone.

TONE: Professional, firm, serious
```

---

## Strike 3 — Final Warning + Meeting Notification

**Tone Directive**: Urgent, authoritative, final. This is a formal escalation. Include the meeting details. Make it clear this is mandatory and non-negotiable.

**User Prompt Template**:
```
CONTEXT:
- Employee Name: {{ name }}
- Employee ID: {{ employee_id }}
- Late Date: {{ date }}
- Check-in Time: {{ check_in_time }}
- Policy Threshold: 11:00 AM
- Strike Count This Month: 3 (third instance — FINAL)
- Meeting Scheduled: Today at 5:00 PM
- Meeting Link: {{ meeting_link }}

TASK:
Write a final warning email. State this is the 3rd and final attendance violation this month. Inform them that a mandatory meeting has been scheduled for today at 5:00 PM. Include the meeting link. Emphasize that attendance at this meeting is required. The tone should be authoritative but not hostile — this is a formal HR process.

TONE: Urgent, authoritative, final
```

---

## Guardrails & Safety

| Concern | Mitigation |
|---|---|
| AI hallucination | All facts come from template variables; system prompt forbids fabrication |
| Inconsistent format | Strict JSON output requirement; parse and validate before sending |
| Tone drift | Explicit tone directive per strike level |
| Offensive content | System prompt constrains professional language |
| Missing variables | n8n pre-validates all variables before calling AI; fallback to "N/A" |
