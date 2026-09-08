-- CUSTOMER SEGMENTATION - SQL QUERIES
-- Purpose: Extract customer segments and analytics from database
-- ============================================================================

-- Query 1: Get all customers with their RFM scores and segments
SELECT 
    CustomerID,
    Recency_Days,
    Purchase_Frequency,
    Total_Spent_Rs,
    R_Score,
    F_Score,
    M_Score,
    RFM_Score,
    Segment_Name,
    CLV_Rs
FROM customer_rfm
ORDER BY CLV_Rs DESC;


-- Query 2: Segment Summary - Count and Revenue
SELECT 
    Segment_Name,
    COUNT(*) AS customer_count,
    ROUND(AVG(Total_Spent_Rs), 2) AS avg_customer_value,
    ROUND(SUM(Total_Spent_Rs), 2) AS total_segment_revenue,
    ROUND(AVG(Purchase_Frequency), 1) AS avg_purchases,
    ROUND(AVG(Recency_Days), 0) AS avg_days_since_purchase
FROM customer_rfm
GROUP BY Segment_Name
ORDER BY total_segment_revenue DESC;


-- Query 3: Champions - VIP Customers
SELECT 
    CustomerID,
    Recency_Days,
    Purchase_Frequency,
    Total_Spent_Rs,
    CLV_Rs
FROM customer_rfm
WHERE Segment_Name = 'Champions'
ORDER BY CLV_Rs DESC;


-- Query 4: Lost/Hibernating - Reactivation Targets
SELECT 
    CustomerID,
    Recency_Days,
    Purchase_Frequency,
    Total_Spent_Rs,
    DATEDIFF(CURRENT_DATE, Last_Purchase_Date) AS days_inactive
FROM customer_rfm
WHERE Segment_Name = 'Lost/Hibernating'
    AND Total_Spent_Rs > 300  -- Focus on valuable lost customers
ORDER BY Total_Spent_Rs DESC;


-- Query 5: Need Attention - At Risk Customers
SELECT 
    CustomerID,
    Recency_Days,
    Purchase_Frequency,
    Total_Spent_Rs,
    R_Score,
    F_Score
FROM customer_rfm
WHERE Segment_Name = 'Need Attention'
    AND Total_Spent_Rs > 250  -- Worth saving
ORDER BY Total_Spent_Rs DESC
LIMIT 100;


-- Query 6: High CLV Customers (Top 10%)
SELECT 
    CustomerID,
    Segment_Name,
    CLV_Rs,
    Total_Spent_Rs,
    Purchase_Frequency,
    Recency_Days
FROM customer_rfm
WHERE CLV_Rs >= (SELECT PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY CLV_Rs) FROM customer_rfm)
ORDER BY CLV_Rs DESC;


-- Query 7: Segment Migration Analysis
-- Customers who could move up to next segment
SELECT 
    CustomerID,
    Segment_Name AS current_segment,
    R_Score,
    F_Score,
    M_Score,
    CASE 
        WHEN Segment_Name = 'Need Attention' AND F_Score >= 3 THEN 'Could become Loyal'
        WHEN Segment_Name = 'Lost/Hibernating' AND M_Score >= 3 THEN 'Could become Big Spender'
        WHEN Segment_Name = 'Loyal Customers' AND R_Score >= 4 THEN 'Could become Champion'
        ELSE 'Stable'
    END AS potential_upgrade
FROM customer_rfm
WHERE Segment_Name IN ('Need Attention', 'Lost/Hibernating', 'Loyal Customers')
ORDER BY Total_Spent_Rs DESC;


-- Query 8: Monthly Cohort Analysis
SELECT 
    DATE_TRUNC('month', First_Purchase_Date) AS cohort_month,
    COUNT(*) AS customers_acquired,
    ROUND(AVG(Total_Spent_Rs), 2) AS avg_lifetime_value,
    ROUND(AVG(Purchase_Frequency), 1) AS avg_purchases
FROM customer_rfm
GROUP BY cohort_month
ORDER BY cohort_month DESC;


-- Query 9: Category Preference by Segment
SELECT 
    c.Segment_Name,
    t.Category,
    COUNT(*) AS purchase_count,
    ROUND(SUM(t.Amount), 2) AS total_spent
FROM customer_rfm c
JOIN transactions t ON c.CustomerID = t.CustomerID
GROUP BY c.Segment_Name, t.Category
ORDER BY c.Segment_Name, total_spent DESC;


-- Query 10: Marketing Campaign Targets
-- Extract customer lists for each campaign
SELECT 
    Segment_Name AS campaign_segment,
    CustomerID,
    CASE 
        WHEN Segment_Name = 'Champions' THEN 'VIP_Program'
        WHEN Segment_Name = 'Loyal Customers' THEN 'Cross_Sell_Campaign'
        WHEN Segment_Name = 'Big Spenders' THEN 'Frequency_Incentive'
        WHEN Segment_Name = 'Need Attention' THEN 'Win_Back_Offer'
        WHEN Segment_Name = 'Lost/Hibernating' THEN 'Reactivation_30pct_Off'
    END AS campaign_name,
    Total_Spent_Rs AS customer_value,
    CLV_Rs AS lifetime_value_projection
FROM customer_rfm
ORDER BY Segment_Name, CLV_Rs DESC;


-- Query 11: Performance Metrics Dashboard
SELECT 
    COUNT(DISTINCT CustomerID) AS total_customers,
    ROUND(AVG(Total_Spent_Rs), 2) AS avg_customer_value,
    ROUND(SUM(Total_Spent_Rs), 2) AS total_revenue,
    ROUND(AVG(Purchase_Frequency), 1) AS avg_purchase_frequency,
    ROUND(AVG(CLV_Rs), 2) AS avg_clv,
    COUNT(CASE WHEN Segment_Name = 'Champions' THEN 1 END) AS champions_count,
    COUNT(CASE WHEN Segment_Name = 'Lost/Hibernating' THEN 1 END) AS at_risk_count
FROM customer_rfm;


-- Query 12: RFM Score Distribution
SELECT 
    RFM_Score,
    COUNT(*) AS customer_count,
    ROUND(AVG(Total_Spent_Rs), 2) AS avg_value,
    ROUND(SUM(Total_Spent_Rs), 2) AS total_value
FROM customer_rfm
GROUP BY RFM_Score
ORDER BY RFM_Score DESC;