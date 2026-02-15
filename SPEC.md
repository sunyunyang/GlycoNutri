# GlycoNutri - 血糖营养计算工具

## 项目概述

**项目名称**: GlycoNutri  
**类型**: Python CLI/Web 工具  
**目标用户**: 营养科、内分泌科医生  
**核心功能**: 结合 CGM 数据与食物营养分析，为医生提供临床决策支持

---

## 功能需求

### 1. 血糖数据输入

- **CGM 数据导入**: 支持 CSV/JSON 格式 (Dexcom, Libre 等)
- **手动输入**: 指尖血、静脉血定期记录
- **数据验证**: 自动检测异常值

### 2. 食物/营养计算

- **GI 查询**: 升糖指数数据库
- **GL 计算**: GL = (GI × 碳水) / 100
- **碳水计算**: 食物碳水化合物含量
- **膳食记录**: 记录患者饮食

### 3. 数据分析

- **Time in Range (TIR)**: 血糖在目标范围内的时间占比
- **Glycemic Variability (GV)**: 血糖波动幅度
- **餐后血糖响应**: 餐后血糖峰值与恢复时间
- **血糖曲线下面积 (AUC)**

### 4. 报告生成

- **患者报告**: 易于理解的血糖/饮食报告
- **临床摘要**: 供医生查看的专业数据

---

## 技术栈

- **语言**: Python 3.10+
- **数据处理**: pandas, numpy
- **CLI**: Click / Typer
- **可选 Web**: FastAPI + HTML/JS

---

## 项目结构

```
GlycoNutri/
├── glyconutri/
│   ├── __init__.py
│   ├── cli.py          # CLI 入口
│   ├── cgm.py          # CGM 数据处理
│   ├── food.py         # 食物 GI/GL 计算
│   ├── analysis # 数据.py    分析
│   └── report.py       # 报告生成
├── data/
│   └── gi_database.csv # GI 数据
├── tests/
├── requirements.txt
└── README.md
```

---

## 第一个里程碑 (v0.1)

1. CLI 基础框架搭建
2. GI 数据库 (50+ 常见食物)
3. GL 计算功能
4. 血糖数据分析 (TIR, GV)

---

## 待定

- CGM 数据导入格式适配
- Web 界面
- 更多食物数据
