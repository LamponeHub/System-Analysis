-- =============================================
-- Аналитический запрос: Коэффициент удержания (Retention Rate) по сегментам
-- Автор: [Твоё имя]
-- Дата: 2026-01-16
-- Бизнес-метрика: 6-month rolling retention by user cohort & loyalty program status
-- =============================================

WITH user_cohorts AS (
    -- Определяем когорту по месяцу первого входа
    SELECT 
        user_id,
        DATE_TRUNC('month', MIN(first_seen_at))::DATE AS cohort_month,
        loyalty_program_enrolled
    FROM dwh.dim_users
    WHERE first_seen_at >= '2025-07-01'  -- Анализируем только последние 6 месяцев
    GROUP BY user_id, loyalty_program_enrolled
),

active_months AS (
    -- Месяцы активности пользователя (по событиям входа)
    SELECT DISTINCT
        e.user_id,
        DATE_TRUNC('month', e.event_timestamp)::DATE AS active_month
    FROM dwh.fact_events e
    WHERE e.event_name = 'user_login'
      AND e.event_timestamp >= '2025-07-01'
),

retention_matrix AS (
    -- Считаем, кто остался активен через N месяцев после когорты
    SELECT
        c.cohort_month,
        c.loyalty_program_enrolled,
        EXTRACT(MONTH FROM AGE(am.active_month, c.cohort_month)) AS months_since_cohort,
        COUNT(DISTINCT c.user_id) AS retained_users
    FROM user_cohorts c
    INNER JOIN active_months am 
        ON c.user_id = am.user_id 
        AND am.active_month >= c.cohort_month
    GROUP BY 1, 2, 3
),

cohort_sizes AS (
    -- Общий размер каждой когорты
    SELECT
        cohort_month,
        loyalty_program_enrolled,
        COUNT(DISTINCT user_id) AS cohort_size
    FROM user_cohorts
    GROUP BY 1, 2
)

-- Финальный отчёт: retention rate (%) по месяцам и программе лояльности
SELECT
    r.cohort_month,
    r.loyalty_program_enrolled,
    r.months_since_cohort,
    cs.cohort_size,
    r.retained_users,
    ROUND(100.0 * r.retained_users / NULLIF(cs.cohort_size, 0), 2) AS retention_rate_pct
FROM retention_matrix r
JOIN cohort_sizes cs
    ON r.cohort_month = cs.cohort_month
    AND r.loyalty_program_enrolled = cs.loyalty_program_enrolled
WHERE r.months_since_cohort BETWEEN 0 AND 5  -- До 6 месяцев включительно
ORDER BY r.cohort_month, r.loyalty_program_enrolled DESC, r.months_since_cohort;