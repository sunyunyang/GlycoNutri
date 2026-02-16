"""
昼夜节律分析模块
24h 模式、皮质醇节律、轮班工作影响分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class CircadianAnalysis:
    """昼夜节律分析"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data.sort_values('timestamp')
        self.cgm_data['hour'] = self.cgm_data['timestamp'].dt.hour
        self.cgm_data['weekday'] = self.cgm_data['timestamp'].dt.dayofweek
    
    def hourly_pattern(self) -> Dict:
        """每小时血糖模式"""
        hourly_stats = []
        
        for hour in range(24):
            hour_data = self.cgm_data[self.cgm_data['hour'] == hour]
            
            if not hour_data.empty:
                hourly_stats.append({
                    'hour': hour,
                    'mean': round(hour_data['glucose'].mean(), 1),
                    'std': round(hour_data['glucose'].std(), 1),
                    'min': round(hour_data['glucose'].min(), 1),
                    'max': round(hour_data['glucose'].max(), 1),
                    'count': len(hour_data)
                })
        
        return {'hourly_pattern': hourly_stats}
    
    def time_period_analysis(self) -> Dict:
        """时段分析"""
        periods = {
            '凌晨 (0-4点)': list(range(0, 4)),
            '凌晨 (4-7点)': list(range(4, 7)),
            '早上 (7-10点)': list(range(7, 10)),
            '上午 (10-12点)': list(range(10, 12)),
            '中午 (12-14点)': list(range(12, 14)),
            '下午 (14-17点)': list(range(14, 17)),
            '傍晚 (17-20点)': list(range(17, 20)),
            '晚上 (20-24点)': list(range(20, 24))
        }
        
        results = {}
        for period_name, hours in periods.items():
            period_data = self.cgm_data[self.cgm_data['hour'].isin(hours)]
            
            if not period_data.empty:
                results[period_name] = {
                    'mean': round(period_data['glucose'].mean(), 1),
                    'std': round(period_data['glucose'].std(), 1),
                    'tir': self._calc_tir(period_data),
                    'count': len(period_data)
                }
        
        return {'time_periods': results}
    
    def _calc_tir(self, data: pd.DataFrame, low: float = 70, high: float = 180) -> float:
        """计算 TIR"""
        if data.empty:
            return 0
        in_range = ((data['glucose'] >= low) & (data['glucose'] <= high)).sum()
        return round(in_range / len(data) * 100, 1)
    
    def dawn_phenomenon_analysis(self) -> Dict:
        """黎明现象分析"""
        # 4-8点 vs 0-4点
        dawn = self.cgm_data[(self.cgm_data['hour'] >= 4) & (self.cgm_data['hour'] < 8)]
        early_night = self.cgm_data[(self.cgm_data['hour'] >= 0) & (self.cgm_data['hour'] < 4)]
        
        if dawn.empty or early_night.empty:
            return {'dawn_phenomenon': False}
        
        dawn_mean = dawn['glucose'].mean()
        night_mean = early_night['glucose'].mean()
        rise = dawn_mean - night_mean
        
        return {
            'dawn_phenomenon': rise > 10,
            'rise_amount': round(rise, 1),
            'dawn_mean': round(dawn_mean, 1),
            'night_mean': round(night_mean, 1),
            'severity': '明显' if rise > 20 else '轻微' if rise > 10 else '无'
        }
    
    def somogyi_effect_analysis(self) -> Dict:
        """Somogyi 效应分析 (夜间低血糖后反跳)"""
        # 找夜间低血糖
        night_low = self.cgm_data[
            (self.cgm_data['hour'] >= 0) & 
            (self.cgm_data['hour'] < 6) &
            (self.cgm_data['glucose'] < 70)
        ]
        
        if night_low.empty:
            return {'somogyi_effect': False}
        
        # 检查低血糖后是否有高血糖
        low_times = night_low['timestamp'].tolist()
        
        for low_time in low_times:
            # 低血糖后2-4小时
            after_low = self.cgm_data[
                (self.cgm_data['timestamp'] > low_time) &
                (self.cgm_data['timestamp'] < low_time + timedelta(hours=4))
            ]
            
            if not after_low.empty and after_low['glucose'].max() > 180:
                return {
                    'somogyi_effect': True,
                    'low_time': low_time.isoformat(),
                    'rebound_glucose': round(after_low['glucose'].max(), 1),
                    'rebound_time': after_low.loc[after_low['glucose'].idxmax(), 'timestamp'].isoformat()
                }
        
        return {'somogyi_effect': False}
    
    def circadian_stability(self) -> Dict:
        """昼夜节律稳定性"""
        hourly_means = []
        
        for hour in range(24):
            hour_data = self.cgm_data[self.cgm_data['hour'] == hour]
            if not hour_data.empty:
                hourly_means.append(hour_data['glucose'].mean())
        
        if len(hourly_means) < 12:
            return {'stability': '数据不足'}
        
        # 计算日内波动
        within_day_std = np.std(hourly_means)
        
        # 计算日间波动
        daily_means = self.cgm_data.groupby(self.cgm_data['timestamp'].dt.date)['glucose'].mean()
        between_day_std = daily_means.std()
        
        stability_score = 100 - (within_day_std * 0.5 + between_day_std * 0.5)
        stability_score = max(0, min(100, stability_score))
        
        return {
            'stability_score': round(stability_score, 1),
            'within_day_variability': round(within_day_std, 1),
            'between_day_variability': round(between_day_std, 1),
            'stability_level': '稳定' if stability_score > 70 else '一般' if stability_score > 50 else '不稳定'
        }
    
    def shift_work_analysis(self) -> Dict:
        """轮班工作影响分析"""
        # 对比工作日 vs 休息日
        self.cgm_data['is_weekend'] = self.cgm_data['weekday'].isin([5, 6])
        
        weekday_data = self.cgm_data[~self.cgm_data['is_weekend']]
        weekend_data = self.cgm_data[self.cgm_data['is_weekend']]
        
        result = {}
        
        if not weekday_data.empty:
            result['weekday'] = {
                'mean': round(weekday_data['glucose'].mean(), 1),
                'std': round(weekday_data['glucose'].std(), 1),
                'tir': self._calc_tir(weekday_data)
            }
        
        if not weekend_data.empty:
            result['weekend'] = {
                'mean': round(weekend_data['glucose'].mean(), 1),
                'std': round(weekend_data['glucose'].std(), 1),
                'tir': self._calc_tir(weekend_data)
            }
        
        if 'weekday' in result and 'weekend' in result:
            diff = result['weekday']['mean'] - result['weekend']['mean']
            result['work_effect'] = round(diff, 1)
        
        return {'shift_work': result}
    
    def get_full_analysis(self) -> Dict:
        """完整分析"""
        return {
            **self.hourly_pattern(),
            **self.time_period_analysis(),
            'dawn_phenomenon': self.dawn_phenomenon_analysis(),
            'somogyi_effect': self.somogyi_effect_analysis(),
            **self.circadian_stability(),
            **self.shift_work_analysis()
        }


