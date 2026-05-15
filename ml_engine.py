import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib
import os

MODEL_PATH = 'memory_model.pkl'

def generate_mock_dataset(filepath='mock_student_data.csv', num_samples=200):
    """Generates a mock dataset for memory retention if a real one isn't available."""
    np.random.seed(42)
    
    student_ids = [f"STU{str(i).zfill(4)}" for i in range(1, num_samples + 1)]
    names = [f"Student {i}" for i in range(1, num_samples + 1)]
    
    # Features
    hours_studied = np.random.uniform(1.0, 10.0, num_samples)
    previous_score = np.random.uniform(40.0, 100.0, num_samples)
    sleep_hours = np.random.uniform(4.0, 10.0, num_samples)
    
    # Target: Memory Retention Score (simulated formula with some noise)
    # More sleep, more study, better previous score = higher retention
    retention_score = (hours_studied * 3) + (previous_score * 0.4) + (sleep_hours * 2) + np.random.normal(0, 5, num_samples)
    
    # Clip between 0 and 100
    retention_score = np.clip(retention_score, 0, 100)
    
    colleges = ['Alpha College of Engineering', 'Beta Institute of Science', 'Gamma Tech', 'Delta University']
    departments = ['Computer Science', 'Information Technology', 'Mechanical Engineering', 'Electronics']
    
    df = pd.DataFrame({
        'student_id': student_ids,
        'name': names,
        'school': [np.random.choice(colleges) for _ in range(num_samples)],
        'department': [np.random.choice(departments) for _ in range(num_samples)],
        'hours_studied': np.round(hours_studied, 1),
        'previous_score': np.round(previous_score, 1),
        'sleep_hours': np.round(sleep_hours, 1),
        'retention_score': np.round(retention_score, 1)
    })
    
    return df

def train_model(data):
    """Trains the Random Forest model on the given CSV data or DataFrame."""
    try:
        if isinstance(data, str):
            df = pd.read_csv(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            return False, "Invalid data format"
        
        # Sanitize column names: strip spaces and lowercase
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Mapping for flexibility
        column_mapping = {
            'student name': 'name',
            'student_name': 'name',
            'student id': 'student_id',
            'school': 'college'
        }
        df = df.rename(columns=column_mapping)
        
        # We need these columns
        features = ['hours_studied', 'previous_score', 'sleep_hours']
        target = 'retention_score'
        
        if not all(col in df.columns for col in features + [target]):
            missing = [col for col in features + [target] if col not in df.columns]
            return False, f"CSV is missing required columns: {', '.join(missing)}"
            
        X = df[features]
        y = df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        print(f"Model trained. MSE: {mse:.2f}")
        
        # Save model
        joblib.dump(model, MODEL_PATH)
        return True, "Model trained successfully!"
    except Exception as e:
        return False, str(e)

def batch_predict(df):
    """Predicts scores for an entire dataframe."""
    if not os.path.exists(MODEL_PATH):
        mock_file = generate_mock_dataset()
        train_model(mock_file)
        
    try:
        model = joblib.load(MODEL_PATH)
        features = df[['hours_studied', 'previous_score', 'sleep_hours']]
        predictions = model.predict(features)
        df['retention_score'] = np.clip(predictions, 0, 100)
        return True, df
    except Exception as e:
        return False, str(e)

def predict_retention(hours_studied, previous_score, sleep_hours):
    """Predicts memory retention score using the trained model."""
    if not os.path.exists(MODEL_PATH):
        mock_file = generate_mock_dataset()
        train_model(mock_file)
        
    try:
        model = joblib.load(MODEL_PATH)
        features = pd.DataFrame({
            'hours_studied': [hours_studied],
            'previous_score': [previous_score],
            'sleep_hours': [sleep_hours]
        })
        prediction = model.predict(features)[0]
        return np.clip(prediction, 0, 100)
    except Exception as e:
        print(f"Prediction error: {e}")
        return 0.0

if __name__ == '__main__':
    print("Generating mock data and testing engine...")
    df = generate_mock_dataset()
    s, msg = train_model(df)
    print(msg)
    test_pred = predict_retention(5.0, 75.0, 7.0)
    print(f"Test prediction: {test_pred}")
