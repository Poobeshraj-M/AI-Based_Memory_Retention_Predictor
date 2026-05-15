import os
import pandas as pd
import numpy as np
from ml_engine import generate_mock_dataset

def test_dashboard_loading():
    user_id = 1
    filepath = f'test_uploaded_data_{user_id}.csv'
    
    # Simulate generate_mock route
    print(f"Generating mock data to {filepath}...")
    generate_mock_dataset(filepath)
    
    if not os.path.exists(filepath):
        print(f"FAILED: File {filepath} does not exist.")
        return

    # Simulate analytics_dashboard route
    print("Simulating dashboard loading...")
    try:
        df = pd.read_csv(filepath)
        print(f"Original columns: {df.columns.tolist()}")
        
        df.columns = [c.strip().lower() for c in df.columns]
        print(f"Lowercased columns: {df.columns.tolist()}")
        
        column_mapping = {'student name': 'name', 'student_id': 'student_id', 'school': 'college'}
        df = df.rename(columns=column_mapping)
        print(f"Renamed columns: {df.columns.tolist()}")
        
        required = ['name', 'hours_studied', 'sleep_hours', 'previous_score', 'retention_score']
        missing = [col for col in required if col not in df.columns]
        
        if not missing:
            print("SUCCESS: All required columns found.")
            chart_data = {
                'labels': df['name'].tolist(),
                'hours_studied': df['hours_studied'].tolist(),
                'sleep_hours': df['sleep_hours'].tolist(),
                'previous_score': df['previous_score'].tolist(),
                'retention_score': df['retention_score'].tolist()
            }
            print(f"Chart data labels count: {len(chart_data['labels'])}")
        else:
            print(f"FAILED: Missing columns: {missing}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    test_dashboard_loading()
