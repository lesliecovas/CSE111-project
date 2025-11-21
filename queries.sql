
-- ============================
-- 20+ DIVERSE SQL STATEMENTS
-- (SELECTs, JOINs, AGGREGATES, SUBQUERY, VIEW, INSERT, UPDATE, DELETE)
-- ============================

/* 1. Simple SELECT: show crops */
SELECT crop_id, crop_name, crop_group FROM crops;

/* 2. List districts */
SELECT district_id, state_name, district_name FROM districts ORDER BY state_name, district_name;

/* 3. Join: production with district & crop (latest year sample) */
SELECT p.year, d.state_name, d.district_name, c.crop_name, p.season, p.area, p.production, p.yield
FROM crop_production_statistic p
JOIN districts d ON p.district_id = d.district_id
JOIN crops c ON p.crop_id = c.crop_id
WHERE p.year = 2023
ORDER BY p.production DESC;

/* 4. Aggregate: total production per state in 2023 */
SELECT d.state_name, SUM(p.production) AS total_production_2023
FROM crop_production_statistic p
JOIN districts d ON p.district_id = d.district_id
WHERE p.year = 2023
GROUP BY d.state_name
ORDER BY total_production_2023 DESC;

/* 5. Average yield by crop */
SELECT c.crop_name, ROUND(AVG(p.yield),2) AS avg_yield
FROM crop_production_statistic p
JOIN crops c ON p.crop_id = c.crop_id
GROUP BY c.crop_name
ORDER BY avg_yield DESC;

/* 6. Many-to-many example: pesticides used for Rice */
SELECT c.crop_name, pu.compound, cp.avg_estimate, cp.effectiveness_score
FROM crop_pesticide cp
JOIN crops c ON cp.crop_id = c.crop_id
JOIN pesticide_use pu ON cp.pesticide_id = pu.pesticide_id
WHERE c.crop_name = 'Rice';

/* 7. Correlation-like: join rainfall (sustainability) with yield */
SELECT d.district_name, s.year, s.rainfall_mm, ROUND(AVG(s.crop_yield),2) AS avg_yield
FROM sustainability_data s
JOIN districts d ON s.district_id = d.district_id
GROUP BY d.district_name, s.year
ORDER BY s.year DESC;

/* 8. Subquery: states with production > 3000 in 2022 */
SELECT DISTINCT d.state_name
FROM crop_production_statistic p
JOIN districts d ON p.district_id = d.district_id
WHERE p.year = 2022
  AND p.production > 3000;

/* 9. Window function (SQLite supports window funcs): top crop per district by production (2023) */
SELECT district_name, crop_name, production, rank() OVER (PARTITION BY district_id ORDER BY production DESC) as rk
FROM (
  SELECT p.district_id, d.district_name, c.crop_name, p.production
  FROM crop_production_statistic p
  JOIN districts d ON p.district_id = d.district_id
  JOIN crops c ON p.crop_id = c.crop_id
  WHERE p.year = 2023
)
WHERE rk = 1;

/* 10. Price analysis: average modal price by crop */
SELECT c.crop_name, ROUND(AVG(cap.modal_price_rs_per_quintal),2) as avg_modal_price
FROM crop_arrival_price cap
JOIN crops c ON cap.crop_id = c.crop_id
GROUP BY c.crop_name
ORDER BY avg_modal_price DESC;

/* 11. Market supply: total arrival tonnes per market */
SELECT m.market_name, SUM(cap.arrival_tonnes) AS total_tonnes
FROM crop_arrival_price cap
JOIN markets m ON cap.market_id = m.market_id
GROUP BY m.market_name
ORDER BY total_tonnes DESC;

/* 12. Create a VIEW: yearly_state_production */
CREATE VIEW IF NOT EXISTS yearly_state_production AS
SELECT p.year, d.state_name, SUM(p.production) AS state_production
FROM crop_production_statistic p
JOIN districts d ON p.district_id = d.district_id
GROUP BY p.year, d.state_name;