# ============ 生物标志物模块 ============

class BiomarkerAnalysis:
    """血糖生物标志物分析"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data.sort_values('timestamp')
    
    def extract_features(self) -> Dict:
        """特征提取"""
        features = {}
        
        # 基本统计
        features['mean'] = round(self.cgm_data['glucose'].mean(), 1)
        features['std'] = round(self.cgm_data['glucose'].std(), 1)
        features['cv'] = round(features['std'] / features['mean'] * 100, 1)  # 变异系数
        
        # 范围内时间
        in_range = ((self.cgm_data['glucose'] >= 70) & (self.cgm_data['glucose'] <= 180)).sum()
        features['tir'] = round(in_range / len(self.cgm_data) * 100, 1)
        
        # 低血糖事件
        below_70 = (self.cgm_data['glucose'] < 70).sum()
        below_54 = (self.cgm_data['glucose'] < 54).sum()
        features['tbr'] = round(below_70 / len(self.cgm_data) * 100, 1)
        features['tbr_severe'] = round(below_54 / len(self.cgm_data) * 100, 1)
        
        # 高血糖
        above_180 = (self.cgm_data['glucose'] > 180).sum()
        above_250 = (self.cgm_data['glucose'] > 250).sum()
        features['tar'] = round(above_180 / len(self.cgm_data) * 100, 1)
        features['tar_severe'] = round(above_250 / len(self.cgm_data) * 100, 1)
        
        # 波动指标
        sorted_data = self.cgm_data.sort_values('timestamp')
        diffs = sorted_data['glucose'].diff().abs()
        features['mean_amplitude'] = round(diffs.mean(), 1)
        features['max_amplitude'] = round(diffs.max(), 1)
        
        # MAGE 计算
        mean_g = features['mean']
        std_g = features['std']
        excursions = []
        prev = sorted_data['glucose'].iloc[0]
        for g in sorted_data['glucose'].iloc[1:]:
            if abs(g - prev) >= std_g:
                excursions.append(abs(g - prev))
            prev = g
        features['mage'] = round(np.mean(excursions), 1) if excursions else 0
        
        return {'biomarkers': features}
    
    def classify_phenotype(self) -> Dict:
        """血糖表型分类"""
        features = self.extract_features()['biomarkers']
        
        phenotypes = []
        
        # 基于 TIR 分类
        if features['tir'] >= 70:
            tir_type = 'TIR良好'
        elif features['tir'] >= 50:
            tir_type = 'TIR中等'
        else:
            tir_type = 'TIR较差'
        phenotypes.append(tir_type)
        
        # 基于波动分类
        if features['cv'] < 20:
            var_type = '稳定型'
        elif features['cv'] < 35:
            var_type = '波动型'
        else:
            var_type = '高度波动'
        phenotypes.append(var_type)
        
        # 基于时间分类
        self.cgm_data['hour'] = self.cgm_data['timestamp'].dt.hour
        dawn = self.cgm_data[(self.cgm_data['hour'] >= 4) & (self.cgm_data['hour'] < 8)]
        night = self.cgm_data[(self.cgm_data['hour'] >= 0) & (self.cgm_data['hour'] < 4)]
        
        if not dawn.empty and not night.empty:
            if dawn['glucose'].mean() - night['glucose'].mean() > 15:
                phenotypes.append('黎明现象')
        
        # 夜间低血糖
        night_data = self.cgm_data[(self.cgm_data['hour'] >= 0) & (self.cgm_data['hour'] < 6)]
        if not night_data.empty and night_data['glucose'].min() < 70:
            phenotypes.append('夜间低血糖')
        
        return {
            'phenotype': phenotypes,
            'primary_type': tir_type,
            'variability_type': var_type
        }
    
    def risk_score(self) -> Dict:
        """综合风险评分"""
        score = 0
        
        features = self.extract_features()['biomarkers']
        
        # TIR 扣分
        if features['tir'] < 50:
            score += 30
        elif features['tir'] < 70:
            score += 15
        
        # 低血糖扣分
        if features['tbr'] > 5:
            score += 20
        elif features['tbr'] > 1:
            score += 10
        
        # 高血糖扣分
        if features['tar'] > 50:
            score += 20
        elif features['tar'] > 25:
            score += 10
        
        # 波动扣分
        if features['cv'] > 40:
            score += 20
        elif features['cv'] > 25:
            score += 10
        
        score = min(100, score)
        
        return {
            'risk_score': score,
            'risk_level': '高风险' if score > 60 else '中风险' if score > 30 else '低风险',
            'factors': self._get_risk_factors(features)
        }
    
    def _get_risk_factors(self, features: Dict) -> List[str]:
        """风险因素"""
        factors = []
        
        if features['tir'] < 70:
            factors.append('Time in Range偏低')
        if features['tbr'] > 1:
            factors.append('低血糖时间过长')
        if features['tar'] > 25:
            factors.append('高血糖时间过长')
        if features['cv'] > 25:
            factors.append('血糖波动较大')
        if features['mage'] > 40:
            factors.append('MAGE偏高')
        
        return factors
    
    def get_full_analysis(self) -> Dict:
        """完整分析"""
        return {
            **self.extract_features(),
            **self.classify_phenotype(),
            **self.risk_score()
        }


# ============ 便捷函数 ============

def analyze_circadian(cgm_data: pd.DataFrame) -> Dict:
    """昼夜节律分析"""
    analysis = CircadianAnalysis(cgm_data)
    return analysis.get_full_analysis()


def analyze_biomarkers(cgm_data: pd.DataFrame) -> Dict:
    """生物标志物分析"""
    analysis = BiomarkerAnalysis(cgm_data)
    return analysis.get_full_analysis()
