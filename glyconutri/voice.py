"""
语音输入模块
使用 Faster Whisper 进行本地语音识别
"""

import os
import tempfile
from typing import Dict, Optional
from faster_whisper import WhisperModel


class VoiceInput:
    """语音输入处理"""
    
    def __init__(self, model_size: str = "base"):
        """
        初始化语音模型
        
        Args:
            model_size: 模型大小 (tiny, base, small, medium, large-v3)
        """
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            # 使用 CPU
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8"
            )
            print(f"✓ Whisper model '{self.model_size}' loaded")
        except Exception as e:
            print(f"✗ Failed to load model: {e}")
            self.model = None
    
    def transcribe_audio(self, audio_path: str, language: str = "zh") -> Dict:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码 (zh, en, auto)
        
        Returns:
            转录结果字典
        """
        if not self.model:
            return {"error": "模型未加载", "text": ""}
        
        try:
            # 转录
            segments, info = self.model.transcribe(
                audio_path,
                language=language if language != "auto" else None,
                beam_size=5,
                vad_filter=True
            )
            
            # 收集所有片段
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
            
            full_text = "".join(text_parts).strip()
            
            return {
                "text": full_text,
                "language": info.language if hasattr(info, 'language') else language,
                "language_probability": info.language_probability if hasattr(info, 'language_probability') else 0,
                "duration": info.duration if hasattr(info, 'duration') else 0
            }
            
        except Exception as e:
            return {"error": str(e), "text": ""}
    
    def transcribe_bytes(self, audio_bytes: bytes, language: str = "zh") -> Dict:
        """
        转录字节数据
        
        Args:
            audio_bytes: 音频字节数据
            language: 语言代码
        """
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        try:
            result = self.transcribe_audio(temp_path, language)
            return result
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_path)
            except:
                pass


class VoiceMealParser:
    """语音餐食解析"""
    
    def __init__(self):
        from glyconutri.nutrition import NUTRITION_DATABASE
        self.food_db = NUTRITION_DATABASE
    
    def parse_meal_description(self, text: str) -> Dict:
        """
        解析餐食描述文本
        
        Args:
            text: 语音转录的文本
        
        Returns:
            识别的食物和营养估算
        """
        text = text.lower()
        found_foods = []
        
        # 常见食物关键词
        keywords = {
            "米饭": "米饭",
            "粥": "白粥",
            "面条": "面条",
            "馒头": "馒头",
            "面包": "面包",
            "牛奶": "牛奶",
            "豆浆": "豆浆",
            "鸡蛋": "鸡蛋",
            "肉": "猪肉",
            "鱼": "鱼肉",
            "虾": "虾",
            "蔬菜": "青菜",
            "苹果": "苹果",
            "香蕉": "香蕉",
            "橙子": "橙子",
            "奶茶": "奶茶",
            "咖啡": "咖啡",
            "可乐": "可乐",
            "啤酒": "啤酒",
            "白酒": "白酒",
        }
        
        for keyword, food_name in keywords.items():
            if keyword in text:
                # 尝试提取数量
                quantity = self._extract_quantity(text, keyword)
                
                food_data = self.food_db.get(food_name, {})
                
                if food_data:
                    carbs = food_data.get('carbs', 0) * quantity
                    gi = food_data.get('gi', 50)
                    
                    found_foods.append({
                        "name": food_name,
                        "quantity": quantity,
                        "carbs": round(carbs, 1),
                        "gi": gi,
                        "gl": round(carbs * gi / 100, 1)
                    })
        
        # 计算总计
        total_carbs = sum(f['carbs'] for f in found_foods)
        weighted_gi = sum(f['carbs'] * f['gi'] for f in found_foods) / total_carbs if total_carbs > 0 else 0
        total_gl = sum(f['gl'] for f in found_foods)
        
        return {
            "raw_text": text,
            "foods": found_foods,
            "total_carbs": round(total_carbs, 1),
            "estimated_gi": round(weighted_gi, 1),
            "estimated_gl": round(total_gl, 1),
            "meal_type": self._detect_meal_type(text)
        }
    
    def _extract_quantity(self, text: str, keyword: str) -> float:
        """提取数量"""
        import re
        
        # 尝试匹配 "X碗", "X个", "X杯" 等
        patterns = [
            rf'(\d+(?:\.\d+)?)\s*[碗个杯盘份]?{keyword}',
            rf'{keyword}\s*(\d+(?:\.\d+)?)\s*[碗个杯盘份]?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        
        return 1.0  # 默认1份
    
    def _detect_meal_type(self, text: str) -> str:
        """检测餐型"""
        if any(w in text for w in ['早餐', '早', '早上']):
            return "breakfast"
        elif any(w in text for w in ['午餐', '中餐', '中午']):
            return "lunch"
        elif any(w in text for w in ['晚餐', '晚', '晚上']):
            return "dinner"
        elif any(w in text for w in ['零食', '加餐', '宵夜']):
            return "snack"
        return "unknown"


# 全局实例
_voice_input: Optional[VoiceInput] = None


def get_voice_input(model_size: str = "base") -> VoiceInput:
    """获取语音输入实例"""
    global _voice_input
    if _voice_input is None:
        _voice_input = VoiceInput(model_size)
    return _voice_input


def transcribe(audio_path: str, language: str = "zh") -> Dict:
    """转录音频"""
    voice = get_voice_input()
    return voice.transcribe_audio(audio_path, language)


def parse_meal_from_speech(text: str) -> Dict:
    """从语音转录文本解析餐食"""
    parser = VoiceMealParser()
    return parser.parse_meal_description(text)
