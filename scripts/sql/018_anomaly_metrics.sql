-- 018: Anomaly metrics table + daily computation functions
-- Run in Supabase SQL Editor

-- ============================================================
-- STEP 1: Create anomaly_metrics table
-- ============================================================
CREATE TABLE IF NOT EXISTS staging.anomaly_metrics (
    metric_id           SERIAL PRIMARY KEY,
    metric_date         DATE NOT NULL,
    metric_name         VARCHAR(50) NOT NULL,
    metric_value        NUMERIC(12,4) NOT NULL,
    baseline_mean       NUMERIC(12,4),
    baseline_stddev     NUMERIC(12,4),
    is_anomaly          BOOLEAN DEFAULT false,
    created_at          TIMESTAMPTZ DEFAULT now(),
    UNIQUE(metric_date, metric_name)
);

COMMENT ON TABLE staging.anomaly_metrics
    IS 'Daily anomaly metrics with baseline stats. Alert when value > 2σ from mean.';

CREATE INDEX IF NOT EXISTS idx_anomaly_metrics_date
    ON staging.anomaly_metrics (metric_date DESC);

CREATE INDEX IF NOT EXISTS idx_anomaly_metrics_name
    ON staging.anomaly_metrics (metric_name, metric_date DESC);

-- ============================================================
-- STEP 2: Function to compute daily metrics
-- ============================================================
CREATE OR REPLACE FUNCTION staging.compute_daily_anomaly_metrics(target_date DATE DEFAULT CURRENT_DATE)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_volume        NUMERIC;
    v_max_stale_h   NUMERIC;
    v_avg_conf      NUMERIC;
    v_zip_coverage  NUMERIC;
    v_mean          NUMERIC;
    v_stddev        NUMERIC;
BEGIN
    -- Metric 1: Daily candidate volume
    SELECT COUNT(*)::numeric INTO v_volume
    FROM staging.decision_candidates
    WHERE DATE(created_at) = target_date;

    -- Metric 2: Max source staleness (hours)
    SELECT COALESCE(MAX(EXTRACT(EPOCH FROM (now() - latest)) / 3600), 0)::numeric
    INTO v_max_stale_h
    FROM (
        SELECT source_system, MAX(created_at) AS latest
        FROM staging.members
        GROUP BY source_system
    ) sub;

    -- Metric 3: Avg confidence score (that day's candidates)
    SELECT COALESCE(AVG(composite_score), 0)::numeric INTO v_avg_conf
    FROM staging.decision_candidates
    WHERE DATE(created_at) = target_date;

    -- Metric 4: ZIP coverage (% of members with zip5)
    SELECT COALESCE(
        SUM(CASE WHEN zip5 IS NOT NULL THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0),
        0
    ) INTO v_zip_coverage
    FROM staging.members;

    -- Insert/update each metric with baseline stats from last 30 days
    -- Volume
    SELECT AVG(metric_value), STDDEV(metric_value) INTO v_mean, v_stddev
    FROM staging.anomaly_metrics
    WHERE metric_name = 'daily_volume' AND metric_date >= target_date - 30 AND metric_date < target_date;

    INSERT INTO staging.anomaly_metrics (metric_date, metric_name, metric_value, baseline_mean, baseline_stddev, is_anomaly)
    VALUES (target_date, 'daily_volume', v_volume, v_mean, v_stddev,
            CASE WHEN v_stddev > 0 AND ABS(v_volume - COALESCE(v_mean, v_volume)) > 2 * v_stddev THEN true ELSE false END)
    ON CONFLICT (metric_date, metric_name) DO UPDATE SET
        metric_value = EXCLUDED.metric_value,
        baseline_mean = EXCLUDED.baseline_mean,
        baseline_stddev = EXCLUDED.baseline_stddev,
        is_anomaly = EXCLUDED.is_anomaly;

    -- Max staleness
    SELECT AVG(metric_value), STDDEV(metric_value) INTO v_mean, v_stddev
    FROM staging.anomaly_metrics
    WHERE metric_name = 'max_staleness_hours' AND metric_date >= target_date - 30 AND metric_date < target_date;

    INSERT INTO staging.anomaly_metrics (metric_date, metric_name, metric_value, baseline_mean, baseline_stddev, is_anomaly)
    VALUES (target_date, 'max_staleness_hours', v_max_stale_h, v_mean, v_stddev,
            CASE WHEN v_stddev > 0 AND ABS(v_max_stale_h - COALESCE(v_mean, v_max_stale_h)) > 2 * v_stddev THEN true ELSE false END)
    ON CONFLICT (metric_date, metric_name) DO UPDATE SET
        metric_value = EXCLUDED.metric_value,
        baseline_mean = EXCLUDED.baseline_mean,
        baseline_stddev = EXCLUDED.baseline_stddev,
        is_anomaly = EXCLUDED.is_anomaly;

    -- Avg confidence
    SELECT AVG(metric_value), STDDEV(metric_value) INTO v_mean, v_stddev
    FROM staging.anomaly_metrics
    WHERE metric_name = 'avg_confidence' AND metric_date >= target_date - 30 AND metric_date < target_date;

    INSERT INTO staging.anomaly_metrics (metric_date, metric_name, metric_value, baseline_mean, baseline_stddev, is_anomaly)
    VALUES (target_date, 'avg_confidence', v_avg_conf, v_mean, v_stddev,
            CASE WHEN v_stddev > 0 AND ABS(v_avg_conf - COALESCE(v_mean, v_avg_conf)) > 2 * v_stddev THEN true ELSE false END)
    ON CONFLICT (metric_date, metric_name) DO UPDATE SET
        metric_value = EXCLUDED.metric_value,
        baseline_mean = EXCLUDED.baseline_mean,
        baseline_stddev = EXCLUDED.baseline_stddev,
        is_anomaly = EXCLUDED.is_anomaly;

    -- ZIP coverage
    SELECT AVG(metric_value), STDDEV(metric_value) INTO v_mean, v_stddev
    FROM staging.anomaly_metrics
    WHERE metric_name = 'zip_coverage' AND metric_date >= target_date - 30 AND metric_date < target_date;

    INSERT INTO staging.anomaly_metrics (metric_date, metric_name, metric_value, baseline_mean, baseline_stddev, is_anomaly)
    VALUES (target_date, 'zip_coverage', v_zip_coverage, v_mean, v_stddev,
            CASE WHEN v_stddev > 0 AND ABS(v_zip_coverage - COALESCE(v_mean, v_zip_coverage)) > 2 * v_stddev THEN true ELSE false END)
    ON CONFLICT (metric_date, metric_name) DO UPDATE SET
        metric_value = EXCLUDED.metric_value,
        baseline_mean = EXCLUDED.baseline_mean,
        baseline_stddev = EXCLUDED.baseline_stddev,
        is_anomaly = EXCLUDED.is_anomaly;
END;
$$;

COMMENT ON FUNCTION staging.compute_daily_anomaly_metrics
    IS 'Computes 4 anomaly metrics for a given date, stores with 30-day baseline stats';

-- ============================================================
-- STEP 3: Seed baseline (run for today)
-- ============================================================
SELECT staging.compute_daily_anomaly_metrics(CURRENT_DATE);

-- Verify
SELECT * FROM staging.anomaly_metrics ORDER BY metric_date DESC, metric_name;
