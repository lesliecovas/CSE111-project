import sqlite3
from sqlite3 import Error
import csv

def openConnection(_dbFile):
    print("+++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Open database: ", _dbFile)
    conn = None 
    try:
        conn = sqlite3.connect(_dbFile)
        conn.execute("PRAGMA foreign_keys = ON;")
        print("Success")
    except Error as e:
        print(e)
    
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    return conn

def closeConnect(_conn, _dbFile):
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Close database: ", _dbFile)
    try:
        _conn.close()
        print("Success")
    except  Error as e:
        print(e)

    print("++++++++++++++++++++++++++++++++++++++++++++++++++")

def createTable(_conn):
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Create table")
    try:
        cur = _conn.cursor()

        # crops
        cur.execute("""
        CREATE TABLE IF NOT EXISTS crops (
            crop_id INTEGER PRIMARY KEY,
            crop_name VARCHAR(100),
            crop_group VARCHAR(100)
        );
        """)

        # districts
        cur.execute("""
        CREATE TABLE IF NOT EXISTS districts (
            district_id INTEGER PRIMARY KEY,
            state_name VARCHAR(100),
            district_name VARCHAR(100)
        );
        """)

        # markets
        cur.execute("""
        CREATE TABLE IF NOT EXISTS markets (
            market_id INTEGER PRIMARY KEY,
            market_name VARCHAR(100),
            district_id INTEGER,
            FOREIGN KEY (district_id) REFERENCES districts(district_id)
        );
        """)

        # crop_arrival_price
        cur.execute("""
        CREATE TABLE IF NOT EXISTS crop_arrival_price (
            arrival_id INTEGER PRIMARY KEY,
            crop_id INTEGER,
            district_id INTEGER,
            market_id INTEGER,
            variety VARCHAR(100),
            arrival_date DATE,
            arrival_tonnes DOUBLE,
            min_price_rs_per_quintal DOUBLE,
            max_price_rs_per_quintal DOUBLE,
            modal_price_rs_per_quintal DOUBLE,
            FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
            FOREIGN KEY (district_id) REFERENCES districts(district_id),
            FOREIGN KEY (market_id) REFERENCES markets(market_id)
        );
        """)

        # crop_production_statistic
        cur.execute("""
        CREATE TABLE IF NOT EXISTS crop_production_statistic (
            stat_id INTEGER PRIMARY KEY,
            crop_id INTEGER,
            district_id INTEGER,
            season VARCHAR(100),
            area DOUBLE,
            production DOUBLE,
            yield DOUBLE,
            FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
            FOREIGN KEY (district_id) REFERENCES districts(district_id)
        );
        """)

        # crop_district
        cur.execute("""
        CREATE TABLE IF NOT EXISTS crop_district (
            crop_id INTEGER,
            district_id INTEGER,
            avg_yield DOUBLE,
            total_area DOUBLE,
            best_season VARCHAR(100),
            PRIMARY KEY (crop_id, district_id),
            FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
            FOREIGN KEY (district_id) REFERENCES districts(district_id)
        );
        """)

        # pesticide_use
        cur.execute("""
        CREATE TABLE IF NOT EXISTS pesticide_use (
            pesticide_id INTEGER PRIMARY KEY,
            district_id INTEGER,
            compound VARCHAR(100),
            low_estimate DOUBLE,
            high_estimate DOUBLE,
            FOREIGN KEY (district_id) REFERENCES districts(district_id)
        );
        """)

        # crop_pesticide
        cur.execute("""
        CREATE TABLE IF NOT EXISTS crop_pesticide (
            crop_id INTEGER,
            pesticide_id INTEGER,
            PRIMARY KEY (crop_id, pesticide_id),
            FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
            FOREIGN KEY (pesticide_id) REFERENCES pesticide_use(pesticide_id)
        );
        """)

        # crop_requirements
        cur.execute("""
        CREATE TABLE IF NOT EXISTS crop_requirements (
            requirement_id INTEGER PRIMARY KEY,
            crop_id INTEGER,
            N DOUBLE,
            P DOUBLE,
            K DOUBLE,
            temperature DOUBLE,
            humidity DOUBLE,
            ph DOUBLE,
            rainfall DOUBLE,
            FOREIGN KEY (crop_id) REFERENCES crops(crop_id)
        );
        """)

        # farm_weather
        cur.execute("""
        CREATE TABLE IF NOT EXISTS farm_weather (
            weather_id INTEGER PRIMARY KEY,
            district_id INTEGER,
            maxT DOUBLE,
            minT DOUBLE,
            windspeed DOUBLE,
            humidity DOUBLE,
            precipitation DOUBLE,
            FOREIGN KEY (district_id) REFERENCES districts(district_id)
        );
        """)

        # sustainability_data
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sustainability_data (
            record_id INTEGER PRIMARY KEY,
            crop_id INTEGER,
            district_id INTEGER,
            soil_ph DOUBLE,
            soil_moisture DOUBLE,
            temperature_c DOUBLE,
            rainfall_mm DOUBLE,
            fertilizer_used VARCHAR(100),
            pesticide_usage VARCHAR(100),
            crop_yield DOUBLE,
            sustainability_score DOUBLE,
            FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
            FOREIGN KEY (district_id) REFERENCES districts(district_id)
        );
        """)

        _conn.commit()
        print("Success")

    except Error as e:
        print(e)

    print("++++++++++++++++++++++++++++++++++++++++++++++++++")


# -----------------------------------------------------------
#  IMPORT CSV INTO TABLE (GENERIC)
# -----------------------------------------------------------

def importCSV(_conn, table_name):
    filename = table_name + ".csv"

    if not os.path.exists(filename):
        print(f"CSV file '{filename}' not found. Skipping.")
        return

    print(f"Importing data from {filename} into {table_name}")

    try:
        cur = _conn.cursor()

        # Get table columns
        cur.execute(f"PRAGMA table_info({table_name});")
        table_columns = [col[1] for col in cur.fetchall()]

        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                filtered = {col: row[col] for col in table_columns if col in row and row[col] != ""}

                columns = ", ".join(filtered.keys())
                placeholders = ", ".join(["?"] * len(filtered))
                values = list(filtered.values())

                sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

                try:
                    cur.execute(sql, values)
                except Error as e:
                    print(f"Error inserting row into {table_name}: {e}")
                    continue

        _conn.commit()
        print(f"Finished importing {table_name}\n")

    except Error as e:
        print(e)


def main():
    database = "agriculture.db"
    conn = openConnection(database)
    createTable(conn)

    tables = [
        "crops",
        "districts",
        "markets",
        "crop_arrival_price",
        "crop_production_statistic",
        "crop_district",
        "pesticide_use",
        "crop_pesticide",
        "crop_requirements",
        "farm_weather",
        "sustainability_data"
    ]

    for t in tables:
        importCSV(conn, t)


    closeConnect(conn, database)


if __name__ == '__main__':
    main()
