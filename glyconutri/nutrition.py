"""
食物营养数据库 - 扩展版
包含 GI、碳水、蛋白质、脂肪、纤维
"""

# 食物营养数据 (每 100g)
# 格式: {名称: {gi: GI值, carbs: 碳水(g), protein: 蛋白(g), fat: 脂肪(g), fiber: 纤维(g)}}

NUTRITION_DATABASE = {
    # ===== 谷物类 =====
    "米饭": {"gi": 73, "carbs": 28, "protein": 2.6, "fat": 0.3, "fiber": 0.4},
    "白米饭": {"gi": 73, "carbs": 28, "protein": 2.6, "fat": 0.3, "fiber": 0.4},
    "糙米饭": {"gi": 68, "carbs": 23, "protein": 2.7, "fat": 0.8, "fiber": 1.8},
    "黑米饭": {"gi": 65, "carbs": 25, "protein": 3, "fat": 0.9, "fiber": 1.7},
    "藜麦": {"gi": 53, "carbs": 21, "protein": 4.4, "fat": 1.9, "fiber": 2.8},
    "面条": {"gi": 55, "carbs": 25, "protein": 5, "fat": 0.5, "fiber": 1.2},
    "意面": {"gi": 49, "carbs": 31, "protein": 5, "fat": 0.9, "fiber": 1.8},
    "白面包": {"gi": 75, "carbs": 49, "protein": 9, "fat": 3.2, "fiber": 2.7},
    "全麦面包": {"gi": 69, "carbs": 43, "protein": 13, "fat": 3.4, "fiber": 7},
    "法棍": {"gi": 95, "carbs": 56, "protein": 8, "fat": 1.5, "fiber": 2.7},
    "馒头": {"gi": 85, "carbs": 47, "protein": 7, "fat": 1, "fiber": 1.5},
    "花卷": {"gi": 88, "carbs": 45, "protein": 6, "fat": 1.5, "fiber": 1.2},
    "包子": {"gi": 89, "carbs": 42, "protein": 8, "fat": 3, "fiber": 1.4},
    "饺子": {"gi": 88, "carbs": 40, "protein": 8, "fat": 4, "fiber": 1.2},
    "粥": {"gi": 69, "carbs": 13, "protein": 1.5, "fat": 0.3, "fiber": 0.5},
    "燕麦": {"gi": 55, "carbs": 66, "protein": 17, "fat": 7, "fiber": 11},
    "麦片": {"gi": 55, "carbs": 66, "protein": 15, "fat": 6, "fiber": 10},
    "玉米": {"gi": 52, "carbs": 22, "protein": 3.3, "fat": 1.2, "fiber": 2.7},
    "小米": {"gi": 71, "carbs": 75, "protein": 9, "fat": 3, "fiber": 4},
    "高粱": {"gi": 54, "carbs": 74, "protein": 10, "fat": 3, "fiber": 4},
    "荞麦": {"gi": 54, "carbs": 71, "protein": 13, "fat": 2.5, "fiber": 12},
    
    # ===== 蔬菜类 =====
    "土豆": {"gi": 85, "carbs": 17, "protein": 2, "fat": 0.1, "fiber": 2.2},
    "炸薯条": {"gi": 75, "carbs": 33, "protein": 3.4, "fat": 15, "fiber": 3},
    "红薯": {"gi": 77, "carbs": 20, "protein": 1.6, "fat": 0.1, "fiber": 3},
    "蒸红薯": {"gi": 63, "carbs": 20, "protein": 1.6, "fat": 0.1, "fiber": 3},
    "南瓜": {"gi": 75, "carbs": 7, "protein": 1, "fat": 0.1, "fiber": 0.8},
    "胡萝卜": {"gi": 71, "carbs": 10, "protein": 0.9, "fat": 0.2, "fiber": 2.8},
    "西兰花": {"gi": 15, "carbs": 7, "protein": 2.8, "fat": 0.4, "fiber": 2.6},
    "菠菜": {"gi": 15, "carbs": 3.6, "protein": 2.9, "fat": 0.4, "fiber": 2.2},
    "番茄": {"gi": 15, "carbs": 3.9, "protein": 0.9, "fat": 0.2, "fiber": 1.2},
    "黄瓜": {"gi": 15, "carbs": 2.4, "protein": 0.8, "fat": 0.2, "fiber": 0.7},
    "茄子": {"gi": 15, "carbs": 5, "protein": 1, "fat": 0.2, "fiber": 2.5},
    "青椒": {"gi": 15, "carbs": 6, "protein": 1, "fat": 0.3, "fiber": 2.1},
    "生菜": {"gi": 15, "carbs": 3, "protein": 1.4, "fat": 0.2, "fiber": 1.3},
    "白菜": {"gi": 15, "carbs": 3, "protein": 1.5, "fat": 0.1, "fiber": 1},
    
    # ===== 水果类 =====
    "苹果": {"gi": 36, "carbs": 14, "protein": 0.3, "fat": 0.2, "fiber": 2.4},
    "香蕉": {"gi": 51, "carbs": 23, "protein": 1.1, "fat": 0.3, "fiber": 2.6},
    "橙子": {"gi": 43, "carbs": 12, "protein": 0.9, "fat": 0.1, "fiber": 2.4},
    "葡萄": {"gi": 59, "carbs": 18, "protein": 0.7, "fat": 0.2, "fiber": 0.9},
    "西瓜": {"gi": 72, "carbs": 8, "protein": 0.6, "fat": 0.2, "fiber": 0.4},
    "梨": {"gi": 38, "carbs": 13, "protein": 0.3, "fat": 0.1, "fiber": 3.1},
    "桃子": {"gi": 42, "carbs": 12, "protein": 0.9, "fat": 0.3, "fiber": 2.3},
    "草莓": {"gi": 40, "carbs": 8, "protein": 0.7, "fat": 0.3, "fiber": 2},
    "猕猴桃": {"gi": 39, "carbs": 15, "protein": 1.1, "fat": 0.5, "fiber": 3},
    "芒果": {"gi": 51, "carbs": 15, "protein": 0.8, "fat": 0.4, "fiber": 1.6},
    "菠萝": {"gi": 59, "carbs": 13, "protein": 0.5, "fat": 0.1, "fiber": 1.4},
    "柚子": {"gi": 25, "carbs": 9, "protein": 0.8, "fat": 0.1, "fiber": 1.1},
    
    # ===== 蛋白质类 =====
    "鸡胸肉": {"gi": 0, "carbs": 0, "protein": 31, "fat": 3.6, "fiber": 0},
    "鸡腿": {"gi": 0, "carbs": 0, "protein": 26, "fat": 8, "fiber": 0},
    "牛肉": {"gi": 0, "carbs": 0, "protein": 26, "fat": 15, "fiber": 0},
    "猪肉": {"gi": 0, "carbs": 0, "protein": 27, "fat": 13, "fiber": 0},
    "三文鱼": {"gi": 0, "carbs": 0, "protein": 20, "fat": 13, "fiber": 0},
    "金枪鱼": {"gi": 0, "carbs": 0, "protein": 30, "fat": 1, "fiber": 0},
    "虾": {"gi": 0, "carbs": 0.2, "protein": 24, "fat": 0.3, "fiber": 0},
    "鸡蛋": {"gi": 0, "carbs": 1.1, "protein": 13, "fat": 11, "fiber": 0},
    "豆腐": {"gi": 15, "carbs": 4, "protein": 8, "fat": 4, "fiber": 0.3},
    "豆浆": {"gi": 15, "carbs": 3, "protein": 3, "fat": 1.8, "fiber": 0.5},
    "牛奶": {"gi": 27, "carbs": 5, "protein": 3.4, "fat": 3.9, "fiber": 0},
    "酸奶": {"gi": 33, "carbs": 12, "protein": 3, "fat": 3, "fiber": 0},
    
    # ===== 坚果类 =====
    "花生": {"gi": 13, "carbs": 20, "protein": 26, "fat": 49, "fiber": 8.5},
    "杏仁": {"gi": 0, "carbs": 22, "protein": 21, "fat": 49, "fiber": 12},
    "核桃": {"gi": 15, "carbs": 14, "protein": 15, "fat": 65, "fiber": 7},
    "腰果": {"gi": 25, "carbs": 30, "protein": 18, "fat": 44, "fiber": 3},
    "芝麻": {"gi": 35, "carbs": 23, "protein": 18, "fat": 50, "fiber": 12},
    
    # ===== 饮品/其他 =====
    "可乐": {"gi": 63, "carbs": 11, "protein": 0, "fat": 0, "fiber": 0},
    "橙汁": {"gi": 50, "carbs": 10, "protein": 0.7, "fat": 0.2, "fiber": 0.2},
    "蜂蜜": {"gi": 61, "carbs": 82, "protein": 0.3, "fat": 0, "fiber": 0.2},
    "白砂糖": {"gi": 65, "carbs": 100, "protein": 0, "fat": 0, "fiber": 0},
}


def get_nutrition(food_name: str) -> dict:
    """获取食物营养信息"""
    return NUTRITION_DATABASE.get(food_name)


def get_all_foods() -> list:
    """获取所有食物列表"""
    return list(NUTRITION_DATABASE.keys())


# 向后兼容: GI 映射
GI_MAP = {name: data['gi'] for name, data in NUTRITION_DATABASE.items()}
CARBS_MAP = {name: data['carbs'] for name, data in NUTRITION_DATABASE.items()}
