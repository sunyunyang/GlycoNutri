"""
AI 教练模块
简单的血糖问答和建议
"""

from typing import Dict, List
import random


class AICoach:
    """AI 教练"""
    
    def __init__(self):
        self.context = []
        self.responses = {
            'greeting': [
                "你好！我是你的血糖管理教练，有什么可以帮你的？",
                "嗨！今天血糖控制得怎么样？",
            ],
            'high_glucose': [
                "血糖偏高时，建议多喝水，适当运动，避免高GI食物。",
                "高血糖时要注意补充水分，适当步行可以帮助降低血糖。",
                "餐后血糖高可以尝试下次减少主食量，增加蔬菜。",
            ],
            'low_glucose': [
                "低血糖很危险！立即补充15-20克碳水，如果汁、糖果。",
                "出现低血糖症状时赶紧补糖，优先选择快速吸收的碳水。",
                "夜间低血糖要特别注意，可以在睡前测一下血糖。",
            ],
            'exercise': [
                "运动可以帮助降低血糖，建议餐后1-2小时运动。",
                "运动前后测血糖，血糖>250或<70时避免运动。",
                "推荐运动：快走、游泳、骑自行车。",
            ],
            'meal': [
                "建议采用211饮食法：2份蔬菜+1份蛋白+1份主食。",
                "先吃菜，再吃肉，最后吃饭，可以减缓血糖上升。",
                "低GI食物有助于血糖稳定，如燕麦、糙米、绿叶蔬菜。",
            ],
            'medication': [
                "按时服药很重要，不要自行调整剂量。",
                "二甲双胍建议随餐服用，可以减少胃肠道反应。",
                "胰岛素注射要注意轮换注射部位。",
            ],
            'default': [
                "我理解你的情况。记得定期监测血糖，记录数据很重要。",
                "好的，保持良好的生活习惯对血糖控制很重要。",
                "坚持就是胜利！有任何问题随时问我。",
            ]
        }
    
    def chat(self, message: str) -> str:
        """对话"""
        message = message.lower()
        
        # 关键词匹配
        if any(w in message for w in ['你好', '嗨', 'hi', 'hello', '在吗']):
            return random.choice(self.responses['greeting'])
        
        elif any(w in message for w in ['高', '升高', '200', '180', '超标']):
            return random.choice(self.responses['high_glucose'])
        
        elif any(w in message for w in ['低', '低血糖', '70', '54', '头晕']):
            return random.choice(self.responses['low_glucose'])
        
        elif any(w in message for w in ['运动', '跑步', '走路', '锻炼']):
            return random.choice(self.responses['exercise'])
        
        elif any(w in message for w in ['吃', '饭', '餐', '食物', '饮食']):
            return random.choice(self.responses['meal'])
        
        elif any(w in message for w in ['药', '胰岛素', '二甲双胍', '注射']):
            return random.choice(self.responses['medication'])
        
        else:
            return random.choice(self.responses['default'])
    
    def get_suggestion(self, glucose: float, context: str = '') -> str:
        """根据血糖值给出建议"""
        if glucose < 54:
            return "⚠️ 危险低血糖！立即补糖！建议摄入15-20克快速碳水，如果汁、糖果。"
        elif glucose < 70:
            return "⚠️ 低血糖预警！建议补充碳水，避免危险。"
        elif glucose < 80:
            return "血糖偏低但还可接受，注意监测。"
        elif glucose <= 140:
            return "✓ 血糖正常范围，继续保持！"
        elif glucose <= 180:
            return "血糖偏高，建议多喝水，适当运动。"
        elif glucose <= 250:
            return "⚠️ 高血糖！注意餐后血糖控制，减少碳水摄入。"
        else:
            return "⚠️ 危险高血糖！建议立即就医或注射胰岛素。"


def chat(message: str) -> str:
    """对话"""
    coach = AICoach()
    return coach.chat(message)


def get_suggestion(glucose: float, context: str = '') -> str:
    """获取建议"""
    coach = AICoach()
    return coach.get_suggestion(glucose, context)
