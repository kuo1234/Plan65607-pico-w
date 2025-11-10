"""
Configuration file for sensor pins and settings.
Modify these values according to your hardware setup.
"""

# ========= Pin Configurations =========

# AD8232 ECG Sensor
AD8232_OUT = 28  # ECG output pin
AD8232_LOP = 19  # Lead-off plus detection
AD8232_LON = 18  # Lead-off minus detection

# Analog Sensors
GSR_SIG = 26  # GSR signal pin
MYO_SIG = 27  # Myoware EMG signal pin

# DHT22 Temperature/Humidity Sensor
DHT_PIN = 21

# MAX30102 (Heart Rate/SpO2) - SoftI2C
MX30102_SDA = 16
MX30102_SCL = 17

# MAX30205 (Body Temperature) - I2C0
MX30205_SDA = 4
MX30205_SCL = 5
I2C0_FREQ = 50000  # 50kHz for stability

# UART Configuration
UART_TX = 0
UART_RX = 1
UART_BAUDRATE = 115200

# ========= Sensor Settings =========

# MAX30102 Settings
MAX30102_SAMPLE_RATE = 400  # Samples per second
MAX30102_FIFO_AVERAGE = 8   # Averaging factor
# Actual acquisition rate = SAMPLE_RATE / FIFO_AVERAGE = 50 Hz

# Main Loop Settings
SAMPLING_INTERVAL_MS = 100  # 100ms = 10Hz sampling rate

# HeartRateMonitor Settings
HR_WINDOW_SECONDS = 3       # Window size in seconds
HR_SMOOTHING_WINDOW = 5     # Smoothing window size

# Heart Rate Validation Range
HR_MIN_BPM = 20
HR_MAX_BPM = 240
