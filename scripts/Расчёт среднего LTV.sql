-- =============================================
-- Аналитический запрос: Расчёт LTV (Lifetime Value) по маркетинговым каналам
-- Автор: [Твоё имя]
-- Дата: 2026-01-16
-- Бизнес-метрика: Net LTV = Total Revenue - CAC per user cohort
-- Период: пользователи, привлечённые с 2025-01-01 по 2025-12-31
-- =============================================

WITH user_cohorts AS (
    -- Определяем когорту по дате первого взаимодействия и источнику трафика
    SELECT 
        user_id,
        DATE_TRUNC('month', first_touch_at)::DATE AS acquisition_month,
        marketing_channel
    FROM dwh.dim_users
    WHERE first_touch_at >= '2025-01-01'
      AND first_touch_at < '2026-01-01'
),

revenue_by_user AS (
    -- Суммарная выручка по каждому пользователю за всё время
    SELECT
        p.user_id,
        SUM(p.amount_usd) AS total_revenue
    FROM dwh.fact_payments p
    WHERE p.status = 'completed'
    GROUP BY p.user_id
),

cac_by_channel AS (
    -- Средняя стоимость привлечения (CAC) по каналам за 2025 год
    SELECT
        marketing_channel,
        SUM(ad_spend_usd) / NULLIF(SUM(new_users), 0) AS cac_per_user
    FROM dwh.fact_marketing_spend
    WHERE report_month BETWEEN '2025-01-01' AND '2025-12-01'
    GROUP BY marketing_channel
)

-- Финальный расчёт LTV и Net LTV
SELECT
    uc.acquisition_month,
    uc.marketing_channel,
    COUNT(uc.user_id) AS cohort_size,
    AVG(rbu.total_revenue) AS avg_ltv_gross,  -- Средняя валовая LTV
    MAX(cac.cac_per_user) AS cac_per_user,    -- CAC из справочника
    AVG(rbu.total_revenue) - MAX(cac.cac_per_user) AS avg_ltv_net  -- Чистая LTV
FROM user_cohorts uc
LEFT JOIN revenue_by_user rbu 
    ON uc.user_id = rbu.user_id
LEFT JOIN cac_by_channel cac 
    ON uc.marketing_channel = cac.marketing_channel
GROUP BY 1, 2
HAVING COUNT(uc.user_id) >= 10  -- Исключаем шум от малых когорт
ORDER BY uc.acquisition_month DESC, avg_ltv_net DESC;