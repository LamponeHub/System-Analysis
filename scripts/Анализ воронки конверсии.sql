-- =============================================
-- Аналитический запрос: Воронка конверсии (Onboarding Funnel)
-- Автор: [Твоё имя]
-- Дата: 2026-01-16
-- Период: Q4 2025 (октябрь–декабрь)
-- Этапы: visit → signup → email_confirm → first_payment
-- =============================================

WITH event_users AS (
    -- Все уникальные пользователи с событиями за период
    SELECT DISTINCT user_id
    FROM dwh.fact_events
    WHERE event_timestamp >= '2025-10-01'
      AND event_timestamp < '2026-01-01'
),

funnel_steps AS (
    SELECT
        eu.user_id,
        -- Этап 1: посетил сайт (любой page_view)
        MAX(CASE WHEN e.event_name = 'page_view' THEN 1 ELSE 0 END) AS visited,
        -- Этап 2: зарегистрировался
        MAX(CASE WHEN e.event_name = 'user_signup' THEN 1 ELSE 0 END) AS signed_up,
        -- Этап 3: подтвердил email
        MAX(CASE WHEN e.event_name = 'email_verified' THEN 1 ELSE 0 END) AS email_confirmed,
        -- Этап 4: совершил первую оплату
        MAX(CASE WHEN p.user_id IS NOT NULL THEN 1 ELSE 0 END) AS made_payment
    FROM event_users eu
    LEFT JOIN dwh.fact_events e 
        ON eu.user_id = e.user_id
        AND e.event_timestamp >= '2025-10-01'
        AND e.event_timestamp < '2026-01-01'
    LEFT JOIN (
        SELECT DISTINCT user_id
        FROM dwh.fact_payments
        WHERE status = 'completed'
          AND payment_timestamp >= '2025-10-01'
          AND payment_timestamp < '2026-01-01'
    ) p ON eu.user_id = p.user_id
    GROUP BY eu.user_id
)

-- Агрегация воронки
SELECT
    '1. Visited site' AS funnel_step,
    COUNT(*) AS users_count,
    ROUND(100.0, 2) AS conversion_pct
FROM funnel_steps
WHERE visited = 1

UNION ALL

SELECT
    '2. Signed up',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM funnel_steps WHERE visited = 1), 0), 2)
FROM funnel_steps
WHERE signed_up = 1

UNION ALL

SELECT
    '3. Email confirmed',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM funnel_steps WHERE visited = 1), 0), 2)
FROM funnel_steps
WHERE email_confirmed = 1

UNION ALL

SELECT
    '4. Made first payment',
    COUNT(*),
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM funnel_steps WHERE visited = 1), 0), 2)
FROM funnel_steps
WHERE made_payment = 1

ORDER BY 
    CASE funnel_step
        WHEN '1. Visited site' THEN 1
        WHEN '2. Signed up' THEN 2
        WHEN '3. Email confirmed' THEN 3
        WHEN '4. Made first payment' THEN 4
    END;