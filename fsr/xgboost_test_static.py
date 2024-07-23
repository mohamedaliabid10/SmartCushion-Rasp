import numpy as np
import joblib

# Load the XGBoost model
model_path = "/home/pi/smart_cushion/models/xgb_model.pkl"
model = joblib.load(model_path)

# Example list of sensor values
sensor_values = [4.0,0.0,0.0,1.0,109.0,531.0,1.0,1.0,851.0,887.0,892.0,894.0,907.0]

# Convert the list to a NumPy array and reshape for prediction
new_data = np.array([sensor_values])

new_data_scaled = new_data  # Comment this line if scaler was used

# Predict the posture
y_pred = model.predict(new_data_scaled)
posture_pred = y_pred[0]  # Assuming the model outputs the predicted class directly

# Print the sensor values and the prediction
print(f"Sensor Values: {sensor_values}")
print(f"Predicted Posture: {posture_pred}")
