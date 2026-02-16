"""
图片食物识别模块
使用阿里云图像识别或本地模型进行食物分类
"""

import base64
import io
from typing import Dict, List, Optional
from PIL import Image
import numpy as np


class FoodImageRecognizer:
    """食物图片识别器"""
    
    def __init__(self, use_cloud: bool = False):
        """
        初始化识别器
        
        Args:
            use_cloud: 是否使用云服务 (默认本地模式)
        """
        self.use_cloud = use_cloud
        self.local_model = None
        
        if not use_cloud:
            self._init_local_model()
    
    def _init_local_model(self):
        """初始化本地模型 (简化版)"""
        # 本地使用颜色和形状特征进行简单分类
        # 实际生产中可替换为 TensorFlow Lite 模型
        self.food_features = {
            'rice': {'color_range': [(200, 255), (180, 220), (150, 200)], 'shape': 'grain'},
            'noodle': {'color_range': [(220, 255), (200, 240), (180, 220)], 'shape': 'long'},
            'vegetable': {'color_range': [(0, 150), (100, 200), (0, 100)], 'shape': 'irregular'},
            'meat': {'color_range': [(100, 180), (50, 100), (30, 80)], 'shape': 'irregular'},
            'fruit': {'color_range': [(150, 255), (100, 200), (50, 150)], 'shape': 'round'},
            'bread': {'color_range': [(180, 240), (150, 200), (100, 160)], 'shape': 'block'},
            'egg': {'color_range': [(200, 255), (200, 255), (180, 220)], 'shape': 'oval'},
            'milk': {'color_range': [(220, 255), (220, 255), (220, 255)], 'shape': 'liquid'},
        }
        print("✓ Food recognizer initialized (local mode)")
    
    def recognize_from_file(self, image_path: str) -> Dict:
        """
        识别图片文件
        
        Args:
            image_path: 图片文件路径
        
        Returns:
            识别结果
        """
        try:
            img = Image.open(image_path)
            return self._recognize_image(img)
        except Exception as e:
            return {"error": str(e), "foods": []}
    
    def recognize_from_bytes(self, image_bytes: bytes) -> Dict:
        """
        识别字节数据
        
        Args:
            image_bytes: 图片字节数据
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return self._recognize_image(img)
        except Exception as e:
            return {"error": str(e), "foods": []}
    
    def recognize_from_base64(self, base64_str: str) -> Dict:
        """
        识别 Base64 编码的图片
        
        Args:
            base64_str: Base64 编码的图片字符串
        """
        try:
            # 移除 data URL 前缀
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            
            img_bytes = base64.b64decode(base64_str)
            return self.recognize_from_bytes(img_bytes)
        except Exception as e:
            return {"error": str(e), "foods": []}
    
    def _recognize_image(self, img: Image.Image) -> Dict:
        """识别图片"""
        # 转换为 RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 调整大小
        img = img.resize((224, 224))
        
        # 获取颜色特征
        img_array = np.array(img)
        avg_color = img_array.mean(axis=(0, 1))
        
        # 简单分类逻辑
        foods = self._classify_by_color(avg_color)
        
        # 估算营养
        nutrition = self._estimate_nutrition(foods)
        
        return {
            "foods": foods,
            "nutrition": nutrition,
            "confidence": 0.7,  # 本地模式置信度较低
            "method": "local" if not self.use_cloud else "cloud"
        }
    
    def _classify_by_color(self, avg_color: np.ndarray) -> List[Dict]:
        """根据颜色分类"""
        r, g, b = avg_color
        
        foods = []
        
        # 白色/浅色 - 米饭、面条、面包
        if r > 180 and g > 170 and b > 150:
            foods.append({"name": "米饭/面食", "confidence": 0.6})
        
        # 绿色 - 蔬菜
        if g > r and g > b and g - r > 30:
            foods.append({"name": "蔬菜", "confidence": 0.7})
        
        # 红色/橙色 - 水果、肉
        if r > g + 30 and r > b + 30:
            foods.append({"name": "水果/肉类", "confidence": 0.5})
        
        # 棕色 - 面包、肉类
        if r > 100 and r < 200 and g > 50 and g < 150 and b < 100:
            foods.append({"name": "肉类/面包", "confidence": 0.5})
        
        # 黄色 - 鸡蛋、奶制品
        if r > 200 and g > 200 and b < 180:
            foods.append({"name": "鸡蛋/奶制品", "confidence": 0.4})
        
        return foods[:3]  # 最多返回3个
    
    def _estimate_nutrition(self, foods: List[Dict]) -> Dict:
        """估算营养"""
        from glyconutri.nutrition import NUTRITION_DATABASE
        
        total_carbs = 0
        total_protein = 0
        total_fat = 0
        
        for food in foods:
            name = food['name']
            # 尝试匹配数据库
            for db_name, data in NUTRITION_DATABASE.items():
                if any(keyword in db_name for keyword in name.split('/')):
                    total_carbs += data.get('carbs', 20) * 0.5
                    total_protein += data.get('protein', 5) * 0.5
                    total_fat += data.get('fat', 3) * 0.5
                    break
        
        return {
            "carbs": round(total_carbs, 1),
            "protein": round(total_protein, 1),
            "fat": round(total_fat, 1),
            "calories": round(total_carbs * 4 + total_protein * 4 + total_fat * 9, 1)
        }


class CloudFoodRecognizer:
    """云端食物识别 (阿里云)"""
    
    def __init__(self, access_key: str = None, secret_key: str = None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint = "food detection endpoint"
    
    def recognize(self, image_path: str = None, image_bytes: bytes = None) -> Dict:
        """云端识别"""
        # 需要配置阿里云账户
        if not self.access_key:
            return {"error": "需要配置阿里云 AccessKey", "foods": []}
        
        # 实际调用阿里云 API
        # 此处为占位实现
        return {"error": "云端识别需要配置", "foods": []}


# 全局实例
_recognizer: Optional[FoodImageRecognizer] = None


def get_food_recognizer(use_cloud: bool = False) -> FoodImageRecognizer:
    """获取识别器实例"""
    global _recognizer
    if _recognizer is None:
        _recognizer = FoodImageRecognizer(use_cloud)
    return _recognizer


def recognize_food(image_path: str = None, image_bytes: bytes = None, base64_str: str = None) -> Dict:
    """识别食物图片"""
    recognizer = get_food_recognizer()
    
    if image_path:
        return recognizer.recognize_from_file(image_path)
    elif image_bytes:
        return recognizer.recognize_from_bytes(image_bytes)
    elif base64_str:
        return recognizer.recognize_from_base64(base64_str)
    
    return {"error": "需要提供图片", "foods": []}