/* 13. Query the VIEW */
SELECT * FROM yearly_state_production WHERE year = 2023 ORDER BY state_production DESC;

/* 14. Insert: add a new district */
INSERT INTO districts (state_name, district_name) VALUES ('Karnataka', 'Bengaluru Urban');

/* 15. Insert: add a new crop and requirement */
INSERT INTO crops (crop_name, crop_group) VALUES ('Cotton', 'Cash Crops');
INSERT INTO crop_requirements (crop_id, N, P, K, temperature, humidity, ph, rainfall) VALUES (
  (SELECT crop_id FROM crops WHERE crop_name='Cotton'), 60, 30, 20, 28, 65, 6.8, 600
);

/* 16. Update: fix a production value (example) */
UPDATE crop_production_statistic
SET production = 3900, yield = ROUND(3900.0/1250.0,3), year = 2023
WHERE stat_id = 6; -- previously inserted row for stat_id 6

/* 17. Update: mark a pesticide avg_estimate (adjust) */
UPDATE pesticide_use SET avg_estimate = avg_estimate * 1.05 WHERE year = 2022 AND compound = 'CompoundA';

/* 18. Delete: remove a demo arrival price record by ID */
DELETE FROM crop_arrival_price WHERE arrival_id = 3;

/* 19. Complex SELECT: join production, weather, and sustainability to get context */
SELECT p.year, d.state_name, d.district_name, c.crop_name, p.production, w.precipitation, s.sustainability_score
FROM crop_production_statistic p
LEFT JOIN farm_weather w ON p.district_id = w.district_id AND w.date LIKE '2023-07-%'
LEFT JOIN sustainability_data s ON p.crop_id = s.crop_id AND p.district_id = s.district_id AND s.year = p.year
JOIN districts d ON p.district_id = d.district_id
JOIN crops c ON p.crop_id = c.crop_id
WHERE p.year = 2023
ORDER BY p.production DESC
LIMIT 10;

/* 20. Aggregate with HAVING: districts with avg yield > 3.0 */
SELECT d.district_name, AVG(p.yield) AS avg_yield
FROM crop_production_statistic p
JOIN districts d ON p.district_id = d.district_id
GROUP BY d.district_name
HAVING AVG(p.yield) > 3.0;

/* 21. Insert multiple production rows (batch demo) */
INSERT INTO crop_production_statistic (crop_id, district_id, season, area, production, yield, year) VALUES
(1, 5, 'Kharif', 300.0, 900.0, 3.0, 2023),
(3, 4, 'Kharif', 600.0, 1800.0, 3.0, 2023);

/* 22. Subquery with IN: crops grown in Ludhiana (district_id = 1) */
SELECT DISTINCT c.crop_name
FROM crop_production_statistic p
JOIN crops c ON p.crop_id = c.crop_id
WHERE p.district_id = 1;

/* 23. Show crop requirements vs average yield (join) */
SELECT c.crop_name, cr.N, cr.P, cr.K, ROUND(AVG(p.yield),2) AS avg_yield
FROM crop_requirements cr
JOIN crops c ON cr.crop_id = c.crop_id
LEFT JOIN crop_production_statistic p ON p.crop_id = c.crop_id
GROUP BY c.crop_name, cr.N, cr.P, cr.K;

/* 24. Delete example: remove a sustainability record (demo) */
DELETE FROM sustainability_data WHERE record_id = 3;

/* 25. Final SELECT: quick dashboard numbers */
SELECT
  (SELECT COUNT(*) FROM districts) AS num_districts,
  (SELECT COUNT(*) FROM crops) AS num_crops,
  (SELECT COUNT(*) FROM crop_production_statistic WHERE year = 2023) AS production_records_2023,
  (SELECT ROUND(AVG(percent),2) FROM (
     SELECT 100.0 * SUM(production) / NULLIF((SELECT SUM(production) FROM crop_production_statistic WHERE year = 2023),0) as percent
     FROM crop_production_statistic WHERE year = 2023
  )) AS dummy_percent;


