"""
运动与睡眠血糖分析模块
结合 CGM 数据分析运动和睡眠期间的血糖变化
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional


# ============ 运动类型定义 ============

EXERCISE_TYPES = {
    "走路": {"intensity": 1, "met": 3.0, "description": "轻度"},
    "慢跑": {"intensity": 2, "met": 7.0, "description": "中度"},
    "跑步": {"intensity": 3, "met": 9.8, "description": "高强度"},
    "骑行": {"intensity": 2, "met": 6.0, "description": "中度"},
    "游泳": {"intensity": 2, "met": 6.0, "description": "中度"},
    "瑜伽": {"intensity": 1, "met": 2.5, "description": "轻度"},
    "健身": {"intensity": 3, "met": 8.0, "description": "高强度"},
    "球类": {"intensity": 3, "met": 8.0, "description": "高强度"},
    "登山": {"intensity": 3, "met": 8.0, "description": "高强度"},
    "太极": {"intensity": 1, "met": 3.0, "description": "轻度"},
}


class ExerciseEvent:
    """运动事件"""
    
    def __init__(self, exercise_type: str, duration_minutes: int, 
                 start_time: datetime = None, intensity: str = None):
        self.exercise_type = exercise_type
        self.duration_minutes = duration_minutes
        self.start_time = start_time or datetime.now()
        
        # 获取运动定义
        exercise_info = EXERCISE_TYPES.get(exercise_type, EXERCISE_TYPES["走路"])
        self.intensity_level = intensity or exercise_info["intensity"]
        self.met = exercise_info["met"]
        self.description = exercise_info["description"]
    
    @property
    def end_time(self) -> datetime:
        return self.start_time + timedelta(minutes=self.duration_minutes)
    
    @property
    def calories_burned(self) -> float:
        """估算卡路里消耗 (假设体重 70kg)"""
        # MET × 体重(kg) × 时间(小时)
        weight_kg = 70
        return self.met * weight_kg * (self.duration_minutes / 60)
    
    def to_dict(self) -> dict:
        return {
            "exercise_type": self.exercise_type,
            "duration_minutes": self.duration_minutes,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "intensity": self.intensity_level,
            "description": self.description,
            "calories_burned": round(self.calories_burned, 1)
        }


class SleepEvent:
    """睡眠事件"""
    
    def __init__(self, sleep_time: datetime, wake_time: datetime = None):
        self.sleep_time = sleep_time
        self.wake_time = wake_time or (datetime.now() + timedelta(hours=8))
    
    @property
    def duration_hours(self) -> float:
        """睡眠时长 (小时)"""
        delta = self.wake_time - self.sleep_time
        return delta.total_seconds() / 3600
    
    @property
    def duration_minutes(self) -> float:
        """睡眠时长 (分钟)"""
        return self.duration_hours * 60
    
    def to_dict(self) -> dict:
        return {
            "sleep_time": self.sleep_time.isoformat(),
            "wake_time": self.wake_time.isoformat(),
            "duration_hours": round(self.duration_hours, 1),
            "duration_minutes": round(self.duration_minutes, 1)
        }


# ============ 运动血糖分析 ============

class ExerciseAnalysis:
    """运动前后血糖分析"""
    
    def __init__(self, exercise: ExerciseEvent, cgm_data: pd.DataFrame):
        self.exercise = exercise
        self.cgm_data = cgm_data
    
    def find_exercise_window(self, before_min: int = 30, after_min: int = 60) -> Dict[str, pd.DataFrame]:
        """找到运动前后时间窗口"""
        start = self.exercise.start_time - timedelta(minutes=before_min)
        end = self.exercise.end_time + timedelta(minutes=after_min)
        
        window = self.cgm_data[
            (self.cgm_data['timestamp'] >= start) & 
            (self.cgm_data['timestamp'] <= end)
        ]
        
        # 运动前
        before = window[window['timestamp'] < self.exercise.start_time]
        
        # 运动中
        during = window[
            (window['timestamp'] >= self.exercise.start_time) & 
            (window['timestamp'] <= self.exercise.end_time)
        ]
        
        # 运动后
        after = window[window['timestamp'] > self.exercise.end_time]
        
        return {"before": before, "during": during, "after": after}
    
    def calculate_baseline(self) -> Optional[float]:
        """运动前基线血糖"""
        window = self.find_exercise_window()
        before = window["before"]
        
        if before.empty:
            return None
        
        return before['glucose'].mean()
    
    def calculate_response(self) -> Dict:
        """计算运动血糖响应"""
        window = self.find_exercise_window()
        baseline = self.calculate_baseline()
        
        if baseline is None:
            return {"error": "数据不足"}
        
        results = {
            "baseline": baseline,
            "exercise": self.exercise.to_dict()
        }
        
        # 运动中最低血糖
        during = window["during"]
        if not during.empty:
            results["during_min"] = during['glucose'].min()
            results["during_max"] = during['glucose'].max()
            results["during_avg"] = during['glucose'].mean()
        
        # 运动后血糖变化
        after = window["after"]
        if not after.empty:
            results["after_min"] = after['glucose'].min()
            results["after_max"] = after['glucose'].max()
            results["after_avg"] = after['glucose'].mean()
            results["change_from_baseline"] = results["after_avg"] - baseline
        
        # 低血糖风险评估
        if results.get("during_min"):
            risk = "高"
            if results["during_min"] < 70:
                risk = "极高"
            elif results["during_min"] < 80:
                risk = "中高"
            elif results["during_min"] >= 100:
                risk = "低"
            results["hypoglycemia_risk"] = risk
        
        return results
    
    def generate_recommendations(self) -> List[str]:
        """生成运动建议"""
        response = self.calculate_response()
        
        if "error" in response:
            return ["数据不足，无法生成建议"]
        
        recommendations = []
        
        # 基于强度建议
        if self.exercise.intensity_level >= 3:
            recommendations.append("高强度运动后需注意延迟性低血糖 (2-6小时)")
        
        # 基于血糖变化
        if response.get("change_from_baseline"):
            change = response["change_from_baseline"]
            if change < -30:
                recommendations.append("血糖下降明显，建议运动中补充碳水")
            elif change > 30:
                recommendations.append("血糖升高，可能需要调整胰岛素")
        
        # 基于低血糖风险
        if response.get("hypoglycemia_risk") in ["极高", "中高"]:
            recommendations.append("存在低血糖风险，建议运动前减少胰岛素剂量")
        
        # 基于时长
        if self.exercise.duration_minutes > 60:
            recommendations.append("长时间运动建议中途补充碳水")
        
        if not recommendations:
            recommendations.append("运动强度适中，血糖控制良好")
        
        return recommendations
    
    def get_full_analysis(self) -> Dict:
        """完整分析"""
        response = self.calculate_response()
        recs = self.generate_recommendations()
        
        return {
            "exercise": response,
            "recommendations": recs
        }


# ============ 睡眠血糖分析 ============

class SleepAnalysis:
    """睡眠期间血糖分析"""
    
    def __init__(self, sleep: SleepEvent, cgm_data: pd.DataFrame):
        self.sleep = sleep
        self.cgm_data = cgm_data
    
    def find_sleep_window(self) -> pd.DataFrame:
        """找到睡眠期间的数据"""
        return self.cgm_data[
            (self.cgm_data['timestamp'] >= self.sleep.sleep_time) & 
            (self.cgm_data['timestamp'] <= self.sleep.wake_time)
        ]
    
    def calculate_metrics(self) -> Dict:
        """计算睡眠血糖指标"""
        window = self.find_sleep_window()
        
        if window.empty:
            return {"error": "数据不足"}
        
        results = {
            "sleep": self.sleep.to_dict(),
            "data_points": len(window)
        }
        
        # 统计指标
        results["mean"] = window['glucose'].mean()
        results["std"] = window['glucose'].std()
        results["min"] = window['glucose'].min()
        results["max"] = window['glucose'].max()
        
        # 时间范围
        results["time_in_range"] = (
            ((window['glucose'] >= 70) & (window['glucose'] <= 180)).sum() / len(window) * 100
        )
        
        # 夜间低血糖检测
        low_readings = window[window['glucose'] < 70]
        if not low_readings.empty:
            results["low_episodes"] = len(low_readings)
            results["low_min"] = low_readings['glucose'].min()
            results["low_times"] = low_readings['timestamp'].dt.strftime('%H:%M').tolist()
        
        # 夜间高血糖检测
        high_readings = window[window['glucose'] > 180]
        if not high_readings.empty:
            results["high_episodes"] = len(high_readings)
            results["high_max"] = high_readings['glucose'].max()
        
        # 血糖波动
        if len(window) > 1:
            window_sorted = window.sort_values('timestamp')
            diffs = window_sorted['glucose'].diff().abs()
            results["avg_fluctuation"] = diffs.mean()
            results["max_fluctuation"] = diffs.max()
        
        # 黎明现象 (Dawn Phenomenon) - 凌晨4-8点血糖升高
        dawn_window = window[
            (window['timestamp'].dt.hour >= 4) & 
            (window['timestamp'].dt.hour < 8)
        ]
        if not dawn_window.empty:
            # 对比前半夜
            early_night = window[
                (window['timestamp'].dt.hour >= 0) & 
                (window['timestamp'].dt.hour < 4)
            ]
            if not early_night.empty:
                dawn_rise = dawn_window['glucose'].mean() - early_night['glucose'].mean()
                results["dawn_phenomenon"] = round(dawn_rise, 1)
        
        # Somogyi 效应 - 夜间低血糖后反跳性高血糖
        if results.get("low_episodes"):
            # 找低血糖后的高血糖
            for idx, row in low_readings.iterrows():
                low_time = row['timestamp']
                after_low = window[window['timestamp'] > low_time + timedelta(hours=2)]
                if not after_low.empty and after_low['glucose'].max() > 180:
                    results["somogyi_effect"] = True
                    results["somogyi_detail"] = {
                        "low_time": low_time.isoformat(),
                        "rebound_high": after_low['glucose'].max()
                    }
                    break
        
        return results
    
    def assess_sleep_quality(self) -> Dict:
        """评估睡眠血糖质量"""
        metrics = self.calculate_metrics()
        
        if "error" in metrics:
            return {"quality": "未知", "score": 0, "issues": ["数据不足"]}
        
        score = 100
        issues = []
        
        # TIR 评分
        tir = metrics.get("time_in_range", 0)
        if tir >= 80:
            pass  # 良好
        elif tir >= 60:
            score -= 10
            issues.append("Time in Range偏低")
        else:
            score -= 25
            issues.append("Time in Range偏低")
        
        # 低血糖
        if metrics.get("low_episodes", 0) > 0:
            score -= 30
            issues.append(f"夜间低血糖 {metrics['low_episodes']} 次")
        
        # 高血糖
        high_episodes = metrics.get("high_episodes", 0)
        data_points = metrics.get("data_points", 1)
        if high_episodes > data_points * 0.3:
            score -= 15
            issues.append("夜间高血糖时间过长")
        
        # 波动
        if metrics.get("avg_fluctuation", 0) > 20:
            score -= 15
            issues.append("夜间血糖波动大")
        
        # 黎明现象
        if metrics.get("dawn_phenomenon", 0) > 20:
            score -= 10
            issues.append("存在黎明现象")
        
        score = max(0, score)
        
        quality = "优秀" if score >= 85 else "良好" if score >= 70 else "一般" if score >= 50 else "较差"
        
        return {
            "score": score,
            "quality": quality,
            "issues": issues
        }
    
    def generate_recommendations(self) -> List[str]:
        """生成睡眠建议"""
        metrics = self.calculate_metrics()
        quality = self.assess_sleep_quality()
        
        if "error" in metrics:
            return ["数据不足，无法生成建议"]
        
        recommendations = []
        
        # 低血糖建议
        if metrics.get("low_episodes", 0) > 0:
            recommendations.append("夜间出现低血糖，建议睡前适当补充碳水")
            recommendations.append("考虑减少睡前胰岛素剂量")
        
        # 高血糖建议
        if metrics.get("high_episodes", 0) > 0:
            recommendations.append("夜间血糖偏高，建议调整晚餐结构")
        
        # 黎明现象建议
        if metrics.get("dawn_phenomenon", 0) > 20:
            recommendations.append("存在黎明现象，考虑调整凌晨胰岛素")
        
        # Somogyi效应
        if metrics.get("somogyi_effect"):
            recommendations.append("检测到Somogyi效应，需避免夜间低血糖")
        
        # 波动建议
        if metrics.get("avg_fluctuation", 0) > 20:
            recommendations.append("夜间血糖波动大，注意晚餐时间和内容")
        
        # 睡眠质量
        if quality["quality"] == "优秀":
            recommendations.append("睡眠血糖控制优秀，继续保持！")
        elif quality["quality"] == "良好":
            recommendations.append("睡眠血糖控制良好，小幅调整即可")
        
        if not recommendations:
            recommendations.append("睡眠血糖控制正常")
        
        return recommendations
    
    def get_full_analysis(self) -> Dict:
        """完整分析"""
        metrics = self.calculate_metrics()
        quality = self.assess_sleep_quality()
        recs = self.generate_recommendations()
        
        return {
            "metrics": metrics,
            "quality": quality,
            "recommendations": recs
        }


# ============ 便捷函数 ============

def analyze_exercise(exercise_type: str, duration_minutes: int, 
                     start_time: datetime, cgm_data: pd.DataFrame) -> Dict:
    """分析运动血糖影响"""
    exercise = ExerciseEvent(exercise_type, duration_minutes, start_time)
    analysis = ExerciseAnalysis(exercise, cgm_data)
    return analysis.get_full_analysis()


def analyze_sleep(sleep_time: datetime, wake_time: datetime, 
                  cgm_data: pd.DataFrame) -> Dict:
    """分析睡眠血糖"""
    sleep = SleepEvent(sleep_time, wake_time)
    analysis = SleepAnalysis(sleep, cgm_data)
    return analysis.get_full_analysis()
