"""
机器学习预测模块
血糖预测、预警算法、推荐算法
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class GlucosePredictor:
    """血糖预测模型"""
    
    def __init__(self, cgm_data: pd.DataFrame):
        self.cgm_data = cgm_data.sort_values('timestamp')
        self.scaler = StandardScaler()
        self.model = None
        self._train_model()
    
    def _prepare_features(self, window_minutes: int = 60) -> tuple:
        """准备特征"""
        df = self.cgm_data.copy()
        df = df.set_index('timestamp')
        
        # 重采样到 5 分钟间隔
        df = df.resample('5min').mean().dropna()
        
        features = []
        targets = []
        
        for i in range(window_minutes // 5, len(df)):
            # 过去 window_minutes 的数据作为特征
            window = df.iloc[i - window_minutes // 5:i]
            
            if len(window) < window_minutes // 5 * 0.8:
                continue
            
            # 特征: 统计量
            feat = [
                window['glucose'].mean(),
                window['glucose'].std(),
                window['glucose'].min(),
                window['glucose'].max(),
                window['glucose'].iloc[-1],  # 最新值
                window['glucose'].iloc[0],    # 最旧值
                window['glucose'].diff().mean(),  # 平均变化
            ]
            
            # 目标: 30分钟后血糖
            if i < len(df):
                target = df.iloc[i]['glucose']
                features.append(feat)
                targets.append(target)
        
        return np.array(features), np.array(targets)
    
    def _train_model(self):
        """训练模型"""
        try:
            X, y = self._prepare_features()
            
            if len(X) < 20:
                self.model = None
                return
            
            # 标准化
            X_scaled = self.scaler.fit_transform(X)
            
            # 训练线性回归
            self.model = LinearRegression()
            self.model.fit(X_scaled, y)
            
        except Exception as e:
            self.model = None
    
    def predict_next(self, minutes: int = 30) -> Dict:
        """预测未来血糖"""
        if self.model is None:
            return {'error': '数据不足，无法预测'}
        
        # 使用最近的数据
        recent = self.cgm_data.tail(12)  # 最近 60 分钟 (5分钟间隔)
        
        if len(recent) < 6:
            return {'error': '数据不足，需要更多历史数据'}
        
        # 提取特征
        feat = [
            recent['glucose'].mean(),
            recent['glucose'].std(),
            recent['glucose'].min(),
            recent['glucose'].max(),
            recent['glucose'].iloc[-1],
            recent['glucose'].iloc[0],
            recent['glucose'].diff().mean()
        ]
        
        # 预测
        X = self.scaler.transform([feat])
        prediction = self.model.predict(X)[0]
        
        # 计算置信区间 (简化版)
        std_error = self.cgm_data['glucose'].std() * 0.1
        
        return {
            'prediction': round(prediction, 1),
            'unit': 'mg/dL',
            'time_ahead_minutes': minutes,
            'confidence_interval': {
                'lower': round(prediction - 1.96 * std_error, 1),
                'upper': round(prediction + 1.96 * std_error, 1)
            },
            'current': round(recent['glucose'].iloc[-1], 1),
            'trend': '上升' if prediction > recent['glucose'].iloc[-1] + 10 else '下降' if prediction < recent['glucose'].iloc[-1] - 10 else '稳定'
        }
    
    def predict_trajectory(self, hours: int = 2) -> Dict:
        """预测血糖轨迹"""
        predictions = []
        
        current_data = self.cgm_data.copy()
        
        for minutes in range(30, hours * 60 + 1, 30):
            if len(current_data) < 6:
                break
            
            # 重新训练最近数据
            temp_predictor = GlucosePredictor(current_data)
            pred = temp_predictor.predict_next(minutes)
            
            if 'error' not in pred:
                predictions.append({
                    'minutes': minutes,
                    'glucose': pred['prediction']
                })
            
            # 添加预测点到数据 (简化)
            new_row = pd.DataFrame({
                'timestamp': [current_data['timestamp'].max() + timedelta(minutes=30)],
                'glucose': [pred.get('prediction', current_data['glucose'].mean())]
            })
            current_data = pd.concat([current_data, new_row], ignore_index=True)
        
        return {'trajectory': predictions}


class GlucoseAlert:
    """血糖预警"""
    
    def __init__(self, cgm_data: pd.DataFrame, settings: Dict = None):
        self.cgm_data = cgm_data.sort_values('timestamp')
        self.settings = settings or {
            'low_threshold': 70,
            'high_threshold': 180,
            'very_low': 54,
            'very_high': 250
        }
    
    def check_current_status(self) -> Dict:
        """检查当前状态"""
        latest = self.cgm_data.iloc[-1]
        glucose = latest['glucose']
        
        status = 'normal'
        level = 'info'
        
        if glucose < self.settings['very_low']:
            status = 'critical_low'
            level = 'critical'
        elif glucose < self.settings['low_threshold']:
            status = 'low'
            level = 'warning'
        elif glucose > self.settings['very_high']:
            status = 'critical_high'
            level = 'critical'
        elif glucose > self.settings['high_threshold']:
            status = 'high'
            level = 'warning'
        
        return {
            'status': status,
            'level': level,
            'glucose': glucose,
            'timestamp': latest['timestamp'].isoformat(),
            'message': self._get_message(status)
        }
    
    def _get_message(self, status: str) -> str:
        """获取消息"""
        messages = {
            'critical_low': '⚠️ 危险低血糖！立即补糖！',
            'low': '低血糖提醒',
            'critical_high': '⚠️ 危险高血糖！立即处理！',
            'high': '高血糖提醒',
            'normal': '血糖正常'
        }
        return messages.get(status, '')
    
    def predict_low_risk(self) -> Dict:
        """预测低血糖风险"""
        recent = self.cgm_data.tail(12)  # 最近 1 小时
        
        if len(recent) < 4:
            return {'risk': 'unknown'}
        
        # 趋势分析
        glucose_values = recent['glucose'].values
        slope = np.polyfit(range(len(glucose_values)), glucose_values, 1)[0]
        
        # 当前值
        current = recent['glucose'].iloc[-1]
        
        # 风险评估
        risk = 'low'
        if current < 80 or (current < 100 and slope < -2):
            risk = 'high'
        elif current < 90 or slope < -1:
            risk = 'medium'
        
        return {
            'risk': risk,
            'current': current,
            'trend': slope,
            'message': self._get_risk_message(risk)
        }
    
    def _get_risk_message(self, risk: str) -> str:
        """风险消息"""
        messages = {
            'high': '低血糖风险高，建议立即补充碳水',
            'medium': '注意下降趋势，可能出现低血糖',
            'low': '目前低血糖风险较低'
        }
        return messages.get(risk, '')
    
    def check_all_alerts(self) -> Dict:
        """检查所有预警"""
        return {
            'current_status': self.check_current_status(),
            'low_risk': self.predict_low_risk()
        }


class MealRecommendation:
    """餐食推荐"""
    
    def __init__(self):
        from glyconutri.nutrition import NUTRITION_DATABASE
        self.food_db = NUTRITION_DATABASE
    
    def recommend_by_time(self, current_glucose: float, time_of_day: int) -> Dict:
        """根据时间和当前血糖推荐"""
        suggestions = []
        
        # 根据时间推荐
        if 6 <= time_of_day < 10:
            # 早餐
            suggestions.append('建议选择低GI主食，如燕麦、糙米')
            suggestions.append('搭配蛋白质延缓血糖上升')
        elif 11 <= time_of_day < 13:
            # 午餐
            suggestions.append('主食适量，蔬菜为主')
            suggestions.append('避免高GI食物搭配')
        elif 17 <= time_of_day < 19:
            # 晚餐
            suggestions.append('晚餐宜清淡，少量主食')
            suggestions.append('注意餐后血糖监测')
        else:
            suggestions.append('非用餐时间，注意零食选择')
        
        # 根据血糖调整
        if current_glucose > 180:
            suggestions.insert(0, '⚠️ 当前血糖偏高，建议选择低GI食物')
        elif current_glucose < 80:
            suggestions.insert(0, '⚠️ 当前血糖偏低，建议先补充碳水')
        
        return {
            'time_period': self._get_time_period(time_of_day),
            'current_glucose': current_glucose,
            'recommendations': suggestions
        }
    
    def _get_time_period(self, hour: int) -> str:
        """获取时间段"""
        if 6 <= hour < 10:
            return '早餐时间'
        elif 10 <= hour < 12:
            return '上午'
        elif 12 <= hour < 14:
            return '午餐时间'
        elif 14 <= hour < 17:
            return '下午'
        elif 17 <= hour < 20:
            return '晚餐时间'
        else:
            return '晚间'
    
    def find_low_gi_alternatives(self, food_name: str) -> List[Dict]:
        """寻找低GI替代食物"""
        target_gi = self.food_db.get(food_name, {}).get('gi', 50)
        
        alternatives = []
        for name, data in self.food_db.items():
            if data.get('gi', 100) < target_gi and data.get('gi', 0) > 0:
                alternatives.append({
                    'name': name,
                    'gi': data['gi'],
                    'carbs': data.get('carbs', 0)
                })
        
        # 返回最低GI的5个
        alternatives.sort(key=lambda x: x['gi'])
        return alternatives[:5]


# ============ 便捷函数 ============

def predict_glucose(cgm_data: pd.DataFrame, minutes: int = 30) -> Dict:
    """预测血糖"""
    predictor = GlucosePredictor(cgm_data)
    return predictor.predict_next(minutes)


def get_alerts(cgm_data: pd.DataFrame, settings: Dict = None) -> Dict:
    """获取预警"""
    alert = GlucoseAlert(cgm_data, settings)
    return alert.check_all_alerts()


def get_meal_recommendation(current_glucose: float = 100, hour: int = None) -> Dict:
    """获取餐食推荐"""
    hour = hour or datetime.now().hour
    recommender = MealRecommendation()
    return recommender.recommend_by_time(current_glucose, hour)
