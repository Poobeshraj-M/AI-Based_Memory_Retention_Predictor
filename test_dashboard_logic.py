from app import app
from models import User
import pandas as pd
import os

def test_dashboard_logic():
    with app.app_context():
        user = User.query.get(1)
        filepath = f'uploaded_data_{user.id}.csv'
        print(f"Checking dashboard for user {user.id} using {filepath}...")
        
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                print(f"Loaded CSV with {len(df)} rows.")
                
                df.columns = [c.strip().lower() for c in df.columns]
                column_mapping = {'student name': 'name', 'student_id': 'student_id', 'school': 'college'}
                df = df.rename(columns=column_mapping)
                
                required = ['name', 'hours_studied', 'sleep_hours', 'previous_score', 'retention_score']
                missing = [col for col in required if col not in df.columns]
                
                if not missing:
                    print("SUCCESS: Required columns found.")
                    # Check if table_rows would be populated
                    table_rows = []
                    for _, row in df.iterrows():
                        table_rows.append({
                            'name': row['name'],
                            'student_id': row.get('student_id', 'N/A'),
                            'college': row.get('college', 'N/A'),
                            'department': row.get('department', 'N/A'),
                            'retention_score': row['retention_score']
                        })
                    print(f"Populated {len(table_rows)} table rows.")
                else:
                    print(f"FAILED: Missing columns: {missing}")
                    print(f"Actual columns: {df.columns.tolist()}")
                    
            except Exception as e:
                print(f"ERROR: {e}")
        else:
            print(f"File {filepath} does not exist.")

if __name__ == '__main__':
    test_dashboard_logic()
