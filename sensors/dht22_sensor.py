"""
DHT22 Sensor Class
Temperature and humidity sensor.
"""

from machine import Pin
import dht


class DHT22Sensor:
    """DHT22 temperature and humidity sensor."""
    
    def __init__(self, dht_pin):
        self.dht_sensor = dht.DHT22(Pin(dht_pin))
    
    def read(self):
        """Read temperature and humidity."""
        try:
            self.dht_sensor.measure()
            env_t = self.dht_sensor.temperature()
            env_h = self.dht_sensor.humidity()
            return {
                'env_temperature': env_t if env_t is not None else 0.0,
                'env_humidity': env_h if env_h is not None else 0.0
            }
        except:
            return {
                'env_temperature': 0.0,
                'env_humidity': 0.0
            }
