-- =============================================
-- Аналитический запрос: Обнаружение аномальных заказов (IQR-based outlier detection)
-- Автор: [Твоё имя]
-- Дата: 2026-01-16
-- Метод: Межквартильный размах (IQR = Q3 - Q1)
-- Правило: выброс = значение < (Q1 - 1.5 * IQR) ИЛИ > (Q3 + 1.5 * IQR)
-- =============================================

WITH order_stats AS (
    SELECT
        order_id,
        user_id,
        amount_usd,
        created_at,
        customer_type,  -- 'retail', 'wholesale', 'corporate'
        sales_channel   -- 'web', 'mobile', 'pos'
    FROM dwh.fact_orders
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
      AND status IN ('completed', 'shipped')
      AND amount_usd > 0
),

quartiles AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY amount_usd) AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY amount_usd) AS q3
    FROM order_stats
),

iqr_bounds AS (
    SELECT
        q1,
        q3,
        (q3 - q1) AS iqr,
        q1 - 1.5 * (q3 - q1) AS lower_bound,
        q3 + 1.5 * (q3 - q1) AS upper_bound
    FROM quartiles
)

SELECT
    os.order_id,
    os.user_id,
    os.amount_usd,
    os.created_at,
    os.customer_type,
    os.sales_channel,
    CASE
        WHEN os.amount_usd < ib.lower_bound THEN 'low_anomaly'
        WHEN os.amount_usd > ib.upper_bound THEN 'high_anomaly'
        ELSE 'normal'
    END AS anomaly_flag,
    ib.lower_bound,
    ib.upper_bound
FROM order_stats os
CROSS JOIN iqr_bounds ib
WHERE os.amount_usd < ib.lower_bound 
   OR os.amount_usd > ib.upper_bound
ORDER BY os.amount_usd DESC;