import json
from datetime import datetime, time, timedelta

LATE_THRESHOLD_HOUR = 11
LATE_THRESHOLD_MIN = 0
TIMEZONE_OFFSET = "+05:30"

def parse_time(time_str):
    """Parse time string ('HH:MM:SS' or 'HH:MM') into time object."""
    if not time_str or not isinstance(time_str, str):
        return None
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None

def normalize_date(date_str):
    """Normalize date string to YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        # Handles YYYY-MM-DD and common ISO formats
        return datetime.fromisoformat(str(date_str)).date().isoformat()
    except (ValueError, TypeError):
        try:
            # Fallback for common Excel formats like DD-MM-YYYY or MM/DD/YYYY
            # But fromisoformat is usually quite robust if it's already ISO.
            # Let's keep it simple for now as the JS version used new Date().
            return datetime.strptime(str(date_str), "%Y-%m-%d").date().isoformat()
        except ValueError:
            return None

def to_timestamp(date_str, time_obj):
    """Convert date string + time object to ISO 8601 string with TZ."""
    if not date_str or not time_obj:
        return None
    return f"{date_str}T{time_obj.isoformat()}{TIMEZONE_OFFSET}"

def consolidate_attendance(items):
    """
    Main logic to consolidate biometric punch logs.
    Input: list of dicts with {employee_id, name, date, time, status}
    """
    grouped = {}
    warnings = []

    # Step 1: Group punches
    for item in items:
        # Support various casing/naming conventions
        employee_id = str(item.get('employee_id') or item.get('Employee_ID') or item.get('EmployeeID') or '').strip()
        name = str(item.get('name') or item.get('Name') or item.get('employee_name') or '').strip()
        date = normalize_date(item.get('date') or item.get('Date'))
        raw_time = item.get('time') or item.get('Time')
        status = str(item.get('status') or item.get('Status') or item.get('punch_status') or item.get('Punch_Status') or '').strip().upper()

        if not employee_id or not date:
            warnings.append(f"Skipped row: missing employee_id or date. Raw: {json.dumps(item)}")
            continue

        if status not in ('IN', 'OUT'):
            warnings.append(f"Skipped row: invalid status '{status}' for {employee_id} on {date}")
            continue

        key = f"{employee_id}__{date}"
        if key not in grouped:
            grouped[key] = {
                'employee_id': employee_id,
                'name': name,
                'date': date,
                'in_times': [],
                'out_times': [],
                'total_punches': 0
            }

        grouped[key]['total_punches'] += 1
        parsed_t = parse_time(raw_time)
        if parsed_t:
            if status == 'IN':
                grouped[key]['in_times'].append(parsed_t)
            else:
                grouped[key]['out_times'].append(parsed_t)
        else:
            warnings.append(f"Invalid time '{raw_time}' for {employee_id} on {date}.")

    # Step 2: Consolidate
    results = []
    for group in grouped.values():
        group['in_times'].sort()
        group['out_times'].sort()

        check_in = group['in_times'][0] if group['in_times'] else None
        check_out = group['out_times'][-1] if group['out_times'] else None

        late_flag = False
        if check_in:
            threshold = time(LATE_THRESHOLD_HOUR, LATE_THRESHOLD_MIN)
            late_flag = check_in > threshold

        missing_punch = not check_in or not check_out

        results.append({
            'employee_id': group['employee_id'],
            'name': group['name'],
            'date': group['date'],
            'check_in': to_timestamp(group['date'], check_in),
            'check_out': to_timestamp(group['date'], check_out),
            'late_flag': late_flag,
            'missing_punch': missing_punch,
            'raw_punch_count': group['total_punches'],
            'month_year': group['date'][:7],
            '_warnings': [w for w in warnings if group['employee_id'] in w]
        })

    return results

if __name__ == "__main__":
    # Example usage (simulating n8n input)
    import sys
    try:
        # If piped data exists
        if not sys.stdin.isatty():
            data = json.load(sys.stdin)
            print(json.dumps(consolidate_attendance(data), indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
