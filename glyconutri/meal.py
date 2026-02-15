"""
真实餐食分析模块
支持多种食物同时摄入的分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from glyconutri.nutrition import get_nutrition, NUTRITION_DATABASE


class FoodItem:
    """单种食物"""
    def __init__(self, name: str, weight: float, nutrition: dict = None):
        self.name = name
        self.weight = weight  # 克
        self.nutrition = nutrition or get_nutrition(name) or {}
        
    @property
    def carbs(self) -> float:
        """碳水 (g)"""
        per_100g = self.nutrition.get('carbs', 0)
        return per_100g * self.weight / 100
    
    @property
    def protein(self) -> float:
        """蛋白质 (g)"""
        per_100g = self.nutrition.get('protein', 0)
        return per_100g * self.weight / 100
    
    @property
    def fat(self) -> float:
        """脂肪 (g)"""
        per_100g = self.nutrition.get('fat', 0)
        return per_100g * self.weight / 100
    
    @property
    def fiber(self) -> float:
        """纤维 (g)"""
        per_100g = self.nutrition.get('fiber', 0)
        return per_100g * self.weight / 100
    
    @property
    def gi(self) -> float:
        """升糖指数"""
        return self.nutrition.get('gi', 0)
    
    @property
    def gl(self) -> float:
        """升糖负荷"""
        return (self.gi * self.carbs) / 100
    
    @property
    def calories(self) -> float:
        """热量 (kcal)"""
        return self.carbs * 4 + self.protein * 4 + self.fat * 9
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "weight": self.weight,
            "carbs": round(self.carbs, 1),
            "protein": round(self.protein, 1),
            "fat": round(self.fat, 1),
            "fiber": round(self.fiber, 1),
            "gi": self.gi,
            "gl": round(self.gl, 1),
            "calories": round(self.calories, 1)
        }


class Meal:
    """一餐（多种食物）"""
    
    def __init__(self, timestamp: datetime = None, name: str = "早餐"):
        self.timestamp = timestamp or datetime.now()
        self.name = name
        self.foods: List[FoodItem] = []
        
    def add_food(self, name: str, weight: float):
        """添加食物"""
        food = FoodItem(name, weight)
        self.foods.append(food)
        return food
    
    # ============ 营养汇总 ============
    
    @property
    def total_carbs(self) -> float:
        """总碳水 (g)"""
        return sum(f.carbs for f in self.foods)
    
    @property
    def total_protein(self) -> float:
        """总蛋白质 (g)"""
        return sum(f.protein for f in self.foods)
    
    @property
    def total_fat(self) -> float:
        """总脂肪 (g)"""
        return sum(f.fat for f in self.foods)
    
    @property
    def total_fiber(self) -> float:
        """总纤维 (g)"""
        return sum(f.fiber for f in self.foods)
    
    @property
    def total_calories(self) -> float:
        """总热量 (kcal)"""
        return sum(f.calories for f in self.foods)
    
    @property
    def weighted_gi(self) -> float:
        """加权 GI（按碳水权重）"""
        if self.total_carbs == 0:
            return 0
        return sum(f.gi * f.carbs for f in self.foods) / self.total_carbs
    
    @property
    def total_gl(self) -> float:
        """总 GL"""
        return sum(f.gl for f in self.foods)
    
    # ============ 膳食结构分析 ============
    
    def get_macro_ratio(self) -> dict:
        """宏量营养素比例 (% of calories)"""
        cals = self.total_calories
        if cals == 0:
            return {"carbs": 0, "protein": 0, "fat": 0}
        
        carbs_cals = self.total_carbs * 4
        protein_cals = self.total_protein * 4
        fat_cals = self.total_fat * 9
        
        return {
            "carbs": round(carbs_cals / cals * 100, 1),
            "protein": round(protein_cals / cals * 100, 1),
            "fat": round(fat_cals / cals * 100, 1)
        }
    
    def get_nutrition_balance(self) -> dict:
        """营养平衡评估"""
        ratio = self.get_macro_ratio()
        
        # 中国居民膳食指南推荐
        # 碳水 50-65%, 蛋白 10-15%, 脂肪 20-30%
        
        issues = []
        if ratio['carbs'] > 65:
            issues.append("碳水过高")
        elif ratio['carbs'] < 40:
            issues.append("碳水过低")
            
        if ratio['protein'] > 20:
            issues.append("蛋白质过高")
        elif ratio['protein'] < 10:
            issues.append("蛋白质过低")
            
        if ratio['fat'] > 35:
            issues.append("脂肪过高")
        elif ratio['fat'] < 15:
            issues.append("脂肪过低")
        
        return {
            "ratio": ratio,
            "issues": issues,
            "balance_score": max(0, 100 - len(issues) * 25)
        }
    
    # ============ 升糖效应分析 ============
    
    def glycemic_risk_assessment(self) -> dict:
        """升糖风险评估"""
        gl = self.total_gl
        weighted_gi = self.weighted_gi
        
        risk_level = "低"
        if gl > 40 or weighted_gi > 70:
            risk_level = "高"
        elif gl > 20 or weighted_gi > 55:
            risk_level = "中"
        
        return {
            "total_gl": round(gl, 1),
            "weighted_gi": round(weighted_gi, 1),
            "risk_level": risk_level,
            "recommendation": self._get_risk_recommendation(risk_level)
        }
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        if risk_level == "低":
            return "血糖响应较平稳，适合日常饮食"
        elif risk_level == "中":
            return "注意控制份量，建议搭配蔬菜和蛋白质"
        else:
            return "高升糖负荷，建议减少主食量，增加蔬菜"
    
    # ============ 食物顺序分析 ============
    
    def analyze_eating_order(self, order: List[str] = None) -> dict:
        """进食顺序分析
        
        Args:
            order: 食物进食顺序列表
        """
        if not order:
            # 默认: 蔬菜 → 蛋白质 → 主食 → 水果
            order = self._get_default_order()
        
        scores = []
        for i, food_name in enumerate(order):
            food = next((f for f in self.foods if f.name == food_name), None)
            if food:
                score = self._calculate_order_score(food, i, len(order))
                scores.append({
                    "food": food_name,
                    "order": i + 1,
                    "score": score,
                    "reason": self._get_order_reason(food, i)
                })
        
        total_score = sum(s['score'] for s in scores) / len(scores) if scores else 0
        
        return {
            "order": scores,
            "total_score": round(total_score, 1),
            "recommendation": self._get_order_recommendation(total_score)
        }
    
    def _get_default_order(self) -> List[str]:
        """获取默认推荐顺序"""
        # 蔬菜 → 蛋白质 → 主食 → 水果
        order = []
        for f in self.foods:
            gi = f.gi
            if gi < 20:  # 蔬菜
                order.insert(0, f.name)
            elif gi == 0:  # 蛋白质
                order.append(f.name)
            elif gi < 55:  # 中低GI
                order.append(f.name)
            else:  # 高GI
                order.append(f.name)
        return order
    
    def _calculate_order_score(self, food: FoodItem, position: int, total: int) -> float:
        """计算顺序得分"""
        gi = food.gi
        base_score = 100
        
        # 蔬菜类 (GI < 20) 应该在前面
        if gi < 20:
            return base_score if position < total / 3 else base_score * 0.6
        
        # 蛋白质 (GI = 0) 应该在中间
        if gi == 0:
            return base_score if total / 3 <= position < total * 2 / 3 else base_score * 0.7
        
        # 主食类应该在后面
        if gi >= 55:
            return base_score if position >= total * 2 / 3 else base_score * 0.6
        
        return base_score * 0.8
    
    def _get_order_reason(self, food: FoodItem, position: int) -> str:
        gi = food.gi
        if gi < 20:
            return "蔬菜纤维有助于延缓糖吸收"
        elif gi == 0:
            return "蛋白质有助于增加饱腹感"
        elif gi >= 55:
            return "主食放在后面可减缓血糖上升"
        return "中GI食物适量摄入"
    
    def _get_order_recommendation(self, score: float) -> str:
        if score >= 80:
            return "进食顺序合理，有助于血糖控制"
        elif score >= 60:
            return "建议调整进食顺序，先吃蔬菜"
        else:
            return "建议优化进食顺序，先菜后肉再主食"
    
    # ============ 膳食建议 ============
    
    def generate_recommendations(self) -> dict:
        """生成膳食建议"""
        recommendations = []
        
        # 营养结构
        balance = self.get_nutrition_balance()
        if balance['issues']:
            for issue in balance['issues']:
                recommendations.append({
                    "type": "nutrition",
                    "issue": issue,
                    "suggestion": self._get_nutrition_suggestion(issue)
                })
        
        # 升糖风险
        glycemic = self.glycemic_risk_assessment()
        if glycemic['risk_level'] != "低":
            recommendations.append({
                "type": "glycemic",
                "risk": glycemic['risk_level'],
                "suggestion": glycemic['recommendation']
            })
        
        # 纤维
        if self.total_fiber < 10:
            recommendations.append({
                "type": "fiber",
                "issue": "纤维摄入不足",
                "suggestion": "建议增加蔬菜摄入"
            })
        
        # 蛋白质
        if self.total_protein < 15:
            recommendations.append({
                "type": "protein",
                "issue": "蛋白质摄入偏低",
                "suggestion": "建议增加肉蛋奶豆制品"
            })
        
        return {
            "balance": balance,
            "glycemic": glycemic,
            "recommendations": recommendations,
            "summary": self._generate_summary(balance, glycemic)
        }
    
    def _get_nutrition_suggestion(self, issue: str) -> str:
        suggestions = {
            "碳水过高": "可适当减少主食量，用蔬菜代替",
            "碳水过低": "可适当增加主食摄入",
            "蛋白质过高": "注意控制肉类摄入量",
            "蛋白质过低": "建议增加优质蛋白摄入",
            "脂肪过高": "建议减少油炸食品摄入",
            "脂肪过低": "可适量增加坚果或油脂"
        }
        return suggestions.get(issue, "注意均衡饮食")
    
    def _generate_summary(self, balance: dict, glycemic: dict) -> str:
        parts = []
        
        if balance['balance_score'] >= 80:
            parts.append("营养均衡")
        elif balance['balance_score'] >= 60:
            parts.append("营养基本均衡")
        else:
            parts.append("需要注意营养搭配")
        
        if glycemic['risk_level'] == "低":
            parts.append("升糖风险低")
        elif glycemic['risk_level'] == "中":
            parts.append("升糖风险中等")
        else:
            parts.append("升糖风险较高")
        
        return "，".join(parts) + "。"
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
            "foods": [f.to_dict() for f in self.foods],
            "summary": {
                "total_carbs": round(self.total_carbs, 1),
                "total_protein": round(self.total_protein, 1),
                "total_fat": round(self.total_fat, 1),
                "total_fiber": round(self.total_fiber, 1),
                "total_calories": round(self.total_calories, 1),
                "weighted_gi": round(self.weighted_gi, 1),
                "total_gl": round(self.total_gl, 1)
            }
        }


# ============ 便捷函数 ============

def create_meal_from_dicts(foods: List[Dict], timestamp: datetime = None, name: str = "早餐") -> Meal:
    """从字典列表创建餐次
    
    Args:
        foods: [{"name": "米饭", "weight": 100}, {"name": "鸡胸肉", "weight": 50}]
        timestamp: 餐食时间
        name: 餐次名称
    
    Returns:
        Meal 对象
    """
    meal = Meal(timestamp, name)
    
    for food in foods:
        meal.add_food(food['name'], food.get('weight', 100))
    
    return meal


def analyze_meal(foods: List[Dict], timestamp: datetime = None, name: str = "早餐") -> dict:
    """分析一餐的完整信息
    
    Args:
        foods: 食物列表
        timestamp: 餐食时间
        name: 餐次名称
    
    Returns:
        完整分析结果
    """
    meal = create_meal_from_dicts(foods, timestamp, name)
    
    return {
        "meal": meal.to_dict(),
        "nutrition_balance": meal.get_nutrition_balance(),
        "glycemic_risk": meal.glycemic_risk_assessment(),
        "eating_order": meal.analyze_eating_order(),
        "recommendations": meal.generate_recommendations()
    }


# ============ 示例 ============

if __name__ == "__main__":
    # 示例：一餐的分析
    foods = [
        {"name": "米饭", "weight": 150},
        {"name": "鸡胸肉", "weight": 100},
        {"name": "西兰花", "weight": 100},
        {"name": "番茄", "weight": 50}
    ]
    
    result = analyze_meal(foods, name = "午餐")
    print(f"餐次: {result['meal']['name']}")
    print(f"总碳水: {result['meal']['summary']['total_carbs']}g")
    print(f"总GL: {result['meal']['summary']['total_gl']}")
    print(f"加权GI: {result['meal']['summary']['weighted_gi']}")
    print(f"营养平衡: {result['nutrition_balance']}")
    print(f"升糖风险: {result['glycemic_risk']}")
    print(f"建议: {result['recommendations']['summary']}")
