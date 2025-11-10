# 專案檔案索引
# Project File Index

## 📁 檔案結構總覽

```
c:\Users\kuoth\Desktop\pi\
│
├── 🚀 單檔案版本（推薦用於快速部署）
│   ├── all_in_one.py              # ⭐ 完整單檔案版本（所有 sensors + main）
│   ├── ALL_IN_ONE_GUIDE.md        # 📖 單檔案版本使用指南
│   └── deploy.ps1                 # 🔧 快速部署腳本（PowerShell）
│
├── 📦 模組化版本（推薦用於開發）
│   ├── main.py                    # 主程式（多頻率系統）
│   ├── config.py                  # 配置檔案（腳位定義）
│   ├── test_sensors.py            # 感應器測試工具
│   ├── test_max30102_hr.py        # MAX30102 心率專用測試
│   └── sensors/                   # 感應器套件資料夾
│       ├── __init__.py            # 套件初始化
│       ├── heart_rate_monitor.py  # 心率監測演算法
│       ├── ad8232_sensor.py       # ECG 感應器
│       ├── gsr_sensor.py          # GSR 感應器
│       ├── myoware_sensor.py      # EMG 感應器
│       ├── dht22_sensor.py        # 溫濕度感應器
│       ├── max30205_sensor.py     # 體溫感應器
│       └── max30102_sensor.py     # 心率/血氧感應器
│
├── 📚 文件檔案
│   ├── README.md                  # 專案總覽
│   ├── QUICK_REFERENCE.md         # 快速參考指南
│   ├── PROJECT_STRUCTURE.md       # 專案結構說明
│   ├── SUMMARY.md                 # 專案摘要
│   ├── COMPARISON.md              # 新舊版本比較
│   ├── INTEGRATION_COMPLETE.md    # 整合完成報告
│   ├── MULTI_RATE_SYSTEM.md       # 多頻率系統說明
│   └── DEBUG_FRONTEND.md          # 前端調試指南
│
├── 🧪 調試和輔助檔案
│   ├── frontend_debug_helper.js   # 前端調試輔助程式
│   └── hr.py                      # 舊版檔案（保留參考）
│
└── 📦 外部依賴（需另外安裝）
    └── max30102/                  # MAX30102 驅動庫
        ├── __init__.py
        └── circular_buffer.py
```

---

## 🎯 使用場景對應

### 場景 1：我想快速部署到 Pico W

**使用檔案：**
```
all_in_one.py          ← 複製這個到 Pico W（命名為 main.py）
ALL_IN_ONE_GUIDE.md    ← 閱讀使用指南
deploy.ps1             ← 執行自動部署腳本
```

**步驟：**
1. 修改 `deploy.ps1` 中的 COM 埠
2. 執行 `.\deploy.ps1`
3. 重新啟動 Pico W

---

### 場景 2：我想開發和測試個別感應器

**使用檔案：**
```
sensors/               ← 所有感應器類別
test_sensors.py        ← 測試工具
test_max30102_hr.py    ← MAX30102 專用測試
config.py              ← 腳位配置
```

**步驟：**
1. 在 Thonny 中打開 `test_sensors.py`
2. 選擇要測試的感應器函數
3. 執行測試

---

### 場景 3：我想運行完整的多感應器系統

**使用檔案：**
```
main.py                ← 主程式（多頻率系統）
sensors/               ← 所有感應器類別（資料夾）
config.py              ← 配置檔案
max30102/              ← MAX30102 庫（需安裝）
```

**步驟：**
1. 將 `main.py` 和 `sensors/` 資料夾上傳到 Pico W
2. 確保 `max30102` 庫已安裝
3. 在 Pico W 上執行 `import main; main.main()`

---

### 場景 4：我想了解專案架構和設計

**閱讀文件：**
```
README.md                  ← 從這裡開始
PROJECT_STRUCTURE.md       ← 了解專案結構
MULTI_RATE_SYSTEM.md       ← 多頻率系統原理
COMPARISON.md              ← 新舊版本對比
```

