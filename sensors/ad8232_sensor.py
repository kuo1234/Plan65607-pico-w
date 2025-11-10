"""
AD8232 ECG Sensor Class
ECG sensor with lead-off detection.
"""

from machine import ADC, Pin


class AD8232Sensor:
    """AD8232 ECG sensor with lead-off detection."""
    
    def __init__(self, out_pin, lop_pin, lon_pin):
        self.ecg_adc = ADC(Pin(out_pin))
        self.lo_plus = Pin(lop_pin, Pin.IN)
        self.lo_minus = Pin(lon_pin, Pin.IN)
    
    def read(self):
        """Read ECG value and lead-off status."""
        ecg_value = self.ecg_adc.read_u16()
        lo_p = bool(self.lo_plus.value())
        lo_n = bool(self.lo_minus.value())
        lo_any = lo_p or lo_n
        
        return {
            'ecg_value': ecg_value,
            'lead_off_plus': lo_p,
            'lead_off_minus': lo_n,
            'lead_off': lo_any
        }
