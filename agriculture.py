import sqlite3
from sqlite3 import Error
import csv
import os

# -------------------------
# DATABASE CONNECTION
# -------------------------

def openConnection(_dbFile):
    print("+++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Open database:", _dbFile)
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
    print("Close database:", _dbFile)
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
        crop_name TEXT,
        crop_group TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS districts (
        district_id INTEGER PRIMARY KEY,
        state_name TEXT,
        district_name TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS markets (
        market_id INTEGER PRIMARY KEY,
        market_name TEXT,
        district_id INTEGER,
        FOREIGN KEY(district_id) REFERENCES districts(district_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pesticide_use (
        pesticide_id INTEGER PRIMARY KEY,
        district_id INTEGER,
        compound TEXT,
        low_estimate REAL,
        high_estimate REAL,
        FOREIGN KEY(district_id) REFERENCES districts(district_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS crop_pesticide (
        crop_id INTEGER,
        pesticide_id INTEGER,
        FOREIGN KEY(crop_id) REFERENCES crops(crop_id),
        FOREIGN KEY(pesticide_id) REFERENCES pesticide_use(pesticide_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS crop_district (
        crop_id INTEGER,
        district_id INTEGER,
        avg_yield REAL,
        total_area REAL,
        best_season TEXT,
        FOREIGN KEY(crop_id) REFERENCES crops(crop_id),
        FOREIGN KEY(district_id) REFERENCES districts(district_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS crop_arrival_price (
        arrival_id INTEGER PRIMARY KEY,
        crop_id INTEGER,
        district_id INTEGER,
        market_id INTEGER,
        variety TEXT,
        arrival_date TEXT,
        arrival_tonnes REAL,
        min_price_rs_per_quintal REAL,
        max_price_rs_per_quintal REAL,
        modal_price_rs_per_quintal REAL,
        FOREIGN KEY(crop_id) REFERENCES crops(crop_id),
        FOREIGN KEY(district_id) REFERENCES districts(district_id),
        FOREIGN KEY(market_id) REFERENCES markets(market_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS crop_production_statistic (
        stat_id INTEGER PRIMARY KEY,
        crop_id INTEGER,
        district_id INTEGER,
        season TEXT,
        area REAL,
        production REAL,
        yield REAL,
        FOREIGN KEY(crop_id) REFERENCES crops(crop_id),
        FOREIGN KEY(district_id) REFERENCES districts(district_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS crop_requirements (
        requirement_id INTEGER PRIMARY KEY,
        crop_id INTEGER,
        N REAL,
        P REAL,
        K REAL,
        temperature REAL,
        humidity REAL,
        ph REAL,
        rainfall REAL,
        FOREIGN KEY(crop_id) REFERENCES crops(crop_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS farm_weather (
        weather_id INTEGER PRIMARY KEY,
        district_id INTEGER,
        maxT REAL,
        minT REAL,
        windspeed REAL,
        humidity REAL,
        precipitation REAL,
        FOREIGN KEY(district_id) REFERENCES districts(district_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sustainability_data (
        record_id INTEGER PRIMARY KEY,
        crop_id INTEGER,
        district_id INTEGER,
        soil_ph REAL,
        soil_moisture REAL,
        temperature_c REAL,
        rainfall_mm REAL,
        fertilizer_used REAL,
        pesticide_usage REAL,
        crop_yield REAL,
        sustainability_score REAL,
        FOREIGN KEY(crop_id) REFERENCES crops(crop_id),
        FOREIGN KEY(district_id) REFERENCES districts(district_id)
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
# IMPORT CSV
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

    # Open with utf-8-sig encoding to automatically remove BOM
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        row_count = 0
        for row in reader:
            row_count += 1
            data = {}
            for k in columns:
                if k in row:
                    val = row[k].strip()
                    if val == "":
                        data[k] = None
                    else:
                        if k in ["crop_id", "district_id", "pesticide_id", 
                                 "arrival_id", "stat_id", "requirement_id", "weather_id", "record_id", "market_id"]:
                            data[k] = int(float(val))
                        else:
                            try:
                                data[k] = float(val)
                            except:
                                data[k] = val
                else:
                    data[k] = None

            # Auto-insert missing parent records ONLY if not importing the parent table itself
            if table_name != "crops" and "crop_id" in data and data["crop_id"] is not None:
                cur.execute("INSERT OR IGNORE INTO crops(crop_id, crop_name, crop_group) VALUES (?, ?, ?)",
                            (data["crop_id"], f"Unknown_{data['crop_id']}", "Unknown"))
            
            if table_name not in ["districts", "crops"] and "district_id" in data and data["district_id"] is not None:
                cur.execute("INSERT OR IGNORE INTO districts(district_id, state_name, district_name) VALUES (?, ?, ?)",
                            (data["district_id"], f"Unknown_{data['district_id']}", f"Unknown_{data['district_id']}"))
            
            if table_name == "crop_pesticide" and "pesticide_id" in data and data["pesticide_id"] is not None:
                cur.execute("INSERT OR IGNORE INTO pesticide_use(pesticide_id, district_id, compound, low_estimate, high_estimate) VALUES (?, ?, ?, ?, ?)",
                            (data["pesticide_id"], None, f"Unknown_{data['pesticide_id']}", None, None))

            columns_str = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            values = [data[k] for k in data.keys()]

            try:
                cur.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})", values)
            except Error as e:
                # Only print error if it's not a UNIQUE constraint failure
                if "UNIQUE constraint failed" not in str(e):
                    print(f"Error inserting row into {table_name}: {e}")
                    print(f"Data: {data}")
                continue

    conn.commit()
    print(f"Finished importing {table_name} ({row_count} rows)\n")

# -------------------------
# MAIN
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