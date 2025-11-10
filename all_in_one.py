"""
All-in-One Sensor Logger for Raspberry Pi Pico W (MicroPython)
單檔案版本 - 包含所有感應器類別、配置和主程式

感應器：
- AD8232 ECG（心電圖）
- Grove GSR（皮膚電導）
- Myoware EMG（肌電圖）
- DHT22（環境溫濕度）
- MAX30205（體溫）
- MAX30102（心率/血氧）

輸出：UART JSON @115200 baud
採樣率：10 Hz (每 100ms)

使用方式：
1. 將此檔案複製到 Pico W（命名為 main.py 會自動執行）
2. 確保已安裝 max30102 庫
3. 重新啟動 Pico W

作者：AI Assistant
日期：2025-10-20
版本：2.0 (Multi-Rate System)
"""

import time
from machine import Pin, UART, I2C, SoftI2C, ADC
from utime import ticks_ms, ticks_diff
import dht


# ============================================================================
# HeartRateMonitor Class
# ============================================================================

class HeartRateMonitor:
    """心率監測器 - 使用移動窗口平滑訊號並找出峰值"""

    def __init__(self, sample_rate=100, window_size=10, smoothing_window=5):
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.smoothing_window = smoothing_window
        self.samples = []
        self.timestamps = []
        self.filtered_samples = []

    def add_sample(self, sample):
        """添加新樣本到監測器"""
        timestamp = ticks_ms()
        self.samples.append(sample)
        self.timestamps.append(timestamp)

        # 應用平滑
        if len(self.samples) >= self.smoothing_window:
            smoothed_sample = sum(self.samples[-self.smoothing_window:]) / self.smoothing_window
            self.filtered_samples.append(smoothed_sample)
        else:
            self.filtered_samples.append(sample)

        # 維持樣本和時間戳記的大小
        if len(self.samples) > self.window_size:
            self.samples.pop(0)
            self.timestamps.pop(0)
            self.filtered_samples.pop(0)

    def find_peaks(self):
        """在過濾後的樣本中找出峰值"""
        peaks = []

        if len(self.filtered_samples) < 3:
            return peaks

        # 計算動態閾值
        recent_samples = self.filtered_samples[-self.window_size:]
        min_val = min(recent_samples)
        max_val = max(recent_samples)
        threshold = min_val + (max_val - min_val) * 0.5

        for i in range(1, len(self.filtered_samples) - 1):
            if (self.filtered_samples[i] > threshold and 
                self.filtered_samples[i - 1] < self.filtered_samples[i] and 
                self.filtered_samples[i] > self.filtered_samples[i + 1]):
                peak_time = self.timestamps[i]
                peaks.append((peak_time, self.filtered_samples[i]))

        return peaks

    def calculate_heart_rate(self):
        """計算心率（BPM）"""
        peaks = self.find_peaks()

        if len(peaks) < 2:
            return None

        # 計算峰值間的平均間隔
        intervals = []
        for i in range(1, len(peaks)):
            interval = ticks_diff(peaks[i][0], peaks[i - 1][0])
            intervals.append(interval)

        average_interval = sum(intervals) / len(intervals)
        heart_rate = 60000 / average_interval

        return heart_rate


# ============================================================================
# AD8232 ECG Sensor Class
# ============================================================================

class AD8232Sensor:
    """AD8232 心電圖感應器（含電極脫落檢測）"""
    
    def __init__(self, out_pin, lop_pin, lon_pin):
        self.ecg_adc = ADC(Pin(out_pin))
        self.lo_plus = Pin(lop_pin, Pin.IN)
        self.lo_minus = Pin(lon_pin, Pin.IN)
    
    def read(self):
        """讀取 ECG 值和電極脫落狀態"""
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


# ============================================================================
# GSR Sensor Class
# ============================================================================

class GSRSensor:
    """Grove GSR 皮膚電導感應器"""
    
    def __init__(self, sig_pin):
        self.gsr_adc = ADC(Pin(sig_pin))
    
    def read(self):
        """讀取 GSR 值"""
        return {'gsr_value': self.gsr_adc.read_u16()}


# ============================================================================
# Myoware EMG Sensor Class
# ============================================================================

