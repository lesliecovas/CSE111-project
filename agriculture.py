import sqlite3
from sqlite3 import Error
import csv
import os

# -------------------------
# DATABASE CONNECTION
# -------------------------
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
    except Error as e:
        print(e)
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")

# -------------------------
# CREATE TABLES
# -------------------------
def createTables(conn):
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS crops (
        crop_id INTEGER PRIMARY KEY,
        crop_name VARCHAR(100),
        crop_group VARCHAR(100)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS districts (
        district_id INTEGER PRIMARY KEY,
        state_name VARCHAR(100),
        district_name VARCHAR(100)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS markets (
        market_id INTEGER PRIMARY KEY,
        market_name VARCHAR(100),
        district_id INTEGER,
        FOREIGN KEY (district_id) REFERENCES districts(district_id)
    );
    """)

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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS crop_pesticide (
        crop_id INTEGER,
        pesticide_id INTEGER,
        PRIMARY KEY (crop_id, pesticide_id),
        FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
        FOREIGN KEY (pesticide_id) REFERENCES pesticide_use(pesticide_id)
    );
    """)

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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS crop_district (
        crop_id INTEGER,
        district_id INTEGER,
        avg_yield DOUBLE,
        total_area DOUBLE,
        best_season VARCHAR(100),
        PRIMARY KEY ( district_id),
        FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
        FOREIGN KEY (district_id) REFERENCES districts(district_id)
    );
    """)

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
    conn.commit()
    print("All tables created successfully!")

# -------------------------
# CLEAR TABLES
# -------------------------
def clearTables(conn):
    cur = conn.cursor()
    tables = ["sustainability_data", "farm_weather", "crop_requirements", "crop_district",
              "crop_production_statistic", "crop_arrival_price", "crop_pesticide",
              "pesticide_use", "markets", "districts", "crops"]
    for t in tables:
        cur.execute(f"DELETE FROM {t}")
    conn.commit()
    print("All tables cleared successfully!")

# -------------------------
# IMPORT CSV WITH PARENT CHECK
# -------------------------
def importCSV(conn, table_name):
    filename = table_name + ".csv"
    if not os.path.exists(filename):
        print(f"CSV file '{filename}' not found. Skipping.")
        return

    print(f"Importing {filename} into {table_name}")
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name});")
    columns = [col[1] for col in cur.fetchall()]

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert empty string to None
            data = {k: (row[k] if row[k] != "" else None) for k in columns if k in row}

            # Auto-insert missing parent records if necessary
            if table_name == "crop_district" or table_name == "crop_pesticide" or table_name == "crop_arrival_price" \
               or table_name == "crop_production_statistic" or table_name == "crop_requirements" \
               or table_name == "sustainability_data":
                # crops
                if "crop_id" in data and data["crop_id"]:
                    cur.execute("INSERT OR IGNORE INTO crops(crop_id, crop_name, crop_group) VALUES (?, ?, ?)",
                                (int(data["crop_id"]), f"Unknown_{data['crop_id']}", "Unknown"))

                # districts
                if "district_id" in data and data["district_id"]:
                    cur.execute("INSERT OR IGNORE INTO districts(district_id, state_name, district_name) VALUES (?, ?, ?)",
                                (int(data["district_id"]), f"Unknown_{data['district_id']}", f"Unknown_{data['district_id']}"))

            if table_name == "crop_pesticide":
                if "pesticide_id" in data and data["pesticide_id"]:
                    cur.execute("INSERT OR IGNORE INTO pesticide_use(pesticide_id, district_id, compound) VALUES (?, ?, ?)",
                                (int(data["pesticide_id"]), None, f"Unknown_{data['pesticide_id']}"))

            columns_str = ", ".join(data.keys())
            placeholders = ", ".join(["?"]*len(data))
            values = [data[k] for k in data.keys()]
            try:
                cur.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})", values)
            except Error as e:
                print(f"Error inserting row into {table_name}: {e}")
                continue
    conn.commit()
    print(f"Finished importing {table_name}\n")

# -------------------------
# MAIN FUNCTION
# -------------------------
def main():
    dbfile = "agriculture.db"
    conn = openConnection(dbfile)
    createTables(conn)
    clearTables(conn)

    tables_order = [
        "crops",
        "districts",
        "markets",
        "pesticide_use",
        "crop_pesticide",
        "crop_arrival_price",
        "crop_production_statistic",
        "crop_district",
        "crop_requirements",
        "farm_weather",
        "sustainability_data"
    ]

    for t in tables_order:
        importCSV(conn, t)

    closeConnect(conn, dbfile)

if __name__ == "__main__":
    main()
