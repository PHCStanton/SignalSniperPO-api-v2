#!/usr/bin/env python3
"""
query_database.py - Script to query the trades database
"""

import sqlite3
import sys
import os

def query_database(db_file):
    """Query the database and print results."""
    if not os.path.exists(db_file):
        print(f"Database file not found: {db_file}")
        return False
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Query signals table
        print("\n=== Signals Table ===")
        cursor.execute("SELECT * FROM signals")
        rows = cursor.fetchall()
        
        if not rows:
            print("No signals found")
        else:
            # Print column names
            columns = [description[0] for description in cursor.description]
            print(" | ".join(columns))
            print("-" * 80)
            
            # Print rows
            for row in rows:
                print(" | ".join(str(item) for item in row))
        
        # Query trades table
        print("\n=== Trades Table ===")
        cursor.execute("SELECT * FROM trades")
        rows = cursor.fetchall()
        
        if not rows:
            print("No trades found")
        else:
            # Print column names
            columns = [description[0] for description in cursor.description]
            print(" | ".join(columns))
            print("-" * 80)
            
            # Print rows
            for row in rows:
                print(" | ".join(str(item) for item in row))
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return False

if __name__ == "__main__":
    db_file = "data/trades.db"
    if len(sys.argv) > 1:
        db_file = sys.argv[1]
    
    query_database(db_file)
