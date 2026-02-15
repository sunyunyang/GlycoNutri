"""
餐后血糖分析模块
分析餐后血糖响应，计算个体化 GI/GL
结合药代动力学/药效动力学 (PK/PD) 原理
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class MealRecord:
    """餐食记录"""
    def __init__(self, food_name: str, weight: float, carbs: float = None, 
                 gi: float = None, timestamp: datetime = None):
        self.food_name = food_name
        self.weight = weight  # 克
        self.carbs = carbs    # 碳水克数
        self.gi = gi         # 升糖指数
        self.timestamp = timestamp or datetime.now()
        
    @property
    def gl(self):
        """升糖负荷"""
        if self.carbs and self.gi:
            return (self.gi * self.carbs) / 100
        return None
    
    def to_dict(self):
        return {
            "food_name": self.food_name,
            "weight": self.weight,
            "carbs": self.carbs,
            "gi": self.gi,
            "gl": self.gl,
            "timestamp": self.timestamp.isoformat()
        }


class PostMealAnalysis:
    """餐后血糖分析 - PK/PD 原理"""
    
    def __init__(self, meal: MealRecord, cgm_data: pd.DataFrame):
        self.meal = meal
        self.cgm_data = cgm_data
        
    def find_post_meal_window(self, hours: int = 2) -> pd.DataFrame:
        """找到餐后时间窗口的数据"""
        meal_time = self.meal.timestamp
        
        # 餐后 X 小时的数据
        end_time = meal_time + timedelta(hours=hours)
        
        window = self.cgm_data[
            (self.cgm_data['timestamp'] >= meal_time) & 
            (self.cgm_data['timestamp'] <= end_time)
        ]
        
        return window
    
    def find_pre_meal_window(self, minutes: int = 30) -> pd.DataFrame:
        """找到餐前时间窗口的数据"""
        meal_time = self.meal.timestamp
        start_time = meal_time - timedelta(minutes=minutes)
        
        window = self.cgm_data[
            (self.cgm_data['timestamp'] >= start_time) & 
            (self.cgm_data['timestamp'] < meal_time)
        ]
        
        return window
    
    # ============ 基础指标 ============
    
    def calculate_baseline(self, minutes: int = 30) -> Optional[float]:
        """计算餐前基线血糖 (取餐前 N 分钟的平均值)"""
        baseline = self.find_pre_meal_window(minutes)
        if baseline.empty:
            return None
        return baseline['glucose'].mean()
    
    def calculate_peak(self) -> Optional[float]:
        """计算餐后血糖峰值 (mg/dL)"""
        window = self.find_post_meal_window()
        if window.empty:
            return None
        return window['glucose'].max()
    
    def calculate_peak_time(self) -> Optional[datetime]:
        """计算达峰时间"""
        window = self.find_post_meal_window()
        if window.empty:
            return None
        peak_idx = window['glucose'].idxmax()
        return window.loc[peak_idx, 'timestamp']
    
    # ============ PK/PD 动力学指标 ============
    
    def time_to_peak(self) -> Optional[float]:
        """达峰时间 (分钟) - PK: Tmax"""
        peak_time = self.calculate_peak_time()
        if peak_time is None:
            return None
        delta = peak_time - self.meal.timestamp
        return delta.total_seconds() / 60
    
    def rate_of_rise(self) -> Optional[float]:
        """血糖上升速率 (mg/dL/min) - PK: 吸收速率"""
        window = self.find_post_meal_window()
        if window.empty or len(window) < 2:
            return None
        
        baseline = self.calculate_baseline()
        
        # 找到从基线上升的第一个点
        window_sorted = window.sort_values('timestamp')
        for i, row in window_sorted.iterrows():
            if row['glucose'] > baseline:
                # 计算上升速率
                time_diff = (row['timestamp'] - self.meal.timestamp).total_seconds() / 60
                if time_diff > 0:
                    return (row['glucose'] - baseline) / time_diff
        return None
    
    def rate_of_decline(self) -> Optional[float]:
        """血糖下降速率 (mg/dL/min) - PK: 消除速率"""
        window = self.find_post_meal_window()
        if window.empty or len(window) < 4:
            return None
        
        # 从峰值后开始计算
        peak_time = self.calculate_peak_time()
        if peak_time is None:
            return None
        
        after_peak = window[window['timestamp'] > peak_time].sort_values('timestamp')
        if len(after_peak) < 2:
            return None
        
        # 使用线性回归计算下降速率
        from scipy import stats
        times = [(row['timestamp'] - peak_time).total_seconds() / 60 for _, row in after_peak.iterrows()]
        values = after_peak['glucose'].values
        
        if len(times) > 1 and times[-1] > 0:
            slope, _, _, _, _ = stats.linregress(times, values)
            return slope
        return None
    
    def peak_baseline_ratio(self) -> Optional[float]:
        """峰值/基线比 - PD: 效应强度比"""
        peak = self.calculate_peak()
        baseline = self.calculate_baseline()
        
        if peak is None or baseline is None or baseline == 0:
            return None
        
        return peak / baseline
    
    def glucose_excursion_amplitude(self) -> Optional[float]:
        """血糖波动幅度 (峰值 - 基线)"""
        peak = self.calculate_peak()
        baseline = self.calculate_baseline()
        
        if peak is None or baseline is None:
            return None
        
        return peak - baseline
    
    def calculate_total_auc(self, hours: int = 2) -> Optional[float]:
        """总曲线下面积 (tAUC) - 药时曲线下面积"""
        window = self.find_post_meal_window(hours)
        if window.empty or window.shape[0] < 2:
            return None
        
        window = window.sort_values('timestamp')
        window['time_diff'] = window['timestamp'].diff().dt.total_seconds() / 60  # 分钟
        
        # 梯形积分 (mg/dL·min)
        auc = 0
        for i in range(1, len(window)):
            h = window.iloc[i]['glucose'] + window.iloc[i-1]['glucose']
            t = window.iloc[i]['time_diff']
            auc += h * t / 2
        
        return auc
    
    def calculate_incremental_auc(self, hours: int = 2) -> Optional[float]:
        """增量曲线下面积 (iAUC) - PD: 净效应"""
        window = self.find_post_meal_window(hours)
        if window.empty or window.shape[0] < 2:
            return None
        
        baseline = self.calculate_baseline()
        if baseline is None:
            return None
        
        # 只计算高于基线的部分
        window = window.copy()
        window['above_baseline'] = window['glucose'] - baseline
        window.loc[window['above_baseline'] < 0, 'above_baseline'] = 0
        
        window = window.sort_values('timestamp')
        window['time_diff'] = window['timestamp'].diff().dt.total_seconds() / 3600  # 小时
        
        # 梯形积分 (mg/dL·h)
        iauc = 0
        for i in range(1, len(window)):
            h = window.iloc[i]['above_baseline'] + window.iloc[i-1]['above_baseline']
            t = window.iloc[i]['time_diff']
            iauc += h * t / 2
        
        return iauc
    
    def calculate_mage(self, hours: int = 2, sd_threshold: float = 1.0) -> Optional[float]:
        """MAGE - Mean Amplitude of Glycemic Excursions
        平均血糖波动幅度 - 标准差法
        PD: 血糖变异性金标准
        """
        window = self.find_post_meal_window(hours)
        if window.empty:
            return None
        
        # 计算超过1个标准差的波动
        mean_g = window['glucose'].mean()
        std_g = window['glucose'].std()
        
        excursions = []
        prev = window['glucose'].iloc[0]
        for g in window['glucose'].iloc[1:]:
            diff = g - prev
            if abs(diff) >= std_g * sd_threshold:
                excursions.append(abs(diff))
            prev = g
        
        return np.mean(excursions) if excursions else None
    
    def duration_above_target(self, target: float = 180, hours: int = 2) -> Optional[float]:
        """超标持续时间 (分钟) - PD: 高血糖暴露"""
        window = self.find_post_meal_window(hours)
        if window.empty:
            return None
        
        above = window[window['glucose'] > target]
        if above.empty:
            return 0
        
        # 近似计算：假设均匀分布
        return len(above) / len(window) * hours * 60
    
    def count_excursions(self, hours: int = 2, threshold: float = 10) -> Optional[int]:
        """波动次数 - 血糖波动频率"""
        window = self.find_post_meal_window(hours)
        if window.empty:
            return None
        
        # 统计方向变化次数
        count = 0
        prev = window['glucose'].iloc[0]
        direction = 0  # 0: 初始, 1: 上升, -1: 下降
        
        for g in window['glucose'].iloc[1:]:
            diff = g - prev
            if abs(diff) >= threshold:
                new_direction = 1 if diff > 0 else -1
                if direction != 0 and new_direction != direction:
                    count += 1
                direction = new_direction
            prev = g
        
        return count
    
    def half_life_estimate(self) -> Optional[float]:
        """血糖半衰期估计 (分钟) - PK: 消除半衰期
        从峰值下降过程中，计算血糖下降一半的时间
        """
        window = self.find_post_meal_window()
        if window.empty or len(window) < 4:
            return None
        
        peak_time = self.calculate_peak_time()
        if peak_time is None:
            return None
        
        baseline = self.calculate_baseline()
        if baseline is None:
            return None
        
        peak = self.calculate_peak()
        half_value = (peak + baseline) / 2
        
        after_peak = window[window['timestamp'] > peak_time].sort_values('timestamp')
        
        # 找到血糖降到一半的时间点
        for _, row in after_peak.iterrows():
            if row['glucose'] <= half_value:
                half_time = (row['timestamp'] - peak_time).total_seconds() / 60
                return half_time * 2  # 半衰期 = 降到一半的时间 * 2
        
        return None
    
    def response_magnitude(self) -> Optional[float]:
        """血糖响应幅度 (峰值 - 基线)"""
        return self.glucose_excursion_amplitude()
    
    def get_full_analysis(self) -> Dict:
        """获取完整 PK/PD 分析结果"""
        baseline = self.calculate_baseline()
        peak = self.calculate_peak()
        peak_time = self.calculate_peak_time()
        response = self.response_magnitude()
        iauc = self.calculate_incremental_auc()
        
        return {
            "meal": self.meal.to_dict(),
            # 基础指标
            "baseline_glucose": baseline,
            "peak_glucose": peak,
            "peak_time": peak_time.isoformat() if peak_time else None,
            "response_magnitude": response,
            "iauc_2h": iauc,
            # PK 指标
            "pk": {
                "time_to_peak_min": self.time_to_peak(),
                "rate_of_rise_mg_dl_min": self.rate_of_rise(),
                "rate_of_decline_mg_dl_min": self.rate_of_decline(),
                "half_life_min": self.half_life_estimate(),
                "total_auc_mg_dl_min": self.calculate_total_auc()
            },
            # PD 指标
            "pd": {
                "peak_baseline_ratio": self.peak_baseline_ratio(),
                "excursion_amplitude": self.glucose_excursion_amplitude(),
                "mage": self.calculate_mage(),
                "duration_above_180_min": self.duration_above_target(180),
                "excursion_count": self.count_excursions(),
                "iauc_2h": iauc
            },
            "data_points": len(self.find_post_meal_window())
        }


class MealSession:
    """一次餐次（包含多种食物）"""
    
    def __init__(self, timestamp: datetime = None):
        self.timestamp = timestamp or datetime.now()
        self.meals: List[MealRecord] = []
        
    def add_food(self, food_name: str, weight: float, carbs: float = None, gi: float = None):
        """添加食物到这一餐"""
        meal = MealRecord(food_name, weight, carbs, gi, self.timestamp)
        self.meals.append(meal)
        return meal
    
    @property
    def total_carbs(self) -> float:
        """总碳水"""
        return sum(m.carbs or 0 for m in self.meals)
    
    @property
    def total_gl(self) -> float:
        """总 GL"""
        return sum(m.gl or 0 for m in self.meals)
    
    @property
    def weighted_gi(self) -> float:
        """加权平均 GI"""
        if not self.meals or self.total_carbs == 0:
            return 0
        
        total_gi_carbs = sum((m.gi or 0) * (m.carbs or 0) for m in self.meals)
        return total_gi_carbs / self.total_carbs
    
    def analyze(self, cgm_data: pd.DataFrame) -> Dict:
        """分析这一餐的血糖响应"""
        analysis = PostMealAnalysis(self.meals[0] if self.meals else None, cgm_data)
        
        return {
            "timestamp": self.timestamp.isoformat(),
            "foods": [m.to_dict() for m in self.meals],
            "total_carbs": self.total_carbs,
            "total_gl": self.total_gl,
            "weighted_gi": self.weighted_gi,
            "analysis": analysis.get_full_analysis() if self.meals else {}
        }


def create_meal_session(foods: List[Dict], timestamp: datetime = None) -> MealSession:
    """创建餐次并添加多种食物
    
    Args:
        foods: 食物列表 [{"name": "米饭", "weight": 100, "carbs": 28}, ...]
        timestamp: 餐食时间
    
    Returns:
        MealSession 对象
    """
    session = MealSession(timestamp)
    
    for food in foods:
        # 从数据库获取 GI 和碳水
        from glyconutri.food import get_food_info
        
        info = get_food_info(food['name'])
        
        carbs = food.get('carbs')
        gi = food.get('gi')
        
        if info and carbs is None:
            carbs = info.get('carbs_per_100g')
            if carbs and food.get('weight'):
                carbs = carbs * food['weight'] / 100
        
        if info and gi is None:
            gi = info.get('gi')
        
        session.add_food(
            food_name=food['name'],
            weight=food.get('weight', 100),
            carbs=carbs,
            gi=gi
        )
    
    return session


class RepeatedMealAnalyzer:
    """重复餐食分析 - 多次测量取平均"""
    
    def __init__(self):
        self.sessions: List[MealSession] = []
        
    def add_session(self, session: MealSession):
        """添加一次餐次"""
        self.sessions.append(session)
    
    def analyze_repeated(self, cgm_data: pd.DataFrame) -> Dict:
        """分析多次餐后的血糖响应"""
        if not self.sessions:
            return {}
        
        responses = []
        peaks = []
        baselines = []
        iaucs = []
        
        for session in self.sessions:
            if not session.meals:
                continue
            
            analysis = PostMealAnalysis(session.meals[0], cgm_data)
            
            resp = analysis.response_magnitude()
            peak = analysis.calculate_peak()
            baseline = analysis.calculate_baseline()
            iauc = analysis.calculate_incremental_auc()
            
            if resp is not None:
                responses.append(resp)
            if peak is not None:
                peaks.append(peak)
            if baseline is not None:
                baselines.append(baseline)
            if iauc is not None:
                iaucs.append(iauc)
        
        return {
            "sample_count": len(self.sessions),
            "response_magnitude": {
                "mean": np.mean(responses) if responses else None,
                "std": np.std(responses) if len(responses) > 1 else 0,
                "values": responses
            },
            "peak_glucose": {
                "mean": np.mean(peaks) if peaks else None,
                "std": np.std(peaks) if len(peaks) > 1 else 0,
                "values": peaks
            },
            "baseline_glucose": {
                "mean": np.mean(baselines) if baselines else None,
                "std": np.std(baselines) if len(baselines) > 1 else 0,
                "values": baselines
            },
            "iauc_2h": {
                "mean": np.mean(iaucs) if iaucs else None,
                "std": np.std(iaucs) if len(iaucs) > 1 else 0,
                "values": iaucs
            }
        }
