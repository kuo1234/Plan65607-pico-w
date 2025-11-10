"""
MAX30102 Heart Rate and SpO2 Sensor Class
Integrated heart rate and blood oxygen sensor with HeartRateMonitor.
"""

from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
from .heart_rate_monitor import HeartRateMonitor
from utime import ticks_ms, ticks_diff


class MAX30102Sensor:
    """MAX30102 heart rate and SpO2 sensor with integrated HeartRateMonitor."""
    
    def __init__(self, i2c, sample_rate=400, fifo_average=8):
        self.sensor = MAX30102(i2c=i2c)
        self.sample_rate = sample_rate
        self.fifo_average = fifo_average
        self.actual_acquisition_rate = int(sample_rate / fifo_average)
        
        # Initialize HeartRateMonitor
        self.hr_monitor = HeartRateMonitor(
            sample_rate=self.actual_acquisition_rate,
            window_size=int(self.actual_acquisition_rate * 3),  # 3 seconds window
            smoothing_window=5
        )
        
        # Heart rate calculation timer (calculate every 2 seconds)
        self._last_hr_calc_time = ticks_ms()
        self._hr_calc_interval = 2000  # 2 seconds in ms
        self._current_hr = 0
        self._current_ir = 0
        
        self._setup_sensor()
    
    def _setup_sensor(self):
        """Setup MAX30102 sensor."""
        try:
            # Check if sensor is connected
            if self.sensor.i2c_address not in self.sensor._i2c.scan():
                print('MAX30102 sensor not found.')
                return False
            
            if not self.sensor.check_part_id():
                print('MAX30102 ID not matching.')
                return False
            
            # Configure sensor
            self.sensor.setup_sensor()
            self.sensor.set_sample_rate(self.sample_rate)
            self.sensor.set_fifo_average(self.fifo_average)
            self.sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)
            
            print('MAX30102 sensor initialized successfully.')
            return True
        except Exception as e:
            print(f'MAX30102 setup error: {e}')
            return False
    
    def read(self):
        """Read heart rate, SpO2, and IR values.
        
        This method should be called frequently (e.g., every 100ms) to:
        1. Continuously poll the sensor and add samples to HeartRateMonitor
        2. Periodically calculate heart rate (every 2 seconds)
        """
        spo2 = 0
        
        try:
            # IMPORTANT: Check and process ALL available samples in FIFO
            self.sensor.check()
            
            # Process all available samples (critical for continuous monitoring)
            sample_count = 0
            while self.sensor.available():
                red = self.sensor.pop_red_from_storage()
                ir = self.sensor.pop_ir_from_storage()
                
                # Store latest IR value for output
                self._current_ir = ir
                
                # Add IR sample to heart rate monitor (continuous feeding)
                self.hr_monitor.add_sample(ir)
                sample_count += 1
            
            # Calculate heart rate periodically (every 2 seconds)
            current_time = ticks_ms()
            if ticks_diff(current_time, self._last_hr_calc_time) >= self._hr_calc_interval:
                calculated_hr = self.hr_monitor.calculate_heart_rate()
                
                # Debug output
                samples_count = len(self.hr_monitor.samples)
                print(f"[MAX30102] Samples: {samples_count}, Calculated HR: {calculated_hr}, Current HR: {self._current_hr}, IR: {self._current_ir}")
                
                if calculated_hr is not None:
                    hr = int(calculated_hr)
                    # Validate heart rate range
                    if 20 <= hr <= 240:
                        self._current_hr = hr
                        print(f"  ✓ Valid HR updated: {hr} BPM")
                    else:
                        print(f"  ✗ Invalid HR (out of range): {hr}")
                        # Keep previous value if out of range
                        pass
                else:
                    print(f"  ✗ HR calculation returned None (need more samples)")
                
                # Update calculation time
                self._last_hr_calc_time = current_time
            
            # Simple SpO2 estimation (placeholder - needs proper algorithm)
            if self._current_hr > 0 and self._current_ir > 0:
                spo2 = 98  # Placeholder value
            else:
                spo2 = 0
                
        except Exception as e:
            # Log error for debugging
            print(f"MAX30102 read error: {e}")
            pass
        
        return {
            'hr_value': self._current_hr,
            'spo2_value': spo2,
            'ir_value': self._current_ir
        }
