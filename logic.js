/**
 * ============================================================================
 * n8n Function Node: Consolidate Biometric Attendance Logs
 * ============================================================================
 *
 * INPUT (from Excel Read node):
 *   Array of { employee_id, name, date, time, status }
 *   where status is "IN" or "OUT", time is "HH:MM:SS" or "HH:MM"
 *
 * OUTPUT:
 *   Array of consolidated records, one per employee per day, with:
 *   - check_in (earliest IN)
 *   - check_out (latest OUT)
 *   - late_flag (check_in > 11:00 AM IST)
 *   - missing_punch flag
 *   - raw_punch_count
 *
 * EDGE CASES HANDLED:
 *   - Multiple IN/OUT punches → deduplicated (first IN, last OUT)
 *   - Missing IN or OUT → flagged, null for missing field
 *   - Invalid/empty time strings → skipped with warning
 *   - Timezone: all comparisons in Asia/Kolkata (IST, UTC+5:30)
 * ============================================================================
 */

const LATE_THRESHOLD_HOUR = 11; // 11:00 AM
const LATE_THRESHOLD_MIN  = 0;
const TIMEZONE_OFFSET     = '+05:30'; // IST

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Parse a time string ("HH:MM:SS" or "HH:MM") into { hours, minutes, seconds }.
 * Returns null if the string is unparseable.
 */
function parseTime(timeStr) {
    if (!timeStr || typeof timeStr !== 'string') return null;
    const cleaned = timeStr.trim();
    const parts = cleaned.split(':');
    if (parts.length < 2 || parts.length > 3) return null;

    const hours   = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    const seconds = parts[2] ? parseInt(parts[2], 10) : 0;

    if (isNaN(hours) || isNaN(minutes) || isNaN(seconds)) return null;
    if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59 || seconds < 0 || seconds > 59) return null;

    return { hours, minutes, seconds };
}

/**
 * Convert a parsed time to total seconds since midnight for easy comparison.
 */
function toSeconds(parsed) {
    return parsed.hours * 3600 + parsed.minutes * 60 + parsed.seconds;
}

/**
 * Format a date string + time string into an ISO 8601 timestamp with timezone.
 * e.g. "2026-03-17" + "10:15:00" → "2026-03-17T10:15:00+05:30"
 */
function toTimestamp(dateStr, timeStr) {
    if (!dateStr || !timeStr) return null;
    return `${dateStr}T${timeStr}${TIMEZONE_OFFSET}`;
}

/**
 * Normalize a date string to YYYY-MM-DD.
 * Handles common Excel date formats.
 */
function normalizeDate(dateStr) {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return null;
    return d.toISOString().split('T')[0];
}

/**
 * Normalize a time string to HH:MM:SS.
 */
function normalizeTime(timeStr) {
    const parsed = parseTime(timeStr);
    if (!parsed) return null;
    return [
        String(parsed.hours).padStart(2, '0'),
        String(parsed.minutes).padStart(2, '0'),
        String(parsed.seconds).padStart(2, '0'),
    ].join(':');
}

// ---------------------------------------------------------------------------
// Main Processing
// ---------------------------------------------------------------------------

const items = $input.all();
const grouped = {};
const warnings = [];

// Step 1: Group all punches by employee_id + date
for (const item of items) {
    const raw = item.json;

    // Normalize inputs
    const employeeId = (raw.employee_id || raw.Employee_ID || raw.EmployeeID || '').toString().trim();
    const name       = (raw.name || raw.Name || raw.employee_name || '').toString().trim();
    const date       = normalizeDate(raw.date || raw.Date);
    const time       = normalizeTime(raw.time || raw.Time);
    const status     = (raw.status || raw.Status || raw.punch_status || raw.Punch_Status || '').toString().trim().toUpperCase();

    // Validate required fields
    if (!employeeId || !date) {
        warnings.push(`Skipped row: missing employee_id or date. Raw: ${JSON.stringify(raw)}`);
        continue;
    }

    if (status !== 'IN' && status !== 'OUT') {
        warnings.push(`Skipped row: invalid status "${status}" for ${employeeId} on ${date}`);
        continue;
    }

    const key = `${employeeId}__${date}`;

    if (!grouped[key]) {
        grouped[key] = {
            employee_id: employeeId,
            name: name,
            date: date,
            inTimes: [],   // raw time strings for IN punches
            outTimes: [],  // raw time strings for OUT punches
            totalPunches: 0,
        };
    }

    grouped[key].totalPunches++;

    if (time) {
        if (status === 'IN') {
            grouped[key].inTimes.push(time);
        } else {
            grouped[key].outTimes.push(time);
        }
    } else {
        warnings.push(`Invalid time "${raw.time}" for ${employeeId} on ${date}. Punch counted but time ignored.`);
    }
}

// Step 2: Consolidate each group into a single record
const results = Object.values(grouped).map(group => {
    // Sort IN times ascending → first one is check-in
    group.inTimes.sort();
    // Sort OUT times ascending → last one is check-out
    group.outTimes.sort();

    const checkInTime  = group.inTimes.length > 0 ? group.inTimes[0] : null;
    const checkOutTime = group.outTimes.length > 0 ? group.outTimes[group.outTimes.length - 1] : null;

    // Late detection: check_in > 11:00 AM
    let lateFlag = false;
    if (checkInTime) {
        const parsed = parseTime(checkInTime);
        if (parsed) {
            const checkInSeconds    = toSeconds(parsed);
            const thresholdSeconds  = LATE_THRESHOLD_HOUR * 3600 + LATE_THRESHOLD_MIN * 60;
            lateFlag = checkInSeconds > thresholdSeconds;
        }
    }

    // Missing punch detection
    const missingPunch = !checkInTime || !checkOutTime;

    return {
        json: {
            employee_id:     group.employee_id,
            name:            group.name,
            date:            group.date,
            check_in:        toTimestamp(group.date, checkInTime),
            check_out:       toTimestamp(group.date, checkOutTime),
            late_flag:        lateFlag,
            missing_punch:   missingPunch,
            raw_punch_count: group.totalPunches,
            month_year:      group.date.substring(0, 7),  // "YYYY-MM"
            _warnings:       warnings.filter(w => w.includes(group.employee_id)),
        }
    };
});

// If no valid records, return a single item with error info
if (results.length === 0) {
    return [{
        json: {
            error: true,
            message: 'No valid records found in uploaded file.',
            warnings: warnings,
        }
    }];
}

return results;
