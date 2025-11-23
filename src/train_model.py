import pandas as pd
import os
import joblib
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

def train_model():
    print("🤖 Starting Model Training...")

    # UPDATED: Paths are now relative to the root folder
    data_path = os.path.join("data", "processed", "training_data.csv")
    models_path = os.path.join("models")
    os.makedirs(models_path, exist_ok=True)

    if not os.path.exists(data_path):
        print(f"❌ Processed data not found at {data_path}. Run process_data.py first.")
        return

    df = pd.read_csv(data_path)

    # 2. Split Data (Features vs Target)
    X = df.drop(columns=['Likes', 'Comments']) 
    y = df['Likes']

    if len(df) < 5:
        print("⚠️ Not enough data to train (need at least 5 rows). Skipping.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Train Model
    print("🧠 Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 4. Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"📊 Model Performance:")
    print(f"   - MAE (Mean Absolute Error): {mae:.2f}")
    print(f"   - R2 Score: {r2:.2f}")

    # 5. Save Artifacts
    model_file = os.path.join(models_path, "engagement_model.pkl")
    joblib.dump(model, model_file)
    print(f"💾 Model saved to {model_file}")

    metrics_file = os.path.join(models_path, "metrics.json")
    with open(metrics_file, "w") as f:
        json.dump({"mae": mae, "r2": r2}, f)

if __name__ == "__main__":
    train_model()