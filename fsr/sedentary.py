import spidev
import time
import RPi.GPIO as GPIO
from datetime import datetime
import json
import paho.mqtt.client as mqtt


# MQTT broker configuration
mqtt_broker = "192.168.43.134"
mqtt_port = 1883  # MQTT broker port
mqtt_topic = "/home/smart_cushion/SEDENTARY"  # MQTT topic to publish DHT11 data

# Initialize MQTT client
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

def format_duration(seconds):
    minutes, sec = divmod(seconds, 60)
    return f"{int(minutes):02d}:{int(sec):02d} min"

# Initialize variables
person_available = False
start_time = time.time()
available_duration = 0
unavailable_duration = 0

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

        # Calculate the sum of the FSR readings
        fsr_sum = (adc_value_mcp1_ch0 + adc_value_mcp1_ch1 + adc_value_mcp1_ch2 + adc_value_mcp1_ch3 +
                   adc_value_mcp1_ch4 + adc_value_mcp1_ch5 + adc_value_mcp1_ch6 + adc_value_mcp1_ch7 +
                   adc_value_mcp2_ch0 + adc_value_mcp2_ch1 + adc_value_mcp2_ch2 + adc_value_mcp2_ch3 + 
                   adc_value_mcp2_ch4)

        # Get the current timestamp
        current_time = time.time()
        elapsed_time = current_time - start_time

        # Prepare data as a JSON payload
        data = {
            "fsr_sum": fsr_sum,
            "elapsed_time": elapsed_time
        }

        # Convert data to JSON format
        payload = json.dumps(data)

        # Publish data to MQTT topic
        client.publish(mqtt_topic, payload)

        # Check if the person is available or unavailable
        if fsr_sum > 300:
            if not person_available:
                print(f"Person is now available at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Unavailable duration: {format_duration(unavailable_duration)}")
                person_available = True
                start_time = current_time
            else:
                available_duration = elapsed_time
        else:
            if person_available:
                print(f"Person is now unavailable at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Available duration: {format_duration(available_duration)}")
                person_available = False
                start_time = current_time
            else:
                unavailable_duration = elapsed_time

        time.sleep(1)

except KeyboardInterrupt:
    spi.close()
    GPIO.cleanup()
    print("Program terminated")
except Exception as e:
    print(f"An error occurred: {e}")
    spi.close()
    GPIO.cleanup()