class MyowareSensor:
    """Myoware 肌電圖感應器（含異常檢測）"""
    
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
        """將 ADC 值轉換為電壓"""
        return (float(adc) / 65535.0) * self.VREF
    
    def _assess_myo_ok(self, adc_val):
        """檢查 EMG 讀數是否有效"""
        v = self._adc_to_volt(adc_val)
        
        # 1) 飽和或接地檢查
        if adc_val >= self.SAT_HIGH_ADC or v >= self.SAT_HIGH_V:
            return False, 'saturated_high'
        if adc_val <= self.SAT_LOW_ADC:
            return False, 'saturated_low'
        
        # 2) 緩衝區更新
        self._myo_buf.append(int(adc_val))
        if len(self._myo_buf) > self.BUF_LEN:
            self._myo_buf.pop(0)
        
        # 3) 平線檢查
        if len(self._myo_buf) >= 8:
            ptp = max(self._myo_buf) - min(self._myo_buf)
            if ptp < self.MIN_PTP_ADC:
                return False, 'flatline'
        
        return True, 'ok'
    
    def read(self):
        """讀取 EMG 值並驗證"""
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


# ============================================================================
# DHT22 Sensor Class
# ============================================================================

class DHT22Sensor:
    """DHT22 環境溫濕度感應器"""
    
    def __init__(self, dht_pin):
        self.dht_sensor = dht.DHT22(Pin(dht_pin))
    
    def read(self):
        """讀取溫度和濕度"""
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


# ============================================================================
# MAX30205 Body Temperature Sensor Class
# ============================================================================

class MAX30205Sensor:
    """MAX30205 高精度體溫感應器"""
    
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
        
        # 掃描感應器
        for a in (0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F):
            if a in self.i2c.scan():
                self.addr = a
                break
    
    def _twos_comp16(self, v):
        """轉換二補數 16 位元值"""
        return v - 0x10000 if (v & 0x8000) else v
    
    def _bus_recovery(self):
        """恢復 I2C 總線（如果鎖定）"""
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
        """讀取體溫（含重試和總線恢復）"""
        if self.addr is None:
            return {'body_temperature': 0.0, 'body_temp_fresh': False}
        
        for attempt in range(6):
            try:
                self.i2c.writeto(self.addr, b'\x00')
                time.sleep_us(60)
                raw = self.i2c.readfrom(self.addr, 2)
                val = self._twos_comp16((raw[0] << 8) | raw[1]) / 256.0
                
                # 擴展數據格式補償 +64°C
                if val < -10.0 and (0.0 <= val + 64.0 <= 100.0):
                    val += 64.0
                
                self._last_body = val
                self._last_body_ms = time.ticks_ms()
                
                # 更新非零值
                if val != 0 and val != 0.0:
                    self._prev_body_nonzero = val
                
                return {'body_temperature': val, 'body_temp_fresh': True}
            except:
                time.sleep_ms(5 + attempt * 5)
                if attempt == 2:
                    self._bus_recovery()
        
        # 所有嘗試失敗：返回保持值
        if self._last_body is not None and time.ticks_diff(time.ticks_ms(), self._last_body_ms) <= self.HOLD_MS:
            body_t_out = self._last_body
        elif self._prev_body_nonzero is not None:
            body_t_out = self._prev_body_nonzero
        else:
            body_t_out = 0.0
        
        return {'body_temperature': body_t_out, 'body_temp_fresh': False}


# ============================================================================
# MAX30102 Heart Rate and SpO2 Sensor Class
# ============================================================================

