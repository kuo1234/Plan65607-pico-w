// 前端調試輔助代碼
// 將此代碼添加到你的 Vue 組件中以幫助診斷問題

// 在 <script setup> 中的 updateCharts 函數修改如下：

const updateCharts = async () => {
  if (isUpdating.value) return;
  isUpdating.value = true;

  try {
    const frame = await window.electronAPI.getSensorData();
    
    // ===== 調試：檢查接收到的數據 =====
    if (frame && Object.keys(frame).length > 0) {
      console.group('📊 Sensor Data Frame');
      
      for (const path in frame) {
        const data = frame[path];
        
        console.log(`Device: ${deviceLabelMap[path] || path}`);
        console.log(`  HR: ${data.hr_value} BPM`);
        console.log(`  SpO2: ${data.spo2_value}%`);
        console.log(`  IR: ${data.ir_value}`);
        
        // 檢查心率狀態
        if (data.hr_value === 0) {
          if (data.ir_value < 10000) {
            console.warn(`  ⚠️ 手指未放在 MAX30102 上（IR 太低）`);
          } else {
            console.warn(`  ⚠️ 心率尚未計算完成（需要 3-5 秒）`);
          }
        } else if (data.hr_value > 0) {
          console.log(`  ✓ 心率正常顯示`);
        }
      }
      
      console.groupEnd();
    }
    
    if (frame) {
      updateTabsFromData(frame);
      const toRender = new Set();

      for (const path in charts) {
        const sensorCharts = charts[path];
        const dataObj = frame[path];
        if (!dataObj) continue;

        for (const groupKey in sensorCharts) {
          const group = sensorCharts[groupKey];
          if (!group) continue;
          group.statusList = [];

          group.dataKeys.forEach((entry, index) => {
            let rawValue = dataObj[entry.key];
            if (rawValue === undefined) return;

            // ===== 調試：追蹤心率數據 =====
            if (entry.key === "hr_value") {
              console.log(`💓 HR Data Point - Path: ${path}, Value: ${rawValue}, Chart visible: ${group.visible}`);
            }

            let displayValue = rawValue;

            // ... 其餘代碼保持不變 ...
            
            // 畫圖
            group.options.data[index].dataPoints.push({ x: xVal.value, y: displayValue });
            
            // ===== 調試：確認數據點已添加 =====
            if (entry.key === "hr_value") {
              const pointsCount = group.options.data[index].dataPoints.length;
              console.log(`  📈 Added to chart. Total points: ${pointsCount}, Last Y: ${displayValue}`);
            }
            
            if (group.options.data[index].dataPoints.length > 100) {
              const arr = group.options.data[index].dataPoints;
              arr.splice(0, arr.length - 100);
            }

            // ... 其餘狀態處理代碼 ...

            toRender.add(group);
          });
        }
      }

      for (const group of toRender) {
        if (group.instance) {
          // ===== 調試：確認圖表渲染 =====
          if (group.label === "心率與血氧") {
            console.log(`🎨 Rendering chart: ${group.label}`);
          }
          group.instance.render();
        }
      }
      
      xVal.value++;
      adjustChartHeights();
    }
  } catch (err) {
    console.error('❌ Update charts error:', err);
  } finally {
    isUpdating.value = false;
    setTimeout(updateCharts, chartUpdateFreq);
  }
};

// ===== 額外的診斷函數 =====

// 檢查所有圖表狀態
function debugChartStatus() {
  console.group('📊 Charts Status');
  for (const path in charts) {
    const sensorCharts = charts[path];
    console.log(`\nDevice: ${deviceLabelMap[path] || path}`);
    
    for (const groupKey in sensorCharts) {
      const group = sensorCharts[groupKey];
      console.log(`  ${group.label}:`);
      console.log(`    - Visible: ${group.visible}`);
      console.log(`    - Instance: ${group.instance ? '✓' : '✗'}`);
      console.log(`    - Data keys: ${group.dataKeys.map(k => k.key).join(', ')}`);
      
      if (group.options?.data) {
        group.options.data.forEach((series, i) => {
          console.log(`    - Series ${i} (${series.name}): ${series.dataPoints?.length || 0} points`);
        });
      }
    }
  }
  console.groupEnd();
}

// 手動觸發心率檢查
function debugHeartRate() {
  console.group('💓 Heart Rate Status');
  for (const path in charts) {
    const sensorCharts = charts[path];
    const hrGroup = sensorCharts.hr_spo2_group;
    
    if (hrGroup) {
      console.log(`\nDevice: ${deviceLabelMap[path] || path}`);
      console.log(`  Visible: ${hrGroup.visible}`);
      console.log(`  Has instance: ${!!hrGroup.instance}`);
      
      if (hrGroup.options?.data) {
        const hrSeries = hrGroup.options.data.find(s => s.name === "Heart Rate");
        if (hrSeries) {
          console.log(`  Data points: ${hrSeries.dataPoints.length}`);
          if (hrSeries.dataPoints.length > 0) {
            const latest = hrSeries.dataPoints[hrSeries.dataPoints.length - 1];
            console.log(`  Latest value: ${latest.y} BPM at time ${latest.x}`);
          }
        }
      }
    }
  }
  console.groupEnd();
}

// 在瀏覽器控制台中可以調用：
// debugChartStatus()
// debugHeartRate()

export { debugChartStatus, debugHeartRate };
