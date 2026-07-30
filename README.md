# 🛴 Gans Scooters: Data Engineering & Analytics Course Project
Welcome to the repository for my Data Analytics course project focused on Gans, an innovative sustainable mobility startup providing electric scooter (e-scooter) sharing services across major global cities.

## 🎯 Project Objective
Gans' operational success relies on one critical factor: ensuring scooters are parked exactly where users actually need them. Asymmetric real-world factors—such as morning commuter flows, adverse weather conditions, or low-cost tourist arrivals—constantly shift the fleet in a highly unorganized manner.

The goal of this project was to design and optimize an ETL (Extract, Transform, Load) pipeline using Python and SQL to automatically gather data from external sources (Weather and Flights). This unified data structure directly supports corporate predictive strategies for fleet relocation via transport trucks or economic user incentives.

## 🛠️ Tech Stack
* **Language:** Python 3.13
* **Python Libraries:** pandas, sqlalchemy, requests, pymysql, datetime
* **Database:** MySQL 8.0 (Relational)
* **IDEs:** Jupyter Notebooks / VS Code

## 📐 Data Architecture & Database Optimization
The database architecture was engineered to be fully dynamic, moving past static data limitations and protecting historical records through advanced Data Engineering practices.

<img width="963" height="673" alt="Screenshot 2026-07-27 alle 12 08 41" src="https://github.com/user-attachments/assets/eab88493-5256-4722-84a3-4ca5b7a36d36" />

### Repository File Structure:
* **1.0 city_population_sql_import.py:** Extracts and loads core city master data and historical demographic records into the MySQL database.
* **2.0 extract_weather_infos.py:** ETL script that extracts and tracks dynamic 5-day weather forecasts via API.
* **3.0 flights_df_creation.py:** ETL script that monitors incoming tourist streams, optimized to handle the strict 12-hour window limit imposed by the flights API.
* **define schemas.sql:** The official database schema including constraints, primary keys, and foreign keys.

### 🏆 Key Design Choices & Technical Solutions:
* **Database Optimization (ICAO Design):** Departing from the rigid theoretical layout, I optimized the schema by consolidating airport registries into a single, streamlined airports table based on ICAO codes (4 letters). This aligns perfectly with international aviation tracking standards and keeps table relationships highly efficient.
* **Upsert Logic (Anti-Duplication):** To guarantee data integrity and protect the auto-incrementing primary IDs required by project specifications, I implemented combined UNIQUE KEY constraints on MySQL. Python loads fresh records into a transient staging table (`flight_temporary`) and merges them into the official tables using the `ON DUPLICATE KEY UPDATE` clause.
* **Historical Data Integrity:** Thanks to the transactional design, running these scripts daily does not overwrite or wipe out previous historical weather logs. Instead, it dynamically appends and refines future forecasts as they become more accurate over time.
* **Flexible Time Matching:** Because flights land at any minute while weather forecasts are locked in 3-hour blocks, data blending was resolved via a custom SQL View. This virtual layer applies a flexible temporal filter (`BETWEEN` +/- 1.5 hours) to seamlessly pair a flight's landing time with its closest weather outlook block.

## 🚀 Future Enhancements & Scalability
The pipeline is fully parameterized using native time scripts (`datetime.now()`) and is production-ready for automation:
* **Local Automation:** Exporting the notebooks into standalone `.py` scripts and configuring a macOS Cron Job to trigger and update the database automatically every morning at 07:00, removing any need for manual execution.
