from app import app
from models import db, User, StudentRecord
import os

def check_system():
    with app.app_context():
        users = User.query.all()
        print(f"Users: {[(u.id, u.username) for u in users]}")
        
        records = StudentRecord.query.count()
        print(f"Total Student Records: {records}")
        
        # Check for uploaded_data_*.csv files
        files = [f for f in os.listdir('.') if f.startswith('uploaded_data')]
        print(f"Uploaded data files: {files}")
        for f in files:
            print(f"  {f}: {os.path.getsize(f)} bytes")

if __name__ == '__main__':
    check_system()