---

### 場景 5：我的心率無法顯示

**調試資源：**
```
test_max30102_hr.py        ← 單獨測試 MAX30102
DEBUG_FRONTEND.md          ← 前端調試指南
frontend_debug_helper.js   ← 前端調試程式
```

**步驟：**
1. 先用 `test_max30102_hr.py` 確認硬體正常
2. 檢查 `DEBUG_FRONTEND.md` 中的診斷步驟
3. 在前端加入 `frontend_debug_helper.js` 的調試代碼

---

## 📋 各檔案詳細說明

### 核心程式檔案

#### `all_in_one.py` ⭐ 最常用
- **用途：** 單檔案完整版本，包含所有感應器類別和主程式
- **大小：** ~800 行
- **優點：** 部署簡單，只需複製一個檔案
- **缺點：** 維護較困難
- **何時使用：** 快速部署、單一裝置、生產環境

#### `main.py`
- **用途：** 模組化版本的主程式
- **大小：** ~200 行
- **依賴：** sensors/ 資料夾、config.py
- **優點：** 代碼清晰，易於維護
- **何時使用：** 開發、測試、多人協作

#### `config.py`
- **用途：** 集中管理所有腳位配置
- **大小：** ~50 行
- **優點：** 修改配置不需要改主程式
- **何時使用：** 需要經常調整腳位時

---

### 感應器類別檔案（sensors/）

#### `heart_rate_monitor.py`
- **功能：** 心率計算演算法
- **演算法：** 移動窗口平滑 + 峰值檢測
- **參數：** sample_rate, window_size, smoothing_window
- **使用者：** MAX30102Sensor

#### `ad8232_sensor.py`
- **感應器：** AD8232 ECG
- **輸出：** ecg_value, lead_off_plus, lead_off_minus, lead_off
- **採樣率：** 10 Hz
- **特色：** 電極脫落檢測

#### `gsr_sensor.py`
- **感應器：** Grove GSR
- **輸出：** gsr_value
- **採樣率：** 10 Hz
- **用途：** 測量皮膚電導（壓力、情緒）

#### `myoware_sensor.py`
- **感應器：** Myoware EMG
- **輸出：** muscle_value, muscle_ok, muscle_voltage, muscle_reason
- **採樣率：** 10 Hz
- **特色：** 飽和檢測、平線檢測、異常診斷

#### `dht22_sensor.py`
- **感應器：** DHT22
- **輸出：** env_temperature, env_humidity
- **採樣率：** 0.5 Hz（每 2 秒）
- **限制：** 感應器本身限制最快 2 秒讀一次

#### `max30205_sensor.py`
- **感應器：** MAX30205 體溫
- **輸出：** body_temperature, body_temp_fresh
- **採樣率：** 1 Hz
- **特色：** I2C 總線恢復、值保持機制

#### `max30102_sensor.py`
- **感應器：** MAX30102 心率/血氧
- **輸出：** hr_value, spo2_value, ir_value
- **採樣率：** 10 Hz FIFO 處理 + 0.5 Hz 心率計算
- **特色：** 整合 HeartRateMonitor、週期性計算

---

### 測試檔案

#### `test_sensors.py`
- **用途：** 測試各個感應器
- **函數：**
  - `test_ecg()` - 測試 ECG
  - `test_gsr()` - 測試 GSR
  - `test_myoware()` - 測試 EMG
  - `test_dht22()` - 測試溫濕度
  - `test_max30205()` - 測試體溫
  - `test_max30102()` - 測試心率
  - `test_all()` - 測試所有感應器

#### `test_max30102_hr.py`
- **用途：** 專門測試 MAX30102 心率檢測
- **測試模式：**
  - `test_max30102_continuous()` - 連續監測（推薦）
  - `test_max30102_debug()` - 調試模式
  - `test_max30102_simple()` - 簡單測試
