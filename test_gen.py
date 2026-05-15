from app import app, db
from models import User
from ml_engine import generate_mock_dataset, train_model
import os

def run_mock_gen():
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            print("Admin user not found")
            return
        
        filepath = f'uploaded_data_{user.id}.csv'
        print(f"Generating mock data for user {user.id} at {filepath}...")
        generate_mock_dataset(filepath)
        
        if os.path.exists(filepath):
            print(f"File created: {filepath}, size: {os.path.getsize(filepath)} bytes")
            success, msg = train_model(filepath)
            print(f"Training success: {success}, msg: {msg}")
        else:
            print(f"FAILED to create file: {filepath}")

if __name__ == '__main__':
    run_mock_gen()
