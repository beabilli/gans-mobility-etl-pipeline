#IMPORT CITY_DF FROM SQL
import pandas as pd
from sqlalchemy import create_engine

# 1. Set connection
USER = 'root'
PASSWORD = 'insertyourpasswordhere'
HOST = '127.0.0.1'
DATABASE = 'gans_database'

# 2. Create the engine
engine = create_engine(f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DATABASE}")

# 3. Read city_df
df = pd.read_sql("SELECT * FROM city", con=engine)

# 4. Display df
print(df.head())

#FIND ALL AIRPORTS FOR EACH LOCATION
import requests
import time

url0 = "https://aerodatabox.p.rapidapi.com/airports/search/location"

headers0 = {
    'x-rapidapi-host': 'aerodatabox.p.rapidapi.com',
    'x-rapidapi-key': 'insertyourapikeyhere'
}

responses = []

# For loop for each row
for index, row in df.iterrows():
    
    querystring = {
        "lat": str(row['latitude']), 
        "lon": str(row['longitude']), 
        "radiusKm": "50", 
        "limit": "10", 
        "withFlightInfoOnly": "false"
    }

    response = requests.get(url0, headers=headers0, params=querystring)
    #
    response_json = response.json()
    responses.append(response_json)
    #
    print(row['city_name'], response_json)


    time.sleep(1.5)
#CREATE AIRPORTS_DF 
import pandas as pd

# 1. Create an empty list to gather all airport rows
airport_list = []

# Use zip to loop through both the API responses and your original DataFrame rows
for city_data, (index, row) in zip(responses, df.iterrows()):

    # Extract the items list containing all airports for THAT specific city
    airport_items = city_data.get("items", [])

    # THE SECOND LOOP: Iterate through each airport found in the items list
    for airport in airport_items:

        # Extract the 4-letter ICAO code for the current airport
        icao_code = airport.get("icao")

        # Safety filter: only add to the DataFrame if a valid ICAO code exists
        if icao_code:

            # Keep the exact original city name from your DataFrame (e.g., Berlin)
            row_data = {"city_name": row["city_name"], "arrival_icao": icao_code}

            # APPEND: Push the row into the global list
            airport_list.append(row_data)

# 2. Convert the full list of dictionaries into the final Pandas DataFrame
df_airports_gans = pd.DataFrame(airport_list)

# Display the clean vertical table
df_airports_gans

#TRANSFER AIRPORTS TABLE ON SQL
import pandas as pd

# 1. Drop duplicates
df_airports_unique = df_airports_gans.drop_duplicates().copy()

# 2. Select 'city_id' and "city_name" from MySQL
df_city_db = pd.read_sql("SELECT city_id, city_name FROM city", con=engine)

# 3. Select 'city_id' and "city_name" from MySQL
df_airports_final = pd.merge(df_airports_unique, df_city_db, on="city_name", how="inner")

# We select only the two columns required for the MySQL schema.
df_airports_to_sql = df_airports_final[['arrival_icao', 'city_id']].copy()

# LOADING INTO MYSQL: Insert the data into the 'airports' table
# We use 'replace' because the list of airports for those cities does not change daily
df_airports_to_sql.to_sql(name="airports", con=engine, if_exists="replace", index=False)
#DEFINE A FUNCTION TO FIND ALL OF THESE INFORMATION FOR THE DF_AIRPORTS CREATED
def get_info_flights(df_airports):

    import time
    from datetime import datetime, timedelta
    import pandas as pd
    import requests

    list_flights3 = []
    # The headers and official credentials we tested earlier
    headers3 = {
        "Content-Type": "application/json",
        "x-rapidapi-host": 'aerodatabox.p.rapidapi.com',
        "x-rapidapi-key": 'insertyourapikeyhere',
    }
    # Automatic calculation of tomorrow's date (12-hour range)
    tomorrow_date2 = datetime.now() + timedelta(days=1)
    tomorrow_date3 = tomorrow_date2.strftime("%Y-%m-%d")

    # It loops directly over the table column you pass it.
    for icao_code in df_airports["arrival_icao"].unique():


        url3 = f"https://aerodatabox.p.rapidapi.com/flights/airports/icao/{icao_code}/{tomorrow_date3}T08:00/{tomorrow_date3}T20:00"
        querystring3 = {
            "withLeg": "true",
            "direction": "Arrival",
            "withCancelled": "true",
            "withCodeshared": "true",
            "withCargo": "true",
            "withPrivate": "true",
            "withLocation": "false",
        }

        response3 = requests.get(url3, headers=headers3, params=querystring3)

        if response3.status_code == 200:
            try:
                flights_datas3 = response3.json()
                for flight in flights_datas3.get("arrivals", []):
                    dict_flights3 = {
                        "flight_num": flight.get("number"),
                        "departure_icao": flight.get("departure", {}).get("airport", {}).get("icao", "N/D"),
                        "arrival_time": flight.get("arrival", {}).get("scheduledTime", {}).get("local", "N/D"),
                        "arrival_icao": icao_code,
                    }
                    list_flights3.append(dict_flights3)
                print(f"Recovered flights for the airport {icao_code}!")
            except Exception:
                print(f"Error reading JSON for the airport {icao_code}.")
        else:
            print(f"No flights or errors for the airport {icao_code}: State {response3.status_code}")

        time.sleep(3)
    # Final df creation
    df_voli3 = pd.DataFrame(list_flights3)

    if not df_voli3.empty:
       # Perform the merge using the table you passed to the function. 
        df_voli_completo3 = pd.merge(df_voli3, df_airports, on="arrival_icao", how="left")
        print("\n Pipeline completed! Table successfully created.")
        return df_voli_completo3
    else:
        print("\nThe flight list remained empty. Check the response statuses above.")
        return df_voli3

from sqlalchemy import text
import pandas as pd

# Use the function for df_airports_gans
df_risultato_finale = get_info_flights(df_airports_gans)

if not df_risultato_finale.empty:
    # 1. Select only the column requested
    df1 = df_risultato_finale[['flight_num', 'departure_icao', 'arrival_time', 'arrival_icao', 'city_name']].copy()
    
    # Remove the time zone for compatibility with MySQL DATETIME.
    df1['arrival_time'] = pd.to_datetime(df1['arrival_time']).dt.tz_localize(None)

    # 2. Cleaning for old temporary tables
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS flight_temporary;"))

     # 3. We load the fresh data into the temporary table
    df1.to_sql(name="flight_temporary", con=engine, if_exists="replace", index=False)

    # 4. Query with temporary disabling of foreign keys to avoid blocking
    upsert_flights_query = """
    INSERT INTO flight (flight_num, departure_icao, arrival_time, arrival_icao, city_name)
    SELECT flight_num, departure_icao, arrival_time, arrival_icao, city_name 
    FROM flight_temporary
    AS nuovi_voli
    ON DUPLICATE KEY UPDATE 
        departure_icao = nuovi_voli.departure_icao,
        arrival_time = nuovi_voli.arrival_time,
        city_name = nuovi_voli.city_name;
    """

    # We carry out everything within a secure transaction.
    with engine.begin() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        connection.execute(text(upsert_flights_query))
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        connection.execute(text("DROP TABLE IF EXISTS flight_temporary;"))

