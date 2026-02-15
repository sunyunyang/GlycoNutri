"""
图表可视化模块
CGM 曲线、血糖波动图
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class GlucoseChart:
    """血糖图表生成"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data.sort_values('timestamp')
    
    def get_time_series_data(self) -> Dict:
        """获取时序数据 (用于折线图)"""
        data = []
        for _, row in self.cgm_data.iterrows():
            data.append({
                'x': row['timestamp'].isoformat(),
                'y': round(row['glucose'], 1)
            })
        return {'time_series': data}
    
    def get_tir_pie_data(self, low: float = 70, high: float = 180) -> Dict:
        """获取 TIR 饼图数据"""
        below = (self.cgm_data['glucose'] < low).sum()
        in_range = ((self.cgm_data['glucose'] >= low) & (self.cgm_data['glucose'] <= high)).sum()
        above = (self.cgm_data['glucose'] > high).sum()
        total = len(self.cgm_data)
        
        return {
            'tir_pie': {
                'below': {'count': int(below), 'percent': round(below / total * 100, 1) if total > 0 else 0},
                'in_range': {'count': int(in_range), 'percent': round(in_range / total * 100, 1) if total > 0 else 0},
                'above': {'count': int(above), 'percent': round(above / total * 100, 1) if total > 0 else 0}
            }
        }
    
    def get_daily_pattern_data(self) -> Dict:
        """获取每日模式数据 (24小时)"""
        self.cgm_data['hour'] = self.cgm_data['timestamp'].dt.hour
        
        hourly_data = []
        for hour in range(24):
            hour_data = self.cgm_data[self.cgm_data['hour'] == hour]
            if not hour_data.empty:
                hourly_data.append({
                    'hour': hour,
                    'mean': round(hour_data['glucose'].mean(), 1),
                    'min': round(hour_data['glucose'].min(), 1),
                    'max': round(hour_data['glucose'].max(), 1),
                    'std': round(hour_data['glucose'].std(), 1)
                })
        
        return {'hourly': hourly_data}
    
    def get_volatility_data(self) -> Dict:
        """获取波动性数据"""
        # 计算相邻点差值
        sorted_data = self.cgm_data.sort_values('timestamp')
        sorted_data['diff'] = sorted_data['glucose'].diff().abs()
        
        # 去除 NaN
        diffs = sorted_data['diff'].dropna()
        
        return {
            'volatility': {
                'mean_change': round(diffs.mean(), 1) if not diffs.empty else 0,
                'max_change': round(diffs.max(), 1) if not diffs.empty else 0,
                'std': round(diffs.std(), 1) if not diffs.empty else 0
            }
        }
    
    def get_all_chart_data(self) -> Dict:
        """获取所有图表数据"""
        return {
            **self.get_time_series_data(),
            **self.get_tir_pie_data(),
            **self.get_daily_pattern_data(),
            **self.get_volatility_data()
        }


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data
    
    def generate_csv(self) -> str:
        """生成 CSV 格式"""
        from glyconutri.analysis import analyze_glucose
        
        stats = analyze_glucose(self.cgm_data)
        
        # 基本统计
        csv_lines = [
            "# GlycoNutri 血糖分析报告",
            f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "# 基本统计",
            f"平均血糖,{stats.get('mean_glucose', 0):.1f}",
            f"中位数血糖,{stats.get('median_glucose', 0):.1f}",
            f"标准差,{stats.get('std_glucose', 0):.1f}",
            f"最低血糖,{stats.get('min_glucose', 0):.1f}",
            f"最高血糖,{stats.get('max_glucose', 0):.1f}",
            "",
            "# TIR 分析",
            f"Time in Range (70-180),{stats.get('tir', 0):.1f}%",
            f"Time Below Range (<70),{stats.get('tbr', 0):.1f}%",
            f"Time Above Range (>180),{stats.get('tar', 0):.1f}%",
            "",
            "# 原始数据",
            "Timestamp,Glucose (mg/dL)"
        ]
        
        # 添加原始数据
        for _, row in self.cgm_data.sort_values('timestamp').iterrows():
            csv_lines.append(f"{row['timestamp'].isoformat()},{row['glucose']:.1f}")
        
        return '\n'.join(csv_lines)
    
    def generate_summary_text(self) -> str:
        """生成文本摘要"""
        from glyconutri.analysis import analyze_glucose
        
        stats = analyze_glucose(self.cgm_data)
        
        lines = [
            "=" * 40,
            "GlycoNutri 血糖分析报告",
            "=" * 40,
            "",
            f"分析时段: {self.cgm_data['timestamp'].min().strftime('%Y-%m-%d %H:%M')} - {self.cgm_data['timestamp'].max().strftime('%Y-%m-%d %H:%M')}",
            f"数据点数: {len(self.cgm_data)}",
            "",
            "【基本统计】",
            f"  平均血糖: {stats.get('mean_glucose', 0):.1f} mg/dL",
            f"  血糖波动: {stats.get('gv', 0):.1f}%",
            f"  最低血糖: {stats.get('min_glucose', 0):.1f} mg/dL",
            f"  最高血糖: {stats.get('max_glucose', 0):.1f} mg/dL",
            "",
            "【TIR 分析】",
            f"  Time in Range (70-180): {stats.get('tir', 0):.1f}%",
            f"  Time Below Range (<70): {stats.get('tbr', 0):.1f}%",
            f"  Time Above Range (>180): {stats.get('tar', 0):.1f}%",
            "",
            "=" * 40
        ]
        
        return '\n'.join(lines)


# ============ 便捷函数 ============

def get_chart_data(cgm_data: pd.DataFrame) -> Dict:
    """获取图表数据"""
    chart = GlucoseChart(cgm_data)
    return chart.get_all_chart_data()

def generate_report(cgm_data: pd.DataFrame, format: str = 'csv') -> str:
    """生成报告"""
    report = ReportGenerator(cgm_data)
    if format == 'csv':
        return report.generate_csv()
    else:
        return report.generate_summary_text()
