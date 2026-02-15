# 🩸 GlycoNutri

血糖营养计算工具 for 医生 & 患者

## 功能

- **CGM 分析**: 上传血糖数据，分析 TIR、GV、平均血糖等
- **餐后分析**: 记录食物，计算 GI/GL，关联 CGM 数据分析餐后血糖响应
- **食物查询**: 搜索食物
 GI/GL 值- **历史记录**: 本地保存分析历史

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Web 服务
python -m glyconutri.web

# 打开浏览器
http://localhost:8000
```

## CLI 用法

```bash
# CGM 分析
python -m glyconutri.cli analyze data/sample_cgm.csv

# 查询 GI
python -m glyconutri.cli gi 米饭

# 计算 GL
python -m glyconutri.cli gl 米饭 30
```

## 技术栈

- Python 3.10+
- FastAPI
- Pandas/NumPy

## 仓库

https://github.com/sunyunyang/GlycoNutri
