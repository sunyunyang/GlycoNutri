"""
CGM 数据处理模块
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional


def load_cgm_data(filepath: str) -> pd.DataFrame:
    """加载 CGM 数据"""
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    elif filepath.endswith('.json'):
        df = pd.read_json(filepath)
    else:
        raise ValueError("不支持的文件格式，请使用 CSV 或 JSON")
    
    # 标准化列名
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    elif 'time' in df.columns:
        df['timestamp'] = pd.to_datetime(df['time'])
    elif 'date' in df.columns:
        df['timestamp'] = pd.to_datetime(df['date'])
    
    if 'glucose' in df.columns:
        df['glucose'] = pd.to_numeric(df['glucose'], errors='coerce')
    elif 'value' in df.columns:
        df['glucose'] = pd.to_numeric(df['value'], errors='coerce')
    
    return df.sort_values('timestamp')


def calculate_tir(df: pd.DataFrame, low: float = 70, high: float = 140) -> float:
    """计算 Time in Range (TIR)"""
    if 'glucose' not in df.columns:
        raise ValueError("数据中缺少血糖列")
    
    in_range = ((df['glucose'] >= low) & (df['glucose'] <= high)).sum()
    total = len(df)
    return (in_range / total) * 100 if total > 0 else 0


def calculate_gv(df: pd.DataFrame) -> float:
    """计算血糖波动 (Glycemic Variability)"""
    if 'glucose' not in df.columns:
        raise ValueError("数据中缺少血糖列")
    
    mean = df['glucose'].mean()
    std = df['glucose'].std()
    return (std / mean) * 100 if mean > 0 else 0


def calculate_auc(df: pd.DataFrame, threshold: float = 140) -> float:
    """计算血糖曲线下面积 (AUC)"""
    if 'glucose' not in df.columns:
        raise ValueError("数据中缺少血糖列")
    
    # 计算高于阈值部分的积分
    above_threshold = df[df['glucose'] > threshold]['glucose'] - threshold
    return above_threshold.sum()
