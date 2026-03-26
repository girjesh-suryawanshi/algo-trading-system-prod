import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

MODEL_PATH = "signal_filter_model.pkl"

def train_model(data: pd.DataFrame):
    """
    Trains a simple RandomForest model to filter signals.
    Features: Premium, Volume, Momentum
    """
    X = data[['premium', 'volume', 'momentum']]
    y = data['success'] # 1 if target hit, 0 otherwise
    
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print("AI Model Trained Successfully")

def predict_signal(premium, volume, momentum):
    """
    Decides whether to take a trade based on features.
    """
    if not os.path.exists(MODEL_PATH):
        return True # Default to True if no model trained
    
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    prediction = model.predict([[premium, volume, momentum]])
    return bool(prediction[0])
