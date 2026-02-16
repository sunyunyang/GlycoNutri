"""
临床试验支持模块
药物效果对比、AB测试、统计分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from scipy import stats


class ClinicalTrial:
    """临床试验分析"""
    
    def __init__(self, cgm_data: pd.DataFrame, group: str = None):
        self.cgm_data = cgm_data.sort_values('timestamp')
        self.group = group
    
    def calculate_endpoints(self) -> Dict:
        """计算试验终点"""
        endpoints = {}
        
        # 首要终点: TIR
        in_range = ((self.cgm_data['glucose'] >= 70) & (self.cgm_data['glucose'] <= 180)).sum()
        endpoints['primary_tir'] = round(in_range / len(self.cgm_data) * 100, 1)
        
        # 次要终点
        endpoints['mean_glucose'] = round(self.cgm_data['glucose'].mean(), 1)
        endpoints['gv'] = round(self.cgm_data['glucose'].std() / self.cgm_data['glucose'].mean() * 100, 1)
        
        # 低血糖时间
        below_70 = (self.cgm_data['glucose'] < 70).sum()
        endpoints['tbr'] = round(below_70 / len(self.cgm_data) * 100, 1)
        
        # 高血糖时间
        above_180 = (self.cgm_data['glucose'] > 180).sum()
        endpoints['tar'] = round(above_180 / len(self.cgm_data) * 100, 1)
        
        return {'endpoints': endpoints}
    
    def calculate_efficacy_metrics(self) -> Dict:
        """计算疗效指标"""
        metrics = {}
        
        # 估计 HbA1c (eA1c)
        mean_g = self.cgm_data['glucose'].mean()
        metrics['ea1c'] = round((mean_g + 46.7) / 28.7, 1)
        
        # 目标范围内优越时间 (UTIR)
        optimal = (self.cgm_data['glucose'].between(80, 140)).sum()
        metrics['utir'] = round(optimal / len(self.cgm_data) * 100, 1)
        
        # 高血糖时间校正 (AHCP)
        above_250 = (self.cgm_data['glucose'] > 250).sum()
        metrics['ahcp'] = round(above_250 / len(self.cgm_data) * 100, 1)
        
        return {'efficacy': metrics}
    
    def get_summary(self) -> Dict:
        """试验总结"""
        return {
            **self.calculate_endpoints(),
            **self.calculate_efficacy_metrics(),
            'data_points': len(self.cgm_data),
            'duration_hours': (self.cgm_data['timestamp'].max() - self.cgm_data['timestamp'].min()).total_seconds() / 3600
        }


class ABTest:
    """AB 测试对比分析"""
    
    def __init__(self, group_a: pd.DataFrame, group_b: pd.DataFrame):
        self.group_a = group_a.sort_values('timestamp')
        self.group_b = group_b.sort_values('timestamp')
    
    def compare_tir(self) -> Dict:
        """TIR 对比"""
        trial_a = ClinicalTrial(self.group_a, 'A')
        trial_b = ClinicalTrial(self.group_b, 'B')
        
        tir_a = trial_a.calculate_endpoints()['endpoints']['primary_tir']
        tir_b = trial_b.calculate_endpoints()['endpoints']['primary_tir']
        
        diff = tir_b - tir_a
        
        # 统计检验
        _, p_value = stats.ttest_ind(
            self.group_a['glucose'],
            self.group_b['glucose']
        )
        
        return {
            'group_a_tir': tir_a,
            'group_b_tir': tir_b,
            'difference': round(diff, 1),
            'p_value': round(p_value, 4),
            'significant': p_value < 0.05,
            'better_group': 'B' if diff > 0 else 'A'
        }
    
    def compare_mean_glucose(self) -> Dict:
        """平均血糖对比"""
        mean_a = self.group_a['glucose'].mean()
        mean_b = self.group_b['glucose'].mean()
        
        _, p_value = stats.ttest_ind(
            self.group_a['glucose'],
            self.group_b['glucose']
        )
        
        return {
            'group_a_mean': round(mean_a, 1),
            'group_b_mean': round(mean_b, 1),
            'difference': round(mean_b - mean_a, 1),
            'p_value': round(p_value, 4),
            'significant': p_value < 0.05
        }
    
    def compare_gv(self) -> Dict:
        """血糖波动对比"""
        gv_a = self.group_a['glucose'].std() / self.group_a['glucose'].mean() * 100
        gv_b = self.group_b['glucose'].std() / self.group_b['glucose'].mean() * 100
        
        _, p_value = stats.levene(
            self.group_a['glucose'],
            self.group_b['glucose']
        )
        
        return {
            'group_a_gv': round(gv_a, 1),
            'group_b_gv': round(gv_b, 1),
            'difference': round(gv_b - gv_a, 1),
            'p_value': round(p_value, 4),
            'significant': p_value < 0.05
        }
    
    def compare_endpoints(self) -> Dict:
        """多终点对比"""
        trial_a = ClinicalTrial(self.group_a, 'A')
        trial_b = ClinicalTrial(self.group_b, 'B')
        
        endpoints_a = trial_a.calculate_endpoints()['endpoints']
        endpoints_b = trial_b.calculate_endpoints()['endpoints']
        
        comparison = {}
        for key in endpoints_a:
            diff = endpoints_b[key] - endpoints_a[key]
            comparison[key] = {
                'group_a': endpoints_a[key],
                'group_b': endpoints_b[key],
                'difference': round(diff, 1)
            }
        
        return {'endpoint_comparison': comparison}
    
    def get_full_comparison(self) -> Dict:
        """完整对比"""
        return {
            'tir_comparison': self.compare_tir(),
            'mean_comparison': self.compare_mean_glucose(),
            'gv_comparison': self.compare_gv(),
            'endpoints': self.compare_endpoints()
        }


class StatisticalAnalysis:
    """统计分析"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data
    
    def confidence_interval(self, metric: str = 'mean', confidence: float = 0.95) -> Dict:
        """置信区间"""
        if metric == 'mean':
            data = self.cgm_data['glucose']
            mean = data.mean()
            sem = stats.sem(data)
            ci = stats.t.interval(confidence, len(data)-1, loc=mean, scale=sem)
            
            return {
                'metric': 'mean',
                'value': round(mean, 2),
                'ci_lower': round(ci[0], 2),
                'ci_upper': round(ci[1], 2),
                'confidence': confidence
            }
        
        return {}
    
    def normality_test(self) -> Dict:
        """正态性检验"""
        data = self.cgm_data['glucose']
        
        # Shapiro-Wilk 检验
        stat, p_value = stats.shapiro(data)
        
        return {
            'test': 'Shapiro-Wilk',
            'statistic': round(stat, 4),
            'p_value': round(p_value, 4),
            'normal': p_value > 0.05
        }
    
    def outlier_detection(self, method: str = 'iqr') -> Dict:
        """异常值检测"""
        data = self.cgm_data['glucose']
        
        if method == 'iqr':
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            outliers = data[(data < lower) | (data > upper)]
            
            return {
                'method': 'IQR',
                'lower_bound': round(lower, 1),
                'upper_bound': round(upper, 1),
                'outlier_count': len(outliers),
                'outlier_percent': round(len(outliers) / len(data) * 100, 1)
            }
        
        return {}
    
    def correlation_analysis(self) -> Dict:
        """相关性分析"""
        # 按时间计算血糖变化率
        sorted_data = self.cgm_data.sort_values('timestamp')
        sorted_data['glucose_diff'] = sorted_data['glucose'].diff()
        sorted_data['time_diff'] = sorted_data['timestamp'].diff().dt.total_seconds() / 60
        
        valid_data = sorted_data.dropna()
        
        if len(valid_data) > 2:
            corr, p_value = stats.pearsonr(
                valid_data['time_diff'],
                valid_data['glucose_diff'].abs()
            )
            
            return {
                'correlation': round(corr, 4),
                'p_value': round(p_value, 4),
                'interpretation': '显著负相关' if corr < -0.3 else '显著正相关' if corr > 0.3 else '无显著相关'
            }
        
        return {'error': '数据不足'}


# ============ 便捷函数 ============

def clinical_trial_analysis(cgm_data: pd.DataFrame) -> Dict:
    """临床试验分析"""
    trial = ClinicalTrial(cgm_data)
    return trial.get_summary()


def ab_test(group_a: pd.DataFrame, group_b: pd.DataFrame) -> Dict:
    """AB 测试"""
    test = ABTest(group_a, group_b)
    return test.get_full_comparison()


def statistical_analysis(cgm_data: pd.DataFrame) -> Dict:
    """统计分析"""
    analysis = StatisticalAnalysis(cgm_data)
    
    return {
        'confidence_interval': analysis.confidence_interval(),
        'normality_test': analysis.normality_test(),
        'outliers': analysis.outlier_detection(),
        'correlation': analysis.correlation_analysis()
    }
