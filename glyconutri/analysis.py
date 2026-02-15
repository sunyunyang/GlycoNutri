"""
数据分析模块
"""

import pandas as pd
import numpy as np
from typing import Dict
from glyconutri.cgm import calculate_tir, calculate_gv


def analyze_glucose(df: pd.DataFrame) -> Dict:
    """综合分析血糖数据"""
    results = {}
    
    # 基本统计
    results['mean_glucose'] = df['glucose'].mean()
    results['median_glucose'] = df['glucose'].median()
    results['std_glucose'] = df['glucose'].std()
    results['min_glucose'] = df['glucose'].min()
    results['max_glucose'] = df['glucose'].max()
    
    # TIR 计算
    results['tir'] = calculate_tir(df)
    
    # 血糖波动
    results['gv'] = calculate_gv(df)
    
    # 低血糖时间
    results['time_below_70'] = (df['glucose'] < 70).sum() / len(df) * 100
    results['time_below_54'] = (df['glucose'] < 54).sum() / len(df) * 100
    
    # 高血糖时间
    results['time_above_180'] = (df['glucose'] > 180).sum() / len(df) * 100
    results['time_above_250'] = (df['glucose'] > 250).sum() / len(df) * 100
    
    return results


def get_glucose_status(tir: float) -> str:
    """根据 TIR 获取血糖控制状态"""
    if tir >= 70:
        return "良好"
    elif tir >= 50:
        return "一般"
    else:
        return "需改善"
