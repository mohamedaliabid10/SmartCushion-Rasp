import spidev
import time
import RPi.GPIO as GPIO

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

def read_adc(channel, cs_index):
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

def get_temperature(channel, cs_index):
    adc_value = read_adc(channel, cs_index)
    voltage = (adc_value * 3.3) / 1024  # Convert to voltage
    temperature_c = voltage * 100  # Convert voltage to temperature
    return temperature_c

try:
    while True:
        temp_c_mcp1_ch7 = get_temperature(7, 1)  # Read from MCP1 (cs_index 0), Channel 7
        print(f"Temperature from MCP1 Channel 7: {temp_c_mcp1_ch7:.2f} °C")
        time.sleep(1)

except KeyboardInterrupt:
    spi.close()
    GPIO.cleanup()
    print("Program terminated")
