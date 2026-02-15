"""
餐后血糖分析模块
分析餐后血糖响应，计算个体化 GI/GL
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
    """餐后血糖分析"""
    
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
    
    def calculate_peak(self) -> Optional[float]:
        """计算餐后血糖峰值"""
        window = self.find_post_meal_window()
        if window.empty:
            return None
        return window['glucose'].max()
    
    def calculate_baseline(self, minutes: int = 30) -> Optional[float]:
        """计算餐前基线血糖 (取餐前 N 分钟的平均值)"""
        meal_time = self.meal.timestamp
        start_time = meal_time - timedelta(minutes=minutes)
        
        baseline = self.cgm_data[
            (self.cgm_data['timestamp'] >= start_time) & 
            (self.cgm_data['timestamp'] < meal_time)
        ]
        
        if baseline.empty:
            return None
        return baseline['glucose'].mean()
    
    def calculate_incremental_auc(self, hours: int = 2) -> Optional[float]:
        """计算餐后血糖增量曲线下面积 (iAUC)"""
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
        
        # 计算时间间隔（小时）
        window = window.sort_values('timestamp')
        window['time_diff'] = window['timestamp'].diff().dt.total_seconds() / 3600
        
        # 梯形积分
        iauc = 0
        for i in range(1, len(window)):
            h = window.iloc[i]['above_baseline'] + window.iloc[i-1]['above_baseline']
            t = window.iloc[i]['time_diff']
            iauc += h * t / 2
        
        return iauc
    
    def calculate_response_magnitude(self) -> Optional[float]:
        """计算血糖响应幅度 (峰值 - 基线)"""
        peak = self.calculate_peak()
        baseline = self.calculate_baseline()
        
        if peak is None or baseline is None:
            return None
        
        return peak - baseline
    
    def get_full_analysis(self) -> Dict:
        """获取完整分析结果"""
        baseline = self.calculate_baseline()
        peak = self.calculate_peak()
        response = self.response_magnitude()
        iauc = self.calculate_incremental_auc()
        
        return {
            "meal": self.meal.to_dict(),
            "baseline_glucose": baseline,
            "peak_glucose": peak,
            "response_magnitude": response,
            "iauc_2h": iauc,
            "data_points": len(self.find_post_meal_window())
        }
    
    def response_magnitude(self) -> Optional[float]:
        """血糖响应幅度"""
        return self.calculate_response_magnitude()


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
