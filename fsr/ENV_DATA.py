import time
import board
import adafruit_sgp40
import adafruit_dht
import json
import paho.mqtt.client as mqtt

# Initialize the I2C bus and the SGP40 sensor
i2c = board.I2C()
sgp = adafruit_sgp40.SGP40(i2c)

# Initialize the DHT device
dhtDevice = adafruit_dht.DHT11(board.D19)

# MQTT broker configuration
mqtt_broker = "192.168.43.79"  #adress ip de rasp
mqtt_port = 1883  # MQTT broker port
mqtt_topic = "/home/smart_cushion/Temp"  # MQTT topic to publish data

# Initialize MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

# Connect callback function
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code "+str(rc))

# Set the on_connect callback
client.on_connect = on_connect

# Connect to MQTT broker
client.connect(mqtt_broker, mqtt_port, 60)

# Main loop
while True:
    try:
        # Read temperature and humidity from the DHT sensor
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity

        if temperature_c is not None and humidity is not None:
            # Get raw VOC values
            raw_voc = sgp.measure_raw()

            # Placeholder for actual normalization/calibration logic
            # Example: Normalize raw VOC value to a range (0-500) for air quality index
            voc_index = (raw_voc / 65535) * 500

            # Prepare data as a JSON payload
            data = {
                "temperature": temperature_c,
                "humidity": humidity,
                "voc_index": voc_index
            }

            # Convert data to JSON format
            payload = json.dumps(data)

            # Publish data to MQTT topic
            client.publish(mqtt_topic, payload)

            # Print the values to the console
            print(
                "Temperature: {:.1f}°C   Humidity: {}%   VOC Index: {:.2f}".format(
                    temperature_c, humidity, voc_index
                )
            )
        else:
            print("Failed to retrieve data from DHT sensor")

    except RuntimeError as error:
        # Handle runtime errors from the DHT sensor
        print("Error reading DHT sensor:", error.args[0])
    except Exception as error:
        # Handle other unexpected errors
        print("Unexpected error:", error)
    finally:
        # Pause for 2 seconds before the next reading
        time.sleep(2)
