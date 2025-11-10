"""
Myoware EMG Sensor Class
EMG sensor with anomaly detection for muscle signal monitoring.
"""

from machine import ADC, Pin


class MyowareSensor:
    """Myoware EMG sensor with anomaly detection."""
    
    VREF = 3.3
    BUF_LEN = 25
    SAT_HIGH_ADC = 64000
    SAT_LOW_ADC = 200
    SAT_HIGH_V = 3.2
    MIN_PTP_ADC = 300
    
    def __init__(self, sig_pin):
        self.myo_adc = ADC(Pin(sig_pin))
        self._myo_buf = []
    
    def _adc_to_volt(self, adc):
        """Convert ADC value to voltage."""
        return (float(adc) / 65535.0) * self.VREF
    
    def _assess_myo_ok(self, adc_val):
        """Check if EMG reading is valid."""
        v = self._adc_to_volt(adc_val)
        
        # 1) Saturation or ground check
        if adc_val >= self.SAT_HIGH_ADC or v >= self.SAT_HIGH_V:
            return False, 'saturated_high'
        if adc_val <= self.SAT_LOW_ADC:
            return False, 'saturated_low'
        
        # 2) Buffer update
        self._myo_buf.append(int(adc_val))
        if len(self._myo_buf) > self.BUF_LEN:
            self._myo_buf.pop(0)
        
        # 3) Flatline check
        if len(self._myo_buf) >= 8:
            ptp = max(self._myo_buf) - min(self._myo_buf)
            if ptp < self.MIN_PTP_ADC:
                return False, 'flatline'
        
        return True, 'ok'
    
    def read(self):
        """Read EMG value with validation."""
        myo = self.myo_adc.read_u16()
        myo_ok, myo_reason = self._assess_myo_ok(myo)
        myo_out = myo if myo_ok else 0
        myo_v = self._adc_to_volt(myo)
        
        return {
            'muscle_value': myo_out,
            'muscle_ok': myo_ok,
            'muscle_voltage': myo_v,
            'muscle_reason': myo_reason
        }
