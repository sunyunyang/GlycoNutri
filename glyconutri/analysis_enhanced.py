"""
分析增强与管理功能模块
饮酒、生理期、压力、疾病影响分析
周报/月报生成
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ============ 饮酒影响分析 ============

class AlcoholAnalysis:
    """饮酒对血糖的影响"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data.sort_values('timestamp')
    
    def analyze_after_drinking(self, drinking_time: datetime) -> Dict:
        """分析饮酒后血糖"""
        # 饮酒后 3-6 小时
        start = drinking_time
        end = drinking_time + timedelta(hours=6)
        
        after = self.cgm_data[
            (self.cgm_data['timestamp'] >= start) & 
            (self.cgm_data['timestamp'] <= end)
        ]
        
        # 饮酒前基线
        before = self.cgm_data[
            (self.cgm_data['timestamp'] >= drinking_time - timedelta(hours=1)) & 
            (self.cgm_data['timestamp'] < drinking_time)
        ]
        
        result = {
            'drinking_time': drinking_time.isoformat()
        }
        
        if not before.empty:
            result['baseline'] = round(before['glucose'].mean(), 1)
        
        if not after.empty:
            result['after'] = {
                'mean': round(after['glucose'].mean(), 1),
                'min': round(after['glucose'].min(), 1),
                'max': round(after['glucose'].max(), 1),
                'drop': round(result.get('baseline', 0) - after['glucose'].min(), 1) if 'baseline' in result else None
            }
        
        # 延迟性低血糖风险
        if not after.empty and after['glucose'].min() < 70:
            result['hypoglycemia_risk'] = '高'
            result['warning'] = '警惕饮酒后延迟性低血糖'
        else:
            result['hypoglycemia_risk'] = '低'
        
        return result
    
    def detect_drinking_pattern(self) -> Dict:
        """检测饮酒模式"""
        # 寻找血糖快速下降后稳定的模式
        self.cgm_data['diff'] = self.cgm_data['glucose'].diff()
        
        # 血糖下降 > 30 mg/dL 且在 1 小时内
        drops = self.cgm_data[
            (self.cgm_data['diff'] < -30) & 
            (self.cgm_data['diff'] > -80)
        ]
        
        if not drops.empty:
            return {
                'possible_drinking': True,
                'events': len(drops),
                'times': drops['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist()[:5]
            }
        
        return {'possible_drinking': False}


# ============ 生理期影响分析 ============

class MenstrualAnalysis:
    """女性生理期血糖影响"""
    
    def __init__(self, cgm_data: pd.DataFrame, period_log: List[Dict] = None):
        self.cgm_data = cgm_data.sort_values('timestamp')
        self.period_log = period_log or []
    
    def add_period_log(self, start_date: datetime, end_date: datetime = None):
        """记录生理期"""
        self.period_log.append({
            'start': start_date,
            'end': end_date or (start_date + timedelta(days=5))
        })
    
    def analyze_phase_impact(self) -> Dict:
        """分析各阶段影响"""
        if not self.period_log:
            return {'error': '需要生理期记录'}
        
        phases = {
            '经期 (Day 1-5)': (0, 5),
            '卵泡期 (Day 6-14)': (5, 14),
            '黄体期 (Day 15-28)': (14, 28)
        }
        
        results = {}
        
        for phase_name, (start_day, end_day) in phases.items():
            phase_data = []
            
            for period in self.period_log:
                period_start = period['start']
                
                for day_offset in range(start_day, end_day + 1):
                    day_date = period_start + timedelta(days=day_offset)
                    day_start = day_date.replace(hour=0, minute=0)
                    day_end = day_date.replace(hour=23, minute=59)
                    
                    day_data = self.cgm_data[
                        (self.cgm_data['timestamp'] >= day_start) &
                        (self.cgm_data['timestamp'] <= day_end)
                    ]
                    
                    if not day_data.empty:
                        phase_data.append(day_data['glucose'].mean())
            
            if phase_data:
                results[phase_name] = {
                    'mean': round(np.mean(phase_data), 1),
                    'std': round(np.std(phase_data), 1),
                    'days': len(phase_data)
                }
        
        # 对比
        if '经期 (Day 1-5)' in results and '卵泡期 (Day 6-14)' in results:
            follicular = results['卵泡期 (Day 6-14)']['mean']
            menstrual = results['经期 (Day 1-5)']['mean']
            results['comparison'] = {
                'menstrual_vs_follicular': round(menstrual - follicular, 1),
                'note': '经期血糖升高' if menstrual > follicular + 5 else '经期血糖下降' if menstrual < follicular - 5 else '无明显差异'
            }
        
        return {'menstrual_impact': results}


# ============ 压力影响分析 ============

class StressAnalysis:
    """压力对血糖的影响"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data.sort_values('timestamp')
    
    def detect_stress_periods(self) -> Dict:
        """检测压力期 (血糖持续升高)"""
        # 连续 2 小时血糖 > 160
        self.cgm_data['hour'] = self.cgm_data['timestamp'].dt.floor('H')
        hourly = self.cgm_data.groupby('hour')['glucose'].mean()
        
        stress_periods = []
        
        consecutive = 0
        start_hour = None
        
        for hour, glucose in hourly.items():
            if glucose > 160:
                if consecutive == 0:
                    start_hour = hour
                consecutive += 1
            else:
                if consecutive >= 2:
                    stress_periods.append({
                        'start': start_hour.isoformat(),
                        'end': (start_hour + timedelta(hours=consecutive)).isoformat(),
                        'duration_hours': consecutive,
                        'avg_glucose': round(hourly[start_hour:hour].mean(), 1)
                    })
                consecutive = 0
                start_hour = None
        
        return {
            'stress_periods': stress_periods,
            'total_periods': len(stress_periods),
            'interpretation': '注意压力管理' if len(stress_periods) > 3 else '压力水平正常'
        }


# ============ 疾病影响分析 ============

class IllnessAnalysis:
    """疾病对血糖的影响"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data.sort_values('timestamp')
    
    def detect_illness_periods(self) -> Dict:
        """检测疾病期间"""
        # 疾病信号: 血糖持续异常波动
        self.cgm_data['hour'] = self.cgm_data['timestamp'].dt.floor('H')
        hourly = self.cgm_data.groupby('hour').agg({
            'glucose': ['mean', 'std']
        })
        hourly.columns = ['mean', 'std']
        
        # 高波动期 (std > 30)
        high_volatility = hourly[hourly['std'] > 30]
        
        if not high_volatility.empty:
            return {
                'unusual_volatility': True,
                'periods': len(high_volatility),
                'hours': high_volatility.index.strftime('%Y-%m-%d %H:00').tolist()[:10],
                'suggestion': '检测到血糖异常波动，可能是疾病或感染影响'
            }
        
        return {'unusual_volatility': False}
    
    def compare_recent_days(self, days: int = 7) -> Dict:
        """对比近期天数"""
        recent = self.cgm_data[self.cgm_data['timestamp'] >= datetime.now() - timedelta(days=days)]
        previous = self.cgm_data[
            (self.cgm_data['timestamp'] >= datetime.now() - timedelta(days=days*2)) &
            (self.cgm_data['timestamp'] < datetime.now() - timedelta(days=days))
        ]
        
        if recent.empty or previous.empty:
            return {'error': '数据不足'}
        
        recent_mean = recent['glucose'].mean()
        previous_mean = previous['glucose'].mean()
        
        change = recent_mean - previous_mean
        
        return {
            'recent_mean': round(recent_mean, 1),
            'previous_mean': round(previous_mean, 1),
            'change': round(change, 1),
            'interpretation': '近期血糖显著升高，注意身体状况' if change > 20 else '近期血糖显著下降' if change < -20 else '近期血糖稳定'
        }


# ============ 周报/月报生成 ============

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data.sort_values('timestamp')
    
    def generate_weekly_report(self) -> Dict:
        """生成周报"""
        # 最近 7 天
        week_data = self.cgm_data[
            self.cgm_data['timestamp'] >= datetime.now() - timedelta(days=7)
        ]
        
        if week_data.empty:
            return {'error': '数据不足'}
        
        # 按天汇总
        week_data['date'] = week_data['timestamp'].dt.date
        daily = week_data.groupby('date').agg({
            'glucose': ['mean', 'std', 'min', 'max', 'count']
        })
        daily.columns = ['mean', 'std', 'min', 'max', 'count']
        
        # 计算 TIR
        in_range = ((week_data['glucose'] >= 70) & (week_data['glucose'] <= 180)).sum()
        tir = in_range / len(week_data) * 100
        
        # 生成报告
        report = {
            'period': f'近7天',
            'overview': {
                'total_readings': len(week_data),
                'mean_glucose': round(week_data['glucose'].mean(), 1),
                'tir': round(tir, 1),
                'gv': round(week_data['glucose'].std() / week_data['glucose'].mean() * 100, 1)
            },
            'daily_summary': [],
            'highlights': [],
            'recommendations': []
        }
        
        # 每日汇总
        for date, row in daily.iterrows():
            report['daily_summary'].append({
                'date': str(date),
                'mean': round(row['mean'], 1),
                'min': round(row['min'], 1),
                'max': round(row['max'], 1)
            })
        
        # 亮点
        best_day = daily['mean'].idxmin()
        report['highlights'].append(f'最佳日期: {best_day}, 平均血糖 {daily.loc[best_day, "mean"]:.1f}')
        
        worst_day = daily['mean'].idxmax()
        report['highlights'].append(f'需注意日期: {worst_day}, 平均血糖 {daily.loc[worst_day, "mean"]:.1f}')
        
        # 建议
        if tir < 50:
            report['recommendations'].append('TIR偏低，建议调整治疗方案')
        if tir >= 70:
            report['recommendations'].append('血糖控制良好，继续保持')
        
        if week_data['glucose'].std() > 30:
            report['recommendations'].append('血糖波动较大，注意餐后血糖控制')
        
        return report
    
    def generate_monthly_report(self) -> Dict:
        """生成月报"""
        month_data = self.cgm_data[
            self.cgm_data['timestamp'] >= datetime.now() - timedelta(days=30)
        ]
        
        if month_data.empty:
            return {'error': '数据不足'}
        
        # 按周汇总
        month_data['week'] = month_data['timestamp'].dt.isocalendar().week
        weekly = month_data.groupby('week').agg({
            'glucose': ['mean', 'std']
        })
        weekly.columns = ['mean', 'std']
        
        # 月度统计
        in_range = ((month_data['glucose'] >= 70) & (month_data['glucose'] <= 180)).sum()
        tir = in_range / len(month_data) * 100
        
        below_70 = (month_data['glucose'] < 70).sum() / len(month_data) * 100
        above_180 = (month_data['glucose'] > 180).sum() / len(month_data) * 100
        
        report = {
            'period': '近30天',
            'overview': {
                'total_readings': len(month_data),
                'mean_glucose': round(month_data['glucose'].mean(), 1),
                'median_glucose': round(month_data['glucose'].median(), 1),
                'std_glucose': round(month_data['glucose'].std(), 1),
                'tir': round(tir, 1),
                'tbr': round(below_70, 1),
                'tar': round(above_180, 1)
            },
            'weekly_trend': [],
            'time_of_day': self._analyze_time_of_day(month_data),
            'goals': self._check_goals(tir, below_70, above_180)
        }
        
        # 每周趋势
        for week, row in weekly.iterrows():
            report['weekly_trend'].append({
                'week': int(week),
                'mean': round(row['mean'], 1),
                'gv': round(row['std'] / row['mean'] * 100, 1)
            })
        
        return report
    
    def _analyze_time_of_day(self, data: pd.DataFrame) -> Dict:
        """时段分析"""
        data = data.copy()
        data['hour'] = data['timestamp'].dt.hour
        
        periods = {
            '凌晨 (0-6点)': (0, 6),
            '白天 (6-18点)': (6, 18),
            '晚上 (18-24点)': (18, 24)
        }
        
        result = {}
        for name, (start, end) in periods.items():
            period_data = data[(data['hour'] >= start) & (data['hour'] < end)]
            if not period_data.empty:
                result[name] = {
                    'mean': round(period_data['glucose'].mean(), 1),
                    'tir': round(((period_data['glucose'] >= 70) & (period_data['glucose'] <= 180)).sum() / len(period_data) * 100, 1)
                }
        
        return result
    
    def _check_goals(self, tir: float, tbr: float, tar: float) -> List[str]:
        """检查目标达成"""
        goals = []
        
        if tir >= 70:
            goals.append('✅ TIR 达成 (>70%)')
        else:
            goals.append(f'❌ TIR 未达成 ({tir:.1f}%)')
        
        if tbr < 4:
            goals.append('✅ 低血糖时间达标 (<4%)')
        else:
            goals.append(f'⚠️ 低血糖时间偏高 ({tbr:.1f}%)')
        
        if tar < 25:
            goals.append('✅ 高血糖时间达标 (<25%)')
        else:
            goals.append(f'⚠️ 高血糖时间偏高 ({tar:.1f}%)')
        
        return goals


# ============ 便捷函数 ============

def analyze_alcohol(cgm_data: pd.DataFrame, drinking_time: datetime) -> Dict:
    """饮酒影响分析"""
    analysis = AlcoholAnalysis(cgm_data)
    return analysis.analyze_after_drinking(drinking_time)


def analyze_stress(cgm_data: pd.DataFrame) -> Dict:
    """压力分析"""
    analysis = StressAnalysis(cgm_data)
    return analysis.detect_stress_periods()


def analyze_illness(cgm_data: pd.DataFrame) -> Dict:
    """疾病影响分析"""
    analysis = IllnessAnalysis(cgm_data)
    return analysis.detect_illness_periods()


def generate_weekly_report(cgm_data: pd.DataFrame) -> Dict:
    """生成周报"""
    generator = ReportGenerator(cgm_data)
    return generator.generate_weekly_report()


def generate_monthly_report(cgm_data: pd.DataFrame) -> Dict:
    """生成月报"""
    generator = ReportGenerator(cgm_data)
    return generator.generate_monthly_report()
