"""
MAX30205 Body Temperature Sensor Class
High-precision body temperature sensor with I2C interface.
"""

import time
from machine import Pin, I2C


class MAX30205Sensor:
    """MAX30205 body temperature sensor."""
    
    HOLD_MS = 1500
    
    def __init__(self, i2c, scl_pin, sda_pin, freq=50000):
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self.freq = freq
        self.i2c = i2c
        self.addr = None
        self._prev_body_nonzero = None
        self._last_body = None
        self._last_body_ms = 0
        
        # Scan for sensor
        for a in (0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F):
            if a in self.i2c.scan():
                self.addr = a
                break
    
    def _twos_comp16(self, v):
        """Convert two's complement 16-bit value."""
        return v - 0x10000 if (v & 0x8000) else v
    
    def _bus_recovery(self):
        """Recover I2C bus if locked."""
        try:
            scl = Pin(self.scl_pin, Pin.OUT, value=1)
            sda = Pin(self.sda_pin, Pin.OUT, value=1)
            time.sleep_us(50)
            for _ in range(9):
                scl.value(0)
                time.sleep_us(6)
                scl.value(1)
                time.sleep_us(6)
            sda.value(0)
            time.sleep_us(6)
            scl.value(1)
            time.sleep_us(6)
            sda.value(1)
            time.sleep_us(6)
        except:
            pass
        self.i2c = I2C(0, scl=Pin(self.scl_pin), sda=Pin(self.sda_pin), freq=self.freq)
    
    def read(self):
        """Read body temperature with retry and bus recovery."""
        if self.addr is None:
            return {'body_temperature': 0.0, 'body_temp_fresh': False}
        
        for attempt in range(6):
            try:
                self.i2c.writeto(self.addr, b'\x00')
                time.sleep_us(60)
                raw = self.i2c.readfrom(self.addr, 2)
                val = self._twos_comp16((raw[0] << 8) | raw[1]) / 256.0
                
                # Extended Data Format compensation +64°C
                if val < -10.0 and (0.0 <= val + 64.0 <= 100.0):
                    val += 64.0
                
                self._last_body = val
                self._last_body_ms = time.ticks_ms()
                
                # Update non-zero value
                if val != 0 and val != 0.0:
                    self._prev_body_nonzero = val
                
                return {'body_temperature': val, 'body_temp_fresh': True}
            except:
                time.sleep_ms(5 + attempt * 5)
                if attempt == 2:
                    self._bus_recovery()
        
        # All attempts failed: return held value
        if self._last_body is not None and time.ticks_diff(time.ticks_ms(), self._last_body_ms) <= self.HOLD_MS:
            body_t_out = self._last_body
        elif self._prev_body_nonzero is not None:
            body_t_out = self._prev_body_nonzero
        else:
            body_t_out = 0.0
        
        return {'body_temperature': body_t_out, 'body_temp_fresh': False}
