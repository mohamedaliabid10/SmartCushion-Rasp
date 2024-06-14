import spidev
import time
import RPi.GPIO as GPIO
import pandas as pd
from datetime import datetime

# Prompt for posture number
posture_number = input("Posture Number: ")

# Generate the CSV filename
csv_filename = f"Posture{posture_number}.csv"

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

# Initialize an empty DataFrame
columns = ["timestamp"]
df = pd.DataFrame(columns=columns)

try:
    while True:
        # Read data from channels on the MCP3008
        adc_value_mcp1_ch0 = read_channel(0, 0)
        adc_value_mcp1_ch1 = read_channel(1, 0)
        adc_value_mcp1_ch2 = read_channel(2, 0)
        adc_value_mcp1_ch3 = read_channel(3, 0)
        adc_value_mcp1_ch4 = read_channel(4, 0)
        adc_value_mcp1_ch5 = read_channel(5, 0)
        adc_value_mcp1_ch6 = read_channel(6, 0)
        adc_value_mcp1_ch7 = read_channel(7, 0)
        adc_value_mcp2_ch0 = read_channel(0, 1)
        adc_value_mcp2_ch1 = read_channel(1, 1)
        adc_value_mcp2_ch2 = read_channel(2, 1)
        adc_value_mcp2_ch3 = read_channel(3, 1)
        adc_value_mcp2_ch4 = read_channel(4, 1)

        # Get the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create a new row of data
        new_data = {
            "timestamp": timestamp,
            "capteur 0": adc_value_mcp1_ch0,
            "capteur 1": adc_value_mcp1_ch1,
            "capteur 2": adc_value_mcp1_ch2,
            "capteur 3": adc_value_mcp1_ch3,
            "capteur 4": adc_value_mcp1_ch4,
            "capteur 5": adc_value_mcp1_ch5,
            "capteur 6": adc_value_mcp1_ch6,
            "capteur 7": adc_value_mcp1_ch7,
            "capteur 8": adc_value_mcp2_ch3,
            "capteur 9": adc_value_mcp2_ch4,
            "capteur 10": adc_value_mcp2_ch0,
            "capteur 11": adc_value_mcp2_ch1,
            "capteur 12": adc_value_mcp2_ch2,
        }

        # Convert the new data to a DataFrame and concatenate it with the existing DataFrame
        new_data_df = pd.DataFrame([new_data])
        df = pd.concat([df, new_data_df], ignore_index=True)

        # Print the current readings
        print(f"FSR Value MCP3008 1 Channel 0 capteur 0: {adc_value_mcp1_ch0}")
        print(f"FSR Value MCP3008 1 Channel 1 capteur 1: {adc_value_mcp1_ch1}")
        print(f"FSR Value MCP3008 1 Channel 2 capteur 2: {adc_value_mcp1_ch2}")
        print(f"FSR Value MCP3008 1 Channel 3 capteur 3: {adc_value_mcp1_ch3}")
        print(f"FSR Value MCP3008 1 Channel 4 capteur 4: {adc_value_mcp1_ch4}")
        print(f"FSR Value MCP3008 1 Channel 5 capteur 5: {adc_value_mcp1_ch5}")
        print(f"FSR Value MCP3008 1 Channel 6 capteur 6: {adc_value_mcp1_ch6}")
        print(f"FSR Value MCP3008 1 Channel 7 capteur 7: {adc_value_mcp1_ch7}")
        print(f"FSR Value MCP3008 2 Channel 3 capteur 8: {adc_value_mcp2_ch3}")
        print(f"FSR Value MCP3008 2 Channel 4 capteur 9: {adc_value_mcp2_ch4}")
        print(f"FSR Value MCP3008 2 Channel 0 capteur 10: {adc_value_mcp2_ch0}")
        print(f"FSR Value MCP3008 2 Channel 1 capteur 11: {adc_value_mcp2_ch1}")
        print(f"FSR Value MCP3008 2 Channel 2 capteur 12: {adc_value_mcp2_ch2}")

        time.sleep(1)

except KeyboardInterrupt:
    spi.close()
    GPIO.cleanup()
    print("Program terminated")

    # Save the DataFrame to a CSV file
    df.to_csv(csv_filename, index=False)
    print(f"Data saved to {csv_filename}")

except Exception as e:
    print(f"An error occurred: {e}")
    spi.close()
    GPIO.cleanup()

    # Save the DataFrame to a CSV file in case of an error
    df.to_csv(csv_filename, index=False)
    print(f"Data saved to {csv_filename}")

