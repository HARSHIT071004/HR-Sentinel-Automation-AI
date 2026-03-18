-- =============================================================================
-- AI-Powered Attendance & Warning System — Production Schema
-- Database: PostgreSQL 15+
-- =============================================================================

-- Enable UUID extension for upload_log
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. DAILY RECORDS
--    One row per employee per day. Stores consolidated check-in/out from 
--    biometric punch data. Idempotent via UNIQUE(employee_id, date).
-- =============================================================================
CREATE TABLE IF NOT EXISTS daily_records (
    id              BIGSERIAL       PRIMARY KEY,
    employee_id     VARCHAR(50)     NOT NULL,
    name            VARCHAR(150)    NOT NULL,
    date            DATE            NOT NULL,
    check_in        TIMESTAMPTZ,                     -- Earliest IN punch
    check_out       TIMESTAMPTZ,                     -- Latest OUT punch
    late_flag       BOOLEAN         DEFAULT FALSE,   -- TRUE if check_in > 11:00 AM IST
    missing_punch   BOOLEAN         DEFAULT FALSE,   -- TRUE if IN or OUT is missing
    raw_punch_count INTEGER         DEFAULT 0,       -- Total punches received (for audit)
    upload_id       UUID,                            -- FK to upload_log
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),

    CONSTRAINT uq_employee_date UNIQUE (employee_id, date)
);

-- Hot paths: lookup by employee, by date, by late flag
CREATE INDEX IF NOT EXISTS idx_dr_employee_id   ON daily_records (employee_id);
CREATE INDEX IF NOT EXISTS idx_dr_date          ON daily_records (date);
CREATE INDEX IF NOT EXISTS idx_dr_late          ON daily_records (date, late_flag) WHERE late_flag = TRUE;

-- =============================================================================
-- 2. MONTHLY SUMMARY
--    Running strike count per employee per month. The month_year column
--    (format: YYYY-MM) naturally resets counts each month — a new month
--    creates a new row with late_count = 0.
-- =============================================================================
CREATE TABLE IF NOT EXISTS monthly_summary (
    id                  BIGSERIAL       PRIMARY KEY,
    employee_id         VARCHAR(50)     NOT NULL,
    name                VARCHAR(150)    NOT NULL,
    month_year          VARCHAR(7)      NOT NULL,    -- e.g. '2026-03'
    late_count          INTEGER         DEFAULT 0,
    warning_level       INTEGER         DEFAULT 0,   -- 0=none, 1=friendly, 2=strict, 3=final
    last_warning_date   DATE,
    last_late_date      DATE,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),

    CONSTRAINT uq_employee_month UNIQUE (employee_id, month_year)
);

CREATE INDEX IF NOT EXISTS idx_ms_month_year    ON monthly_summary (month_year);
CREATE INDEX IF NOT EXISTS idx_ms_late_count    ON monthly_summary (month_year, late_count);

-- =============================================================================
-- 3. UPLOAD LOG
--    Tracks every file upload for idempotency. A SHA-256 hash of the file
--    content is stored. If a duplicate hash is detected, the upload is
--    rejected before any processing occurs.
-- =============================================================================
CREATE TABLE IF NOT EXISTS upload_log (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_name       VARCHAR(255)    NOT NULL,
    file_hash       VARCHAR(64)     NOT NULL UNIQUE,  -- SHA-256 hex digest
    row_count       INTEGER         DEFAULT 0,
    records_created INTEGER         DEFAULT 0,
    records_updated INTEGER         DEFAULT 0,
    status          VARCHAR(20)     DEFAULT 'processing',  -- processing | completed | failed
    error_message   TEXT,
    uploaded_at     TIMESTAMPTZ     DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ul_file_hash ON upload_log (file_hash);

-- =============================================================================
-- 4. WARNING LOG
--    Audit trail of every warning email sent. Required for HR compliance.
--    Stores the full email body, strike level, and delivery status.
-- =============================================================================
CREATE TABLE IF NOT EXISTS warning_log (
    id              BIGSERIAL       PRIMARY KEY,
    employee_id     VARCHAR(50)     NOT NULL,
    name            VARCHAR(150)    NOT NULL,
    month_year      VARCHAR(7)      NOT NULL,
    strike_level    INTEGER         NOT NULL,         -- 1, 2, or 3
    email_subject   TEXT            NOT NULL,
    email_body      TEXT            NOT NULL,
    email_to        VARCHAR(255),
    meeting_link    TEXT,                              -- Only for strike 3
    delivery_status VARCHAR(20)     DEFAULT 'sent',   -- sent | failed | pending
    sent_at         TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wl_employee  ON warning_log (employee_id, month_year);
CREATE INDEX IF NOT EXISTS idx_wl_strike    ON warning_log (strike_level);

-- =============================================================================
-- TRIGGER: auto-update updated_at on row modification
-- =============================================================================
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_daily_records_updated
    BEFORE UPDATE ON daily_records
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER trg_monthly_summary_updated
    BEFORE UPDATE ON monthly_summary
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- =============================================================================
-- VIEW: Dashboard query — today's late employees with risk level
-- =============================================================================
CREATE OR REPLACE VIEW v_dashboard_today AS
SELECT
    dr.employee_id,
    dr.name,
    dr.check_in,
    dr.check_out,
    dr.late_flag,
    dr.missing_punch,
    COALESCE(ms.late_count, 0)    AS monthly_late_count,
    COALESCE(ms.warning_level, 0) AS warning_level,
    CASE
        WHEN COALESCE(ms.late_count, 0) >= 3 THEN 'CRITICAL'
        WHEN COALESCE(ms.late_count, 0) = 2  THEN 'AT_RISK'
        WHEN COALESCE(ms.late_count, 0) = 1  THEN 'WARNING'
        ELSE 'SAFE'
    END AS risk_status
FROM daily_records dr
LEFT JOIN monthly_summary ms
    ON dr.employee_id = ms.employee_id
    AND ms.month_year = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
WHERE dr.date = CURRENT_DATE
ORDER BY ms.late_count DESC NULLS LAST, dr.name;