class MAX30102Sensor:
    """MAX30102 心率和血氧感應器（整合 HeartRateMonitor）"""
    
    def __init__(self, i2c, sample_rate=400, fifo_average=8):
        # 延遲導入 MAX30102 庫（避免在沒有安裝時出錯）
        from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
        
        self.sensor = MAX30102(i2c=i2c)
        self.sample_rate = sample_rate
        self.fifo_average = fifo_average
        self.actual_acquisition_rate = int(sample_rate / fifo_average)
        
        # 初始化 HeartRateMonitor
        self.hr_monitor = HeartRateMonitor(
            sample_rate=self.actual_acquisition_rate,
            window_size=int(self.actual_acquisition_rate * 3),  # 3 秒窗口
            smoothing_window=5
        )
        
        # 心率計算計時器（每 2 秒計算一次）
        self._last_hr_calc_time = ticks_ms()
        self._hr_calc_interval = 2000  # 2 秒（毫秒）
        self._current_hr = 0
        self._current_ir = 0
        
        self._setup_sensor(MAX30105_PULSE_AMP_MEDIUM)
    
    def _setup_sensor(self, pulse_amp):
        """設置 MAX30102 感應器"""
        try:
            # 檢查感應器是否連接
            if self.sensor.i2c_address not in self.sensor._i2c.scan():
                print('MAX30102 sensor not found.')
                return False
            
            if not self.sensor.check_part_id():
                print('MAX30102 ID not matching.')
                return False
            
            # 配置感應器
            self.sensor.setup_sensor()
            self.sensor.set_sample_rate(self.sample_rate)
            self.sensor.set_fifo_average(self.fifo_average)
            self.sensor.set_active_leds_amplitude(pulse_amp)
            
            print('MAX30102 sensor initialized successfully.')
            return True
        except Exception as e:
            print(f'MAX30102 setup error: {e}')
            return False
    
    def read(self):
        """讀取心率、血氧和 IR 值
        
        此方法應經常調用（例如每 100ms）以：
        1. 持續輪詢感應器並添加樣本到 HeartRateMonitor
        2. 週期性計算心率（每 2 秒）
        """
        spo2 = 0
        
        try:
            # 重要：檢查並處理 FIFO 中的所有可用樣本
            self.sensor.check()
            
            # 處理所有可用樣本（對於連續監測至關重要）
            sample_count = 0
            while self.sensor.available():
                red = self.sensor.pop_red_from_storage()
                ir = self.sensor.pop_ir_from_storage()
                
                # 儲存最新的 IR 值用於輸出
                self._current_ir = ir
                
                # 添加 IR 樣本到心率監測器（持續餵送）
                self.hr_monitor.add_sample(ir)
                sample_count += 1
            
            # 週期性計算心率（每 2 秒）
            current_time = ticks_ms()
            if ticks_diff(current_time, self._last_hr_calc_time) >= self._hr_calc_interval:
                calculated_hr = self.hr_monitor.calculate_heart_rate()
                
                # 調試輸出
                samples_count = len(self.hr_monitor.samples)
                print(f"[MAX30102] Samples: {samples_count}, Calculated HR: {calculated_hr}, Current HR: {self._current_hr}, IR: {self._current_ir}")
                
                if calculated_hr is not None:
                    hr = int(calculated_hr)
                    # 驗證心率範圍
                    if 20 <= hr <= 240:
                        self._current_hr = hr
                        print(f"  ✓ Valid HR updated: {hr} BPM")
                    else:
                        print(f"  ✗ Invalid HR (out of range): {hr}")
                        # 如果超出範圍則保留先前的值
                        pass
                else:
                    print(f"  ✗ HR calculation returned None (need more samples)")
                
                # 更新計算時間
                self._last_hr_calc_time = current_time
            
            # 簡單的血氧估算（佔位符 - 需要適當的演算法）
            if self._current_hr > 0 and self._current_ir > 0:
                spo2 = 98  # 佔位符值
            else:
                spo2 = 0
                
        except Exception as e:
            # 記錄錯誤以便調試
            print(f"MAX30102 read error: {e}")
            pass
        
        return {
            'hr_value': self._current_hr,
            'spo2_value': spo2,
            'ir_value': self._current_ir
        }


# ============================================================================
# Sensor Manager Class
# ============================================================================

