# All-in-One Sensor Logger for Pico W (MicroPython)
# AD8232 ECG + Grove GSR + Myoware + DHT22 + MAX30102 + MAX30205
# UART JSON @115200
# Modular Architecture - Each sensor is a separate class

import time
from machine import Pin, UART, I2C, SoftI2C

# Import all sensor classes from the sensors package
from sensors import (
    AD8232Sensor,
    GSRSensor,
    MyowareSensor,
    DHT22Sensor,
    MAX30205Sensor,
    MAX30102Sensor
)


class SensorManager:
    """Manages all sensors and coordinates data collection."""
    
    def __init__(self):
        # ========= Pin Configurations =========
        AD8232_OUT, AD8232_LOP, AD8232_LON = 28, 19, 18
        GSR_SIG, MYO_SIG, DHT_PIN = 26, 27, 21
        MX30102_SDA, MX30102_SCL = 16, 17
        MX30205_SDA, MX30205_SCL, I2C0_FREQ = 4, 5, 50000
        
        # ========= Initialize Sensors =========
        print("Initializing sensors...")
        
        # Analog sensors
        self.ecg_sensor = AD8232Sensor(AD8232_OUT, AD8232_LOP, AD8232_LON)
        self.gsr_sensor = GSRSensor(GSR_SIG)
        self.myo_sensor = MyowareSensor(MYO_SIG)
        
        # DHT22 sensor
        self.dht_sensor = DHT22Sensor(DHT_PIN)
        
        # ========= Initialize I2C Buses =========
        self.i2c0 = I2C(0, scl=Pin(MX30205_SCL), sda=Pin(MX30205_SDA), freq=I2C0_FREQ)
        self.i2c_soft = SoftI2C(sda=Pin(MX30102_SDA), scl=Pin(MX30102_SCL), freq=400000)
        
        # I2C sensors
        self.temp_sensor = MAX30205Sensor(self.i2c0, MX30205_SCL, MX30205_SDA, I2C0_FREQ)
        self.max30102_sensor = MAX30102Sensor(self.i2c_soft, sample_rate=400, fifo_average=8)
        
        # ========= Initialize UART =========
        self.uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
        
        # ========= Sensor Update Intervals & Last Values =========
        # Define update intervals in milliseconds for each sensor
        self.update_intervals = {
            'ecg': 100,       # 10 Hz - high frequency for ECG waveform
            'gsr': 100,       # 10 Hz - GSR changes moderately fast
            'myo': 100,       # 10 Hz - muscle activity changes fast
            'dht': 2000,      # 0.5 Hz - temp/humidity change slowly
            'temp': 1000,     # 1 Hz - body temperature changes slowly
            'max30102': 100,  # 10 Hz - but HR calculates every 2s internally
        }
        
        # Track last update times
        self.last_update_times = {
            'ecg': 0,
            'gsr': 0,
            'myo': 0,
            'dht': 0,
            'temp': 0,
            'max30102': 0,
        }
        
        # Store last valid readings for each sensor
        self.last_readings = {
            'ecg': {'ecg_value': 0, 'lead_off_plus': False, 'lead_off_minus': False, 'lead_off': False},
            'gsr': {'gsr_value': 0},
            'myo': {'muscle_value': 0, 'muscle_ok': True, 'muscle_voltage': 0.0, 'muscle_reason': 'Normal'},
            'dht': {'env_temperature': 0.0, 'env_humidity': 0.0},
            'temp': {'body_temperature': 0.0, 'body_temp_fresh': True},
            'max30102': {'hr_value': 0, 'spo2_value': 98, 'ir_value': 0},
        }
        
        print("All sensors initialized successfully!")
    
    def read_all(self):
        """Read all sensor data and return as JSON string.
        
        Each sensor is read at its own update interval.
        If not time to update, the last valid reading is used.
        This allows different sensors to run at different frequencies.
        """
        try:
            current_time = time.ticks_ms()
            
            # ========= ECG Sensor (10 Hz) =========
            if time.ticks_diff(current_time, self.last_update_times['ecg']) >= self.update_intervals['ecg']:
                self.last_readings['ecg'] = self.ecg_sensor.read()
                self.last_update_times['ecg'] = current_time
            ecg_data = self.last_readings['ecg']
            
            # ========= GSR Sensor (10 Hz) =========
            if time.ticks_diff(current_time, self.last_update_times['gsr']) >= self.update_intervals['gsr']:
                self.last_readings['gsr'] = self.gsr_sensor.read()
                self.last_update_times['gsr'] = current_time
            gsr_data = self.last_readings['gsr']
            
            # ========= Myoware Sensor (10 Hz) =========
            if time.ticks_diff(current_time, self.last_update_times['myo']) >= self.update_intervals['myo']:
                self.last_readings['myo'] = self.myo_sensor.read()
                self.last_update_times['myo'] = current_time
            myo_data = self.last_readings['myo']
            
            # ========= DHT22 Sensor (0.5 Hz - every 2 seconds) =========
            if time.ticks_diff(current_time, self.last_update_times['dht']) >= self.update_intervals['dht']:
                self.last_readings['dht'] = self.dht_sensor.read()
                self.last_update_times['dht'] = current_time
            dht_data = self.last_readings['dht']
            
            # ========= MAX30205 Temperature Sensor (1 Hz) =========
            if time.ticks_diff(current_time, self.last_update_times['temp']) >= self.update_intervals['temp']:
                self.last_readings['temp'] = self.temp_sensor.read()
                self.last_update_times['temp'] = current_time
            temp_data = self.last_readings['temp']
            
            # ========= MAX30102 Heart Rate Sensor (10 Hz read, 0.5 Hz HR calc) =========
            # Note: This sensor is read at 10Hz to process FIFO continuously,
            # but heart rate is calculated internally every 2 seconds
            if time.ticks_diff(current_time, self.last_update_times['max30102']) >= self.update_intervals['max30102']:
                self.last_readings['max30102'] = self.max30102_sensor.read()
                self.last_update_times['max30102'] = current_time
            hr_data = self.last_readings['max30102']
            
            # Build JSON string (using format for MicroPython compatibility)
            json_data = (
                '{"ecg_value": %d, "gsr_value": %d, '
                '"muscle_value": %d, "muscle_ok": %s, "muscle_voltage": %.3f, "muscle_reason": "%s", '
                '"env_temperature": %.2f, "env_humidity": %.2f, '
                '"body_temperature": %.2f, "body_temp_fresh": %s, '
                '"hr_value": %d, "spo2_value": %d, "ir_value": %d, '
                '"lead_off_plus": %s, "lead_off_minus": %s, "lead_off": %s}\n'
            ) % (
                ecg_data['ecg_value'],
                gsr_data['gsr_value'],
                myo_data['muscle_value'],
                str(myo_data['muscle_ok']).lower(),
                myo_data['muscle_voltage'],
                myo_data['muscle_reason'],
                dht_data['env_temperature'],
                dht_data['env_humidity'],
                temp_data['body_temperature'],
                str(temp_data['body_temp_fresh']).lower(),
                hr_data['hr_value'],
                hr_data['spo2_value'],
                hr_data['ir_value'],
                str(ecg_data['lead_off_plus']).lower(),
                str(ecg_data['lead_off_minus']).lower(),
                str(ecg_data['lead_off']).lower()
            )
            
            return json_data
            
        except Exception as e:
            # Return None on error, will print "No data" in main loop
            print("Error in read_all(): %s" % str(e))
            return None
    
    def run(self):
        """Main loop for continuous data acquisition at 10Hz."""
        print("\n" + "="*60)
        print("Starting sensor data acquisition...")
        print("Sampling rate: 10 Hz (every 100ms)")
        print("UART output: 115200 baud")
        print("="*60 + "\n")
        
        # Initialize MAX30102: collect samples for 5 seconds before starting main loop
        print("Initializing MAX30102 heart rate monitor...")
        print("Please place your finger on the MAX30102 sensor now.")
        for i in range(50):  # 5 seconds at 10Hz
            self.read_all()
            if i % 10 == 0:
                print(f"  Collecting samples... {i//10 + 1}/5 seconds")
            time.sleep_ms(100)
        
        print("Initialization complete! Starting main loop...")
        print("Press Ctrl+C to stop.")
        print("="*60 + "\n")
        
        while True:
            data = self.read_all()
            if data:
                # Send via UART
                self.uart.write(data.encode('utf-8'))
                # Print to console
                print(data.strip())
            else:
                print('No data')
            
            # 10Hz sampling rate
            time.sleep_ms(100)


def main():
    """Main entry point."""
    try:
        sensor_manager = SensorManager()
        sensor_manager.run()
    except KeyboardInterrupt:
        print("\n\nStopped by user (Ctrl+C)")
    except Exception as e:
        print("\n\nError: %s" % str(e))
        raise


if __name__ == '__main__':
    main()
