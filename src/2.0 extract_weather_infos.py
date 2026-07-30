from sqlalchemy import create_engine
import requests
import pandas as pd
from sqlalchemy import text


schema = "gans_database" 
host = "127.0.0.1"          
user = "root"              
password = "insertyourpassword"   
port = 3306                 

connection_string = f'mysql+pymysql://{user}:{password}@{host}:{port}/{schema}'

engine = create_engine(connection_string)
df_city = pd.read_sql("SELECT * FROM city", engine)
#DEFINE AN ETL FUNCTION FOR A 5-DAY WEATHER FORECAST
def get_weather(city_df):
    
    api_key = "insertyourkeyhere"
    url = "https://api.openweathermap.org/data/2.5/forecast"
    
    # Empty lists
    city_ids = []
    dt_txt = []
    outlook = []
    temperature = []
    feels_like = []
    speed = []
    pop = []
    
    # 2. For loop on rows of city_df table
    for index, row in city_df.iterrows():
        
        # take lat and lon from city_df rows
        lat = row["latitude"]
        lon = row["longitude"]
        current_id = row["city_id"]
        
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        response = requests.get(url=url, params=params)
        weather_json = response.json()
        
        # 4. Inner loop to extract the 40 blocks for that city
        for i in range(len(weather_json["list"])):
            city_ids.append(current_id) # Salviamo l'ID per non perderlo!
            dt_txt.append(weather_json["list"][i]["dt_txt"])
            outlook.append(weather_json["list"][i]["weather"][0]["description"])
            temperature.append(weather_json["list"][i]["main"]["temp"])
            feels_like.append(weather_json["list"][i]["main"]["feels_like"])
            speed.append(weather_json["list"][i]["wind"]["speed"])
            pop.append(weather_json["list"][i]["pop"])
            
    # 5. Create the final dictionary
    weather_dict = {
        "city_id": city_ids,
        "forecast_time": dt_txt,
        "outlook": outlook,
        "temperature": temperature,
        "feels_like": feels_like,
        "wind_speed": speed,
        "rain_prob": pop
    }
    
    # Transform the final dictionary in Dataframe
    final_df = pd.DataFrame(weather_dict)
    return final_df
#USE THE FUNCTION ON CITY_DF
# read city from MySQL
city_from_sql = pd.read_sql("city", con=engine)

# Use get_weather function
bulk_weather_df = get_weather(city_from_sql)

# Remove old temporary table remnants
with engine.begin() as connection:
    connection.execute(text("DROP TABLE IF EXISTS weather_temporary;"))

# Let's load the fresh data into the temporary table
bulk_weather_df.to_sql(
    "weather_temporary", con=engine, if_exists="replace", index=False
)

# Query to insert data into the 'weather' table without duplicates
upsert_query = """
INSERT INTO weather (city_id, forecast_time, outlook, temperature, feels_like, wind_speed, rain_prob)
SELECT city_id, forecast_time, outlook, temperature, feels_like, wind_speed, rain_prob 
FROM weather_temporary
AS nuovi_dati
ON DUPLICATE KEY UPDATE 
    outlook = nuovi_dati.outlook,
    temperature = nuovi_dati.temperature,
    feels_like = nuovi_dati.feels_like,
    wind_speed = nuovi_dati.wind_speed,
    rain_prob = nuovi_dati.rain_prob;
"""

# We perform the final transfer and clean the database.
with engine.begin() as connection:
    connection.execute(text(upsert_query))
    connection.execute(text("DROP TABLE IF EXISTS weather_temporary;"))

