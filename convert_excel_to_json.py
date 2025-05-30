import pandas as pd
import json
from datetime import datetime
import os

def convert_excel_to_json():
    """Convert Excel file to JSON and compare timestamps"""
    
    # Read the Excel file
    excel_file_path = r'data\2025-05-29_TIMESTAMPS\export_history_c78250b78aab87206c5b579ecbfd44c8.xlsx'
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_file_path)
        print(f"Excel file loaded successfully. Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst few rows:")
        print(df.head())
        
        # Convert to JSON
        json_data = df.to_dict('records')
        
        # Save as JSON file
        output_file = r'data\2025-05-29_TIMESTAMPS\export_history_converted.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"\nExcel data converted to JSON and saved as: {output_file}")
        
        # Load the existing timestamps JSON for comparison
        timestamps_file = r'data\2025-05-29_TIMESTAMPS\2025-05-29_timestamps.json'
        with open(timestamps_file, 'r', encoding='utf-8') as f:
            timestamps_data = json.load(f)
        
        print(f"\nLoaded timestamps data with {len(timestamps_data)} records")
        
        # Compare timestamps
        compare_timestamps(json_data, timestamps_data)
        
        return json_data, timestamps_data
        
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def compare_timestamps(excel_data, timestamps_data):
    """Compare timestamps between Excel data and timestamps JSON"""
    
    print("\n" + "="*60)
    print("TIMESTAMP COMPARISON ANALYSIS")
    print("="*60)
    
    # Extract timestamps from both datasets
    print(f"\nExcel data records: {len(excel_data)}")
    print(f"Timestamps data records: {len(timestamps_data)}")
    
    # Look for timestamp columns in Excel data
    timestamp_columns = []
    if excel_data:
        for col in excel_data[0].keys():
            if any(keyword in str(col).lower() for keyword in ['time', 'date', 'timestamp', 'created', 'executed']):
                timestamp_columns.append(col)
    
    print(f"\nPotential timestamp columns in Excel: {timestamp_columns}")
    
    # Extract timestamps from timestamps JSON
    signal_times = []
    execution_times = []
    
    for record in timestamps_data:
        if 'signal_received' in record:
            signal_times.append(record['signal_received'])
        if 'signal_executed' in record:
            execution_times.append(record['signal_executed'])
    
    print(f"\nTimestamps from JSON file:")
    print(f"Signal received times: {len(signal_times)}")
    print(f"Signal executed times: {len(execution_times)}")
    
    # Show sample timestamps
    if signal_times:
        print(f"\nSample signal received times:")
        for i, time_str in enumerate(signal_times[:3]):
            print(f"  {i+1}. {time_str}")
    
    if execution_times:
        print(f"\nSample signal executed times:")
        for i, time_str in enumerate(execution_times[:3]):
            print(f"  {i+1}. {time_str}")
    
    # Show Excel timestamp data if available
    if excel_data and timestamp_columns:
        print(f"\nSample Excel timestamps:")
        for i, record in enumerate(excel_data[:3]):
            print(f"  Record {i+1}:")
            for col in timestamp_columns:
                if col in record:
                    print(f"    {col}: {record[col]}")

if __name__ == "__main__":
    excel_data, timestamps_data = convert_excel_to_json()
