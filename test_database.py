# test_database.py
# Quick script to test if database is properly set up

import sqlite3
import os

def test_database():
    """Test if agriculture.db exists and has data"""
    
    if not os.path.exists("agriculture.db"):
        print("❌ agriculture.db not found!")
        print("   Run: python agriculture.py")
        return False
    
    print("✅ Database file found")
    
    try:
        conn = sqlite3.connect("agriculture.db")
        cur = conn.cursor()
        
        # Test each table
        tables = [
            "crops", "districts", "markets", "pesticide_use",
            "crop_pesticide", "crop_district", "crop_arrival_price",
            "crop_production_statistic", "crop_requirements",
            "farm_weather", "sustainability_data"
        ]
        
        print("\n📊 Table Statistics:")
        print("-" * 50)
        
        total_records = 0
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            total_records += count
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {table:30s} {count:6d} records")
        
        print("-" * 50)
        print(f"   Total Records: {total_records}")
        
        # Test some basic queries
        print("\n🔍 Quick Data Tests:")
        print("-" * 50)
        
        # Test crops
        cur.execute("SELECT COUNT(*) FROM crops")
        crop_count = cur.fetchone()[0]
        print(f"✅ Crops: {crop_count}")
        
        # Test districts
        cur.execute("SELECT COUNT(DISTINCT state_name) FROM districts WHERE state_name IS NOT NULL")
        state_count = cur.fetchone()[0]
        print(f"✅ States: {state_count}")
        
        # Test production
        cur.execute("SELECT COUNT(*) FROM crop_production_statistic")
        prod_count = cur.fetchone()[0]
        print(f"✅ Production records: {prod_count}")
        
        # Test joins
        cur.execute("""
            SELECT COUNT(*) 
            FROM crop_production_statistic p
            JOIN crops c ON p.crop_id = c.crop_id
            JOIN districts d ON p.district_id = d.district_id
        """)
        join_count = cur.fetchone()[0]
        print(f"✅ Successful joins: {join_count}")
        
        # Test foreign keys
        cur.execute("PRAGMA foreign_keys")
        fk_status = cur.fetchone()[0]
        fk_text = "Enabled" if fk_status else "Disabled"
        print(f"✅ Foreign keys: {fk_text}")
        
        conn.close()
        
        print("\n" + "=" * 50)
        if total_records > 0:
            print("✅ DATABASE IS READY!")
            print("   Run: python gui.py")
        else:
            print("⚠️  Database exists but has no data")
            print("   Run: python agriculture.py")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing database: {e}")
        return False

def show_sample_data():
    """Show sample data from key tables"""
    try:
        conn = sqlite3.connect("agriculture.db")
        cur = conn.cursor()
        
        print("\n\n📋 Sample Data Preview:")
        print("=" * 50)
        
        # Sample crops
        print("\n🌾 Sample Crops:")
        cur.execute("SELECT crop_id, crop_name, crop_group FROM crops LIMIT 5")
        for row in cur.fetchall():
            print(f"   ID: {row[0]:3d} | {row[1]:20s} | {row[2] or 'N/A'}")
        
        # Sample districts
        print("\n📍 Sample Districts:")
        cur.execute("SELECT district_id, state_name, district_name FROM districts LIMIT 5")
        for row in cur.fetchall():
            print(f"   ID: {row[0]:3d} | {row[1]:15s} | {row[2]}")
        
        # Sample production
        print("\n📊 Sample Production Data:")
        cur.execute("""
            SELECT c.crop_name, d.district_name, p.season, p.yield
            FROM crop_production_statistic p
            JOIN crops c ON p.crop_id = c.crop_id
            JOIN districts d ON p.district_id = d.district_id
            WHERE p.yield IS NOT NULL
            LIMIT 5
        """)
        for row in cur.fetchall():
            print(f"   {row[0]:15s} | {row[1]:15s} | {row[2]:10s} | Yield: {row[3]:.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"Could not show sample data: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🌾 Agricultural Database Test")
    print("=" * 50 + "\n")
    
    if test_database():
        show_sample_data()
    
    print("\n")