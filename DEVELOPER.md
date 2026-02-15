# GlycoNutri 开发者对接文档

## 概述

GlycoNutri 是一个基于 CGM (连续血糖监测) 数据的血糖营养分析工具。可作为独立模块接入现有系统。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web Interface                        │
│         (FastAPI + HTML/JS - localhost:8000)           │
├─────────────────────────────────────────────────────────┤
│                      API Layer                          │
│  /api/cgm/analyze  /api/trend/analyze  /api/meal/...   │
├─────────────────────────────────────────────────────────┤
│                    Core Modules                         │
│  cgm.py | trend.py | meal.py | activity.py | ...      │
├─────────────────────────────────────────────────────────┤
│                     Data Layer                          │
│        gi_database.py | nutrition.py | medication.py   │
└─────────────────────────────────────────────────────────┘
```

---

## 模块说明

| 模块 | 功能 | 依赖 |
|------|------|------|
| `cgm.py` | CGM 数据解析、TIR/GV 计算 | pandas, numpy |
| `trend.py` | 多日趋势分析 | pandas |
| `meal.py` | 餐食营养分析 | nutrition.py |
| `activity.py` | 运动/睡眠血糖分析 | pandas |
| `medication.py` | 药物血糖分析 | pandas |
| `postmeal.py` | 餐后血糖 PK/PD 分析 | pandas, scipy |
| `chart.py` | 图表数据生成 | pandas |
| `gi_database.py` | GI 数据库 (150+ 食物) | - |
| `nutrition.py` | 营养数据库 (50+ 食物) | - |

---

## Python API 使用

### 1. CGM 数据分析

```python
from glyconutri.cgm import load_cgm_data, calculate_tir, calculate_gv
from glyconutri.analysis import analyze_glucose
import pandas as pd

# 解析 CGM 数据
df = load_cgm_data('your_cgm_file.csv')

# 或手动创建 DataFrame
df = pd.DataFrame({
    'timestamp': pd.to_datetime(['2026-02-15 08:00', '2026-02-15 08:15']),
    'glucose': [95, 98]
})

# 分析
results = analyze_glucose(df)
# 返回: {tir, gv, mean_glucose, std_glucose, min_glucose, max_glucose, ...}
```

### 2. 餐食营养分析

```python
from glyconutri.meal import analyze_meal

# 分析一餐
foods = [
    {"name": "米饭", "weight": 150},
    {"name": "鸡胸肉", "weight": 100},
    {"name": "西兰花", "weight": 100}
]

result = analyze_meal(foods, meal_name="午餐")
# 返回: {meal, nutrition_balance, glycemic_risk, recommendations}
```

### 3. 趋势分析

```python
from glyconutri.trend import analyze_trend

# 多日数据分析
result = analyze_trend(cgm_data)
# 返回: {daily, weekly, monthly, time_of_day, weekday, patterns}
```

### 4. 运动血糖分析

```python
from glyconutri.activity import analyze_exercise, analyze_sleep
from datetime import datetime

# 运动分析
result = analyze_exercise(
    exercise_type="跑步",
    duration_minutes=30,
    start_time=datetime.now(),
    cgm_data=df
)

# 睡眠分析
result = analyze_sleep(
    sleep_time=datetime(2026, 2, 15, 23, 0),
    wake_time=datetime(2026, 2, 16, 7, 0),
    cgm_data=df
)
```

### 5. 药物分析

```python
from glyconutri.medication import analyze_medication, analyze_insulin

# 口服药物分析
result = analyze_medication(
    medication_name="二甲双胍",
    dosage=500,
    taken_time=datetime.now(),
    cgm_data=df
)

# 胰岛素分析
result = analyze_insulin(
    insulin_type="速效",
    units=6,
    injection_time=datetime.now(),
    cgm_data=df
)
```

### 6. 餐后血糖 PK/PD 分析

```python
from glyconutri.postmeal import PostMealAnalysis, MealRecord
from datetime import datetime

meal = MealRecord("米饭", 150, carbs=42, gi=73, timestamp=datetime.now())
analysis = PostMealAnalysis(meal, cgm_data)

result = analysis.get_full_analysis()
# 返回: {baseline_glucose, peak_glucose, pk: {...}, pd: {...}, clinical: {...}}
```

---

## REST API 端点

启动服务: `python -m glyconutri.web`

### CGM 分析
```bash
POST /api/cgm/analyze
Body: {"data": "timestamp,glucose\n2026-02-15 08:00,95\n..."}
```

### 趋势分析
```bash
POST /api/trend/analyze
Body: {"data": "多日CGM数据"}
```

### 餐食营养分析
```bash
POST /api/meal/nutrition
Body: {"foods": [{"name": "米饭", "weight": 150}], "meal_name": "午餐"}
```

### 运动分析
```bash
POST /api/activity/exercise
Body: {"exercise_type": "跑步", "duration_minutes": 30, "start_time": "2026-02-15T10:00:00", "cgm_data": "..."}
```

### 睡眠分析
```bash
POST /api/activity/sleep
Body: {"sleep_time": "2026-02-15T23:00:00", "wake_time": "2026-02-16T07:00:00", "cgm_data": "..."}
```

### 药物分析
```bash
POST /api/medication/analyze
Body: {"medication_type": "口服", "medication_name": "二甲双胍", "dosage": 500, "taken_time": "2026-02-15T08:00:00", "cgm_data": "..."}
```

---

## 数据格式

### CGM 数据输入格式

支持 CSV、TXT、JSON，自动识别：

```
# 标准格式
timestamp,glucose
2026-02-15 08:00,95
2026-02-15 08:15,98

# 医院格式 (无表头)
2026-02-15 08:00 95
2026-02-15 08:15 98

# Tab 分隔
2026-02-15 08:00	95
```

### 返回数据格式

```json
{
  "tir": 75.5,
  "gv": 15.2,
  "mean_glucose": 120.3,
  "std_glucose": 18.5,
  "min_glucose": 65,
  "max_glucose": 210,
  "tbr": 2.1,
  "tar": 22.4
}
```

---

## 快速接入示例

### 作为 Python 模块使用

```python
# 1. 安装
pip install pandas numpy scipy

# 2. 导入
from glyconutri.meal import analyze_meal
from glyconutri.cgm import analyze_glucose

# 3. 调用
result = analyze_meal([{"name": "米饭", "weight": 100}])
print(result)
```

### 作为 HTTP API 使用

```python
import requests

# 调用餐食分析
response = requests.post("http://localhost:8000/api/meal/nutrition", json={
    "foods": [{"name": "米饭", "weight": 150}],
    "meal_name": "午餐"
})
print(response.json())
```

---

## 依赖

```
pandas
numpy
scipy
fastapi
uvicorn
```

---

## 目录结构

```
glyconutri/
├── __init__.py
├── cgm.py           # CGM 解析
├── cgm_adapters.py  # CGM 设备适配器
├── analysis.py       # 基础分析
├── trend.py         # 趋势分析
├── meal.py          # 餐食分析
├── nutrition.py     # 营养数据库
├── activity.py       # 运动/睡眠
├── medication.py    # 药物分析
├── postmeal.py      # 餐后 PK/PD
├── chart.py         # 图表
├── gi_database.py   # GI 数据库
├── food.py          # 食物查询
├── report.py        # 报告生成
└── web.py           # Web 服务
```

---

## 联系方式

- GitHub: https://github.com/sunyunyang/GlycoNutri
- 本地服务: http://localhost:8000
