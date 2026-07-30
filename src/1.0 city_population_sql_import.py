import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
# DEFINE A FUNCTION FOR CITY TABLE
def get_city_geo(list_of_cities):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/134.0.0.0"}

    countries = []
    latitudes = []
    longitudes = []

    for city in list_of_cities:
        url = f"https://en.wikipedia.org/wiki/{city}"

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        # 1. Country Extraction
        country = "Not found"
        country_label = soup.find("th", class_="infobox-label", string="Country")
        if country_label:
            country_data = country_label.find_next_sibling("td", class_="infobox-data")
            if country_data:
                country = country_data.get_text(strip=True)
        countries.append(country)

        # 2. Coordinates Extraction (Latitude & Longitude)
        latitude = None
        longitude = None
        geo_span = soup.find("span", class_="geo")

        if geo_span:
            try:
                coords = geo_span.get_text().split(";")
                if len(coords) == 2:
                    latitude = float(coords[0].strip())
                    longitude = float(coords[1].strip())
            except:
                pass

        latitudes.append(latitude)
        longitudes.append(longitude)

    # --- FINAL GEOGRAPHIC DATAFRAME CREATION WITHOUT ID ---
    df = pd.DataFrame({
        "city_name": list_of_cities,
        "country": countries,
        "latitude": latitudes,
        "longitude": longitudes
    })

    return df
#DEFINE A FUNCTION FOR POPULATION TABLE

def get_population(list_of_cities):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/134.0.0.0"}
    populations = []
    years = []  # List to save timestamp years

    for city in list_of_cities:
        url = f"https://en.wikipedia.org/wiki/{city}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        population = 0
        year = None  # Starting value for the year

        try:
            
            pop_element = soup.find(string="Population")
            population = int(pop_element.find_next("td").text.replace(",", ""))

            # Search for the year in the same row as the professor's title (e.g., Berlin)
            header_text = pop_element.find_parent("tr").get_text()
            match_anno = re.search(r'\d{4}', header_text)
            if match_anno:
                year = int(match_anno.group(0))

        except:
            # 2. FALLBACK STRATEGY (Your geometric logic)
            infobox_rows = soup.select("table.infobox tr")
            for index, row in enumerate(infobox_rows):
                header = row.find("th", class_="infobox-header")
                if header and "Population" in header.get_text():

                    # Search for the year in your safe header (e.g., Hamburg)
                    match_anno_geo = re.search(r'\d{4}', header.get_text())
                    if match_anno_geo:
                        year = int(match_anno_geo.group(0))

                    # Get population from the rows below
                    for next_row in infobox_rows[index + 1 : index + 5]:
                        city_label = next_row.find("th", class_="infobox-label")
                        if city_label and "City" in city_label.get_text():
                            data_cell = next_row.find("td", class_="infobox-data")
                            if data_cell:
                                clean_pop = "".join(filter(str.isdigit, data_cell.get_text()))
                                population = int(clean_pop) if clean_pop else 0
                                break
                    break

        # If a city does not have a stated year, use 2024 as a safety net
        if not year:
            year = 2024

        populations.append(population)
        years.append(year)

    # --- CLEAN DATAFRAME CREATION ---
    df = pd.DataFrame({
        "city_name": list_of_cities,                       # Needed for the subsequent merge!
        "population_size": populations,
        "timestamp_population": years
    })

    # Convert population to millions with two decimal places
    df["population_size"] = (df["population_size"] / 1000000).round(2)

    # Clean ordering of temporary columns before database insertion
    df = df[["city_name", "population_size", "timestamp_population"]]

    return df


# CREATE A TABLE FOR CITIES WITH GEO INFO & A TABLE FOR POPULATION WITH DEMOGRAPHIC INFO
city_df = get_city_geo(["Berlin", "Hamburg", "Munich"])
print(city_df)

population_df = get_population(["Berlin", "Hamburg", "Munich"])
print(population_df)
# CONNECT TO DATABASE SCHEMA IN SQL
# Upload city table
schema = "gans_database"
host = "127.0.0.1"
user = "root"
password = "insertyourpassword"
port = 3306

connection_string = f'mysql+pymysql://{user}:{password}@{host}:{port}/{schema}'

city_df.to_sql('city',
                  if_exists='append',
                  con=connection_string,
                  index=False)

# Retrieve information from SQL to this notebook

city_from_sql = pd.read_sql("city", con=connection_string)
print(city_from_sql)

# Merge population table with the city table from SQL

population_df = population_df.merge(city_from_sql, on="city_name", how="left")

population_df = population_df.drop(columns=["city_name"])
population_df = population_df[["city_id", "population_size", "timestamp_population"]]

# Export this new population table to SQL

population_df.to_sql('population', if_exists='append', con=connection_string, index=False)
