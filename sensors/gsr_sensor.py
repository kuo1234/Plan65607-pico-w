"""
GSR Sensor Class
Grove GSR sensor for measuring galvanic skin response.
"""

from machine import ADC, Pin


class GSRSensor:
    """Grove GSR sensor."""
    
    def __init__(self, sig_pin):
        self.gsr_adc = ADC(Pin(sig_pin))
    
    def read(self):
        """Read GSR value."""
        return {'gsr_value': self.gsr_adc.read_u16()}