- **何時使用：** 心率無法顯示時

---

### 文件檔案

#### `README.md`
- **內容：** 專案總覽、快速開始、功能列表
- **適合：** 第一次接觸專案的人

#### `QUICK_REFERENCE.md`
- **內容：** 快速參考卡、常用命令、故障排除
- **適合：** 已熟悉專案，需要快速查找資訊

#### `PROJECT_STRUCTURE.md`
- **內容：** 詳細的專案結構、各檔案說明
- **適合：** 想深入了解架構的開發者

#### `MULTI_RATE_SYSTEM.md`
- **內容：** 多頻率系統原理、優點、配置方法
- **適合：** 想了解為什麼不同感應器可以不同頻率

#### `DEBUG_FRONTEND.md`
- **內容：** 前端調試指南、常見問題解決
- **適合：** 遇到前端顯示問題時

#### `ALL_IN_ONE_GUIDE.md`
- **內容：** 單檔案版本完整使用指南
- **適合：** 使用 `all_in_one.py` 的用戶

---

### 輔助檔案

#### `deploy.ps1`
- **用途：** PowerShell 自動部署腳本
- **功能：** 自動上傳 `all_in_one.py` 到 Pico W
- **修改：** 改變 `$PORT` 變數為你的 COM 埠

#### `frontend_debug_helper.js`
- **用途：** 前端 Vue.js 調試輔助程式
- **功能：** 添加詳細的 console.log 輸出
- **使用：** 整合到 Vue 組件中

---

## 🔄 版本演進

### v1.0 - 單檔案版本（hr.py）
- 所有代碼在一個檔案
- 難以維護和測試

### v2.0 - 模組化版本（sensors/）
- 每個感應器獨立類別
- 易於測試和維護
- 但部署較複雜

### v2.1 - 多頻率系統
- 各感應器獨立更新頻率
- 優化效能（減少 30-40% 讀取）
- 保持統一 10Hz 輸出

### v2.2 - All-in-One 版本（all_in_one.py）
- 結合 v1.0 的部署簡易性
- 保留 v2.1 的所有功能
- **目前推薦版本** ⭐

---

## 📊 檔案大小統計

| 檔案類型 | 數量 | 總行數 | 平均行數 |
|---------|------|--------|----------|
| 感應器類別 | 7 | ~600 | ~85 |
| 主程式 | 2 | ~1000 | ~500 |
| 測試檔案 | 2 | ~400 | ~200 |
| 文件 | 8 | ~2000 | ~250 |
| **總計** | **19** | **~4000** | **~210** |

---

## 🎓 學習路徑建議

### 初學者：
1. 閱讀 `README.md`
2. 使用 `all_in_one.py` 快速部署
3. 參考 `ALL_IN_ONE_GUIDE.md` 測試

### 中級使用者：
1. 了解 `PROJECT_STRUCTURE.md`
2. 使用模組化版本（`main.py` + `sensors/`）
3. 用 `test_sensors.py` 測試個別感應器
4. 閱讀 `MULTI_RATE_SYSTEM.md` 了解原理

### 進階開發者：
1. 研究各 sensor 類別的實作
2. 修改 `heart_rate_monitor.py` 優化演算法
3. 整合新的感應器
4. 貢獻改進和錯誤修正

---

## 🆘 求助指南

遇到問題時，按此順序查找：

1. **硬體問題** → `README.md` 硬體連接章節
2. **心率無法顯示** → `test_max30102_hr.py` + `DEBUG_FRONTEND.md`
3. **感應器讀數異常** → `test_sensors.py` 單獨測試
4. **部署問題** → `ALL_IN_ONE_GUIDE.md` 故障排除
5. **架構疑問** → `PROJECT_STRUCTURE.md` + `MULTI_RATE_SYSTEM.md`

---

**建議：將此檔案加入書籤，方便隨時查閱！** 📌
