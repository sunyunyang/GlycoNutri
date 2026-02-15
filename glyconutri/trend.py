"""
血糖趋势分析模块
多日血糖趋势、周期性分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict


class TrendAnalysis:
    """血糖趋势分析"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data.sort_values('timestamp')
        
    def daily_summary(self) -> List[Dict]:
        """每日汇总"""
        self.cgm_data['date'] = self.cgm_data['timestamp'].dt.date
        
        daily_stats = []
        for date, group in self.cgm_data.groupby('date'):
            stats = {
                'date': str(date),
                'mean': group['glucose'].mean(),
                'median': group['glucose'].median(),
                'std': group['glucose'].std(),
                'min': group['glucose'].min(),
                'max': group['glucose'].max(),
                'data_points': len(group),
                'tir': self._calculate_tir(group)
            }
            daily_stats.append(stats)
        
        return daily_stats
    
    def _calculate_tir(self, day_data: pd.DataFrame, low: float = 70, high: float = 180) -> float:
        """计算指定日期的 TIR"""
        in_range = ((day_data['glucose'] >= low) & (day_data['glucose'] <= high)).sum()
        return in_range / len(day_data) * 100 if len(day_data) > 0 else 0
    
    def weekly_summary(self) -> Dict:
        """周汇总"""
        self.cgm_data['week'] = self.cgm_data['timestamp'].dt.isocalendar().week
        self.cgm_data['year'] = self.cgm_data['timestamp'].dt.year
        
        weekly = []
        for (year, week), group in self.cgm_data.groupby(['year', 'week']):
            weekly.append({
                'year': int(year),
                'week': int(week),
                'mean': group['glucose'].mean(),
                'std': group['glucose'].std(),
                'tir': self._calculate_tir(group),
                'days': group['timestamp'].dt.date.nunique()
            })
        
        return {'weekly': weekly}
    
    def monthly_summary(self) -> Dict:
        """月汇总"""
        self.cgm_data['month'] = self.cgm_data['timestamp'].dt.to_period('M')
        
        monthly = []
        for month, group in self.cgm_data.groupby('month'):
            monthly.append({
                'month': str(month),
                'mean': group['glucose'].mean(),
                'std': group['glucose'].std(),
                'tir': self._calculate_tir(group),
                'days': group['timestamp'].dt.date.nunique()
            })
        
        return {'monthly': monthly}
    
    def time_of_day_analysis(self) -> Dict:
        """时段分析"""
        self.cgm_data['hour'] = self.cgm_data['timestamp'].dt.hour
        
        # 定义时段
        periods = {
            '凌晨 (0-6)': (0, 6),
            '早上 (6-12)': (6, 12),
            '下午 (12-18)': (12, 18),
            '晚上 (18-24)': (18, 24)
        }
        
        results = {}
        for period_name, (start, end) in periods.items():
            period_data = self.cgm_data[(self.cgm_data['hour'] >= start) & (self.cgm_data['hour'] < end)]
            if not period_data.empty:
                results[period_name] = {
                    'mean': period_data['glucose'].mean(),
                    'std': period_data['glucose'].std(),
                    'tir': self._calculate_tir(period_data),
                    'count': len(period_data)
                }
        
        return {'time_of_day': results}
    
    def weekday_analysis(self) -> Dict:
        """星期分析"""
        self.cgm_data['weekday'] = self.cgm_data['timestamp'].dt.dayofweek
        
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        results = {}
        for i, name in enumerate(weekdays):
            day_data = self.cgm_data[self.cgm_data['weekday'] == i]
            if not day_data.empty:
                results[name] = {
                    'mean': day_data['glucose'].mean(),
                    'std': day_data['glucose'].std(),
                    'tir': self._calculate_tir(day_data)
                }
        
        return {'weekday': results}
    
    def pattern_detection(self) -> Dict:
        """模式检测"""
        patterns = {}
        
        # 黎明现象检测
        dawn = self.cgm_data[
            (self.cgm_data['timestamp'].dt.hour >= 4) & 
            (self.cgm_data['timestamp'].dt.hour < 8)
        ]
        baseline = self.cgm_data[
            (self.cgm_data['timestamp'].dt.hour >= 0) & 
            (self.cgm_data['timestamp'].dt.hour < 4)
        ]
        
        if not dawn.empty and not baseline.empty:
            dawn_rise = dawn['glucose'].mean() - baseline['glucose'].mean()
            if dawn_rise > 20:
                patterns['dawn_phenomenon'] = {
                    'detected': True,
                    'rise': dawn_rise
                }
        
        # 持续高血糖
        high_episodes = self._find_high_episodes()
        if high_episodes:
            patterns['high_episodes'] = high_episodes
        
        # 频繁低血糖
        low_episodes = self._find_low_episodes()
        if low_episodes:
            patterns['low_episodes'] = low_episodes
        
        # 日间波动大
        daily_stds = self.cgm_data.groupby(self.cgm_data['timestamp'].dt.date)['glucose'].std()
        high_var_days = (daily_stds > 30).sum()
        if high_var_days > 0:
            patterns['high_variability_days'] = high_var_days
        
        return {'patterns': patterns}
    
    def _find_high_episodes(self) -> List[Dict]:
        """找到持续高血糖事件"""
        high = self.cgm_data[self.cgm_data['glucose'] > 180].copy()
        if high.empty:
            return []
        
        episodes = []
        start = None
        prev_time = None
        
        high = high.sort_values('timestamp')
        for _, row in high.iterrows():
            if start is None:
                start = row['timestamp']
                prev_time = row['timestamp']
            elif (row['timestamp'] - prev_time).total_seconds() > 3600:  # 超过1小时
                # 保存上一个事件
                end = prev_time
                duration = (end - start).total_seconds() / 3600
                if duration >= 2:  # 持续至少2小时
                    episodes.append({
                        'start': start.isoformat(),
                        'end': end.isoformat(),
                        'duration_hours': round(duration, 1),
                        'max_glucose': high[(high['timestamp'] >= start) & (high['timestamp'] <= end)]['glucose'].max()
                    })
                start = row['timestamp']
            prev_time = row['timestamp']
        
        return episodes
    
    def _find_low_episodes(self) -> List[Dict]:
        """找到低血糖事件"""
        low = self.cgm_data[self.cgm_data['glucose'] < 70].copy()
        if low.empty:
            return []
        
        episodes = []
        start = None
        prev_time = None
        
        low = low.sort_values('timestamp')
        for _, row in low.iterrows():
            if start is None:
                start = row['timestamp']
                prev_time = row['timestamp']
            elif (row['timestamp'] - prev_time).total_seconds() > 1800:  # 超过30分钟
                if start != prev_time:
                    episodes.append({
                        'time': start.isoformat(),
                        'min_glucose': low[(low['timestamp'] >= start) & (low['timestamp'] <= prev_time)]['glucose'].min()
                    })
                start = row['timestamp']
            prev_time = row['timestamp']
        
        return episodes
    
    def get_full_trend(self) -> Dict:
        """完整趋势分析"""
        return {
            'daily': self.daily_summary(),
            **self.weekly_summary(),
            **self.monthly_summary(),
            **self.time_of_day_analysis(),
            **self.weekday_analysis(),
            **self.pattern_detection()
        }


# ============ 便捷函数 ============

def analyze_trend(cgm_data: pd.DataFrame) -> Dict:
    """分析血糖趋势"""
    analysis = TrendAnalysis(cgm_data)
    return analysis.get_full_trend()
