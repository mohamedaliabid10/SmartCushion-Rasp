import spidev
import time
import RPi.GPIO as GPIO
import json
import paho.mqtt.client as mqtt
import numpy as np
import joblib
from datetime import datetime
from collections import Counter
import warnings
from sklearn.exceptions import DataConversionWarning

# Suppress specific warnings
warnings.filterwarnings(action='ignore', category=DataConversionWarning)
warnings.filterwarnings(action='ignore', message="X does not have valid feature names")

# Load the Random Forest model
model_path = "/home/pi/smart_cushion/models/random_forest_model.pkl"
model = joblib.load(model_path)

# MQTT broker configuration
mqtt_broker = "192.168.43.134"
mqtt_port = 1883  # MQTT broker port
mqtt_topic = "/home/smart_cushion/posture"  # MQTT topic to publish posture data

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)  # specifying MQTT protocol version explicitly

# Connect callback function
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code "+str(rc))

# Set the on_connect callback
client.on_connect = on_connect

# Connect to MQTT broker
client.connect(mqtt_broker, mqtt_port, 60)

# GPIO pin numbers for chip select
CS_PINS = [23, 24]  # GPIO 23 for MCP3008_1, GPIO 24 for MCP3008_2

# Set up GPIO
GPIO.setmode(GPIO.BCM)
for pin in CS_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)  # Deselect all chips initially

# SPI configuration
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1350000

def read_channel(channel, cs_index):
    # Select the appropriate MCP3008 by setting the CS line low
    for pin in CS_PINS:
        GPIO.output(pin, GPIO.HIGH)  # Deselect all chips first
    GPIO.output(CS_PINS[cs_index], GPIO.LOW)  # Select the desired chip
    time.sleep(0.001)  # Short delay to ensure proper selection
    
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    
    GPIO.output(CS_PINS[cs_index], GPIO.HIGH)  # Deselect the chip after reading
    time.sleep(0.001)  # Short delay to ensure proper deselection
    return data

# Initialize storage for posture predictions
posture_predictions = []

try:
    while True:
        # Read data from channels on the MCP3008
        adc_values = [
            read_channel(0, 0), read_channel(1, 0), read_channel(2, 0),
            read_channel(3, 0), read_channel(4, 0), read_channel(5, 0),
            read_channel(6, 0), read_channel(7, 0), read_channel(3, 1),
            read_channel(4, 1), read_channel(0, 1), read_channel(1, 1),
            read_channel(2, 1)
        ]

        # Calculate the sum of the sensor values
        sensor_sum = sum(adc_values)

        # Check if the sum of the sensor values is above 300
        if sensor_sum > 300:
            # Create a new data point for prediction
            new_data = np.array([adc_values])
            
            # Standardize the new data point if scaler was used
            # Uncomment the following line if you used a scaler during training
            # new_data_scaled = scaler.transform(new_data)
            # If no scaler was used, use new_data directly
            new_data_scaled = new_data  # Comment this line if scaler was used

            # Predict the posture
            y_pred = model.predict(new_data_scaled)
            posture_pred = y_pred[0]  # Assuming the model outputs the predicted class directly
            
            # Store the prediction
            posture_predictions.append(posture_pred)
            
            # If we have 30 predictions (30 seconds worth), process them
            if len(posture_predictions) >= 20: #kol 20 seconds
                # Find the most frequent posture prediction
                most_common_posture = Counter(posture_predictions).most_common(1)[0][0]
                
                #print values
                print(f"all predicted values:{posture_predictions}")
                # Print the sensor values and the most common posture
                print(f"Most common posture in the last 30 seconds: {most_common_posture}")
                
                # Prepare data as a JSON payload
                data = {
                    "posture": int(most_common_posture),
                }

                # Convert data to JSON format
                payload = json.dumps(data)

                # Publish data to MQTT topic
                client.publish(mqtt_topic, payload)

                # Clear the posture predictions
                posture_predictions = []

        time.sleep(1)

except KeyboardInterrupt:
    spi.close()
    GPIO.cleanup()
    print("Program terminated")

except Exception as e:
    print(f"An error occurred: {e}")
    spi.close()
    GPIO.cleanup()
