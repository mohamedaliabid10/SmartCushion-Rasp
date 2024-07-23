import spidev
import time
import RPi.GPIO as GPIO
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib

# Load the Random Forest model
model_path = "/home/pi/smart_cushion/models/random_forest_model.pkl"
model = joblib.load(model_path)


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

try:
    while True:
        # Read data from channels on the MCP3008
        adc_value_mcp1_ch0 = read_channel(0, 0) #capteur0
        adc_value_mcp1_ch1 = read_channel(1, 0) #capteur1
        adc_value_mcp1_ch2 = read_channel(2, 0) #capteur2
        adc_value_mcp1_ch3 = read_channel(3, 0) #capteur3
        adc_value_mcp1_ch4 = read_channel(4, 0) #capteur4
        adc_value_mcp1_ch5 = read_channel(5, 0) #capteur5
        adc_value_mcp1_ch6 = read_channel(6, 0) #capteur6
        adc_value_mcp1_ch7 = read_channel(7, 0) #capteur7
        adc_value_mcp2_ch0 = read_channel(0, 1) #capteur10
        adc_value_mcp2_ch1 = read_channel(1, 1) #capteur11
        adc_value_mcp2_ch2 = read_channel(2, 1) #capteur12
        adc_value_mcp2_ch3 = read_channel(3, 1) #capteur8
        adc_value_mcp2_ch4 = read_channel(4, 1) #capteur9

        # Create a new data point for prediction
        new_data = np.array([[
            adc_value_mcp1_ch0, adc_value_mcp1_ch1, adc_value_mcp1_ch2,
            adc_value_mcp1_ch3, adc_value_mcp1_ch4, adc_value_mcp1_ch5,
            adc_value_mcp1_ch6, adc_value_mcp1_ch7, adc_value_mcp2_ch3,
            adc_value_mcp2_ch4, adc_value_mcp2_ch0, adc_value_mcp2_ch1,
            adc_value_mcp2_ch2
        ]])
        
        # Standardize the new data point if scaler was used
        # Uncomment the following line if you used a scaler during training
        # new_data_scaled = scaler.transform(new_data)
        # If no scaler was used, use new_data directly
        new_data_scaled = new_data  # Comment this line if scaler was used

        # Predict the posture
        y_pred = model.predict(new_data_scaled)
        posture_pred = y_pred[0]  # Assuming the model outputs the predicted class directly
        
        # Print the sensor values and the prediction
        print(f"Sensor Values: {new_data[0]}")
        print(f"Predicted Posture: {posture_pred}")

        time.sleep(1)

except KeyboardInterrupt:
    spi.close()
    GPIO.cleanup()
    print("Program terminated")

except Exception as e:
    print(f"An error occurred: {e}")
    spi.close()
    GPIO.cleanup()