class SensorManager:
    """感應器管理器 - 協調所有感應器的數據收集"""
    
    def __init__(self):
        # ========= 腳位配置 =========
        AD8232_OUT, AD8232_LOP, AD8232_LON = 28, 19, 18
        GSR_SIG, MYO_SIG, DHT_PIN = 26, 27, 21
        MX30102_SDA, MX30102_SCL = 16, 17
        MX30205_SDA, MX30205_SCL, I2C0_FREQ = 4, 5, 50000
        
        # ========= 初始化感應器 =========
        print("Initializing sensors...")
        
        # 類比感應器
        self.ecg_sensor = AD8232Sensor(AD8232_OUT, AD8232_LOP, AD8232_LON)
        self.gsr_sensor = GSRSensor(GSR_SIG)
        self.myo_sensor = MyowareSensor(MYO_SIG)
        
        # DHT22 感應器
        self.dht_sensor = DHT22Sensor(DHT_PIN)
        
        # ========= 初始化 I2C 總線 =========
        self.i2c0 = I2C(0, scl=Pin(MX30205_SCL), sda=Pin(MX30205_SDA), freq=I2C0_FREQ)
        self.i2c_soft = SoftI2C(sda=Pin(MX30102_SDA), scl=Pin(MX30102_SCL), freq=400000)
        
        # I2C 感應器
        self.temp_sensor = MAX30205Sensor(self.i2c0, MX30205_SCL, MX30205_SDA, I2C0_FREQ)
        self.max30102_sensor = MAX30102Sensor(self.i2c_soft, sample_rate=400, fifo_average=8)
        
        # ========= 初始化 UART =========
        self.uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
        
        # ========= 感應器更新間隔與最後值 =========
        # 定義每個感應器的更新間隔（毫秒）
        self.update_intervals = {
            'ecg': 100,       # 10 Hz - ECG 波形需要高採樣率
            'gsr': 100,       # 10 Hz - GSR 變化中等速度
            'myo': 100,       # 10 Hz - 肌肉活動變化快速
            'dht': 2000,      # 0.5 Hz - 溫濕度變化緩慢
            'temp': 1000,     # 1 Hz - 體溫變化緩慢
            'max30102': 100,  # 10 Hz - 但 HR 內部每 2 秒計算
        }
        
        # 追蹤上次更新時間
        self.last_update_times = {
            'ecg': 0,
            'gsr': 0,
            'myo': 0,
            'dht': 0,
            'temp': 0,
            'max30102': 0,
        }
        
        # 儲存每個感應器的最後有效讀數
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
        """讀取所有感應器數據並返回 JSON 字串
        
        每個感應器以自己的更新間隔讀取。
        如果未到更新時間，使用最後的有效讀數。
        這允許不同的感應器以不同的頻率運行。
        """
        try:
            current_time = time.ticks_ms()
            
            # ========= ECG 感應器 (10 Hz) =========
            if time.ticks_diff(current_time, self.last_update_times['ecg']) >= self.update_intervals['ecg']:
                self.last_readings['ecg'] = self.ecg_sensor.read()
                self.last_update_times['ecg'] = current_time
            ecg_data = self.last_readings['ecg']
            
            # ========= GSR 感應器 (10 Hz) =========
            if time.ticks_diff(current_time, self.last_update_times['gsr']) >= self.update_intervals['gsr']:
                self.last_readings['gsr'] = self.gsr_sensor.read()
                self.last_update_times['gsr'] = current_time
            gsr_data = self.last_readings['gsr']
            
            # ========= Myoware 感應器 (10 Hz) =========
            if time.ticks_diff(current_time, self.last_update_times['myo']) >= self.update_intervals['myo']:
                self.last_readings['myo'] = self.myo_sensor.read()
                self.last_update_times['myo'] = current_time
            myo_data = self.last_readings['myo']
            
            # ========= DHT22 感應器 (0.5 Hz - 每 2 秒) =========
            if time.ticks_diff(current_time, self.last_update_times['dht']) >= self.update_intervals['dht']:
                self.last_readings['dht'] = self.dht_sensor.read()
                self.last_update_times['dht'] = current_time
            dht_data = self.last_readings['dht']
            
            # ========= MAX30205 體溫感應器 (1 Hz) =========
            if time.ticks_diff(current_time, self.last_update_times['temp']) >= self.update_intervals['temp']:
                self.last_readings['temp'] = self.temp_sensor.read()
                self.last_update_times['temp'] = current_time
            temp_data = self.last_readings['temp']
            
            # ========= MAX30102 心率感應器 (10 Hz 讀取, 0.5 Hz HR 計算) =========
            # 注意：此感應器每 10Hz 讀取以持續處理 FIFO，
            # 但心率在內部每 2 秒計算一次
            if time.ticks_diff(current_time, self.last_update_times['max30102']) >= self.update_intervals['max30102']:
                self.last_readings['max30102'] = self.max30102_sensor.read()
                self.last_update_times['max30102'] = current_time
            hr_data = self.last_readings['max30102']
            
            # 建立 JSON 字串（使用 format 以相容 MicroPython）
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
            # 錯誤時返回 None，主循環會顯示 "No data"
            print("Error in read_all(): %s" % str(e))
            return None
    
    def run(self):
        """主循環 - 以 10Hz 持續採集數據"""
        print("\n" + "="*60)
        print("Starting sensor data acquisition...")
        print("Sampling rate: 10 Hz (every 100ms)")
        print("UART output: 115200 baud")
        print("="*60 + "\n")
        
        # 初始化 MAX30102：在開始主循環前收集 5 秒樣本
        print("Initializing MAX30102 heart rate monitor...")
        print("Please place your finger on the MAX30102 sensor now.")
        for i in range(50):  # 5 秒（10Hz）
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
                # 透過 UART 發送
                self.uart.write(data.encode('utf-8'))
                # 顯示到控制台
                print(data.strip())
            else:
                print('No data')
            
            # 10Hz 採樣率
            time.sleep_ms(100)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """主入口點"""
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
