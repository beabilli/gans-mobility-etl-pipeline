-- =====================================================================
-- COMPLETE AND DEFINITIVE DATABASE SCHEMA FOR GANS PROJECT (ICAO COMPLIANT)
-- =====================================================================

DROP DATABASE IF EXISTS gans_database;
CREATE DATABASE gans_database;
USE gans_database;

-- 1. City Table: Stores core geographical and administrative data for each city
CREATE TABLE city (
    city_id INT AUTO_INCREMENT, 
    city_name VARCHAR(100) NOT NULL, 
    country VARCHAR(100), 
    latitude DECIMAL(9,6), 
    longitude DECIMAL(9,6),
    PRIMARY KEY (city_id) 
);

-- 2. Population Table: Tracks historical demographic data linked to each city
CREATE TABLE population (
    population_id INT AUTO_INCREMENT,
    city_id INT,
    population_size DECIMAL(10,2),
    timestamp_population INT,
    PRIMARY KEY (population_id), 
    FOREIGN KEY (city_id) REFERENCES city(city_id) ON DELETE CASCADE
);

-- 3. Airports Table: Optimized bridge table mapping cities to their airport ICAO codes
CREATE TABLE airports (
    arrival_icao VARCHAR(4), 
    city_id INT,
    PRIMARY KEY (arrival_icao), 
    FOREIGN KEY (city_id) REFERENCES city(city_id) ON DELETE CASCADE
);

-- 4. Weather Table: Stores 5-day weather forecasts with unique constraints and float precision
CREATE TABLE weather (
    weather_id INT AUTO_INCREMENT,
    city_id INT,
    forecast_time DATETIME,
    outlook VARCHAR(255),
    temperature FLOAT,
    feels_like FLOAT,
    wind_speed FLOAT,
    rain_prob FLOAT,
    PRIMARY KEY (weather_id),
    FOREIGN KEY (city_id) REFERENCES city(city_id) ON DELETE CASCADE,
    UNIQUE KEY unique_weather (city_id, forecast_time)
);

-- 5. Flight Table: Tracks incoming flights with unique anti-duplication constraints based on ICAO codes
CREATE TABLE flight (
    flight_id INT AUTO_INCREMENT,
    flight_num VARCHAR(25),
    departure_icao VARCHAR(4),
    arrival_time DATETIME,
    arrival_icao VARCHAR(4), 
    city_name VARCHAR(100),   
    PRIMARY KEY (flight_id),
    FOREIGN KEY (arrival_icao) REFERENCES airports(arrival_icao) ON DELETE CASCADE, 
    UNIQUE KEY unique_flight (flight_num, arrival_time, arrival_icao) 
);
