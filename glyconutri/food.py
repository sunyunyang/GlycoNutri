"""
食物 GI/GL 计算模块
"""

# 常见食物 GI 值数据库
GI_DATABASE = {
    # 谷物类
    "米饭": 73,
    "白米饭": 73,
    "糙米饭": 68,
    "面条": 55,
    "白面包": 75,
    "全麦面包": 69,
    "馒头": 85,
    "粥": 69,
    "燕麦": 55,
    "麦片": 55,
    
    # 蔬菜类
    "土豆": 85,
    "红薯": 77,
    "南瓜": 75,
    "胡萝卜": 71,
    "西兰花": 15,
    "菠菜": 15,
    "番茄": 15,
    "黄瓜": 15,
    "茄子": 15,
    
    # 水果类
    "西瓜": 76,
    "菠萝": 66,
    "芒果": 56,
    "葡萄": 59,
    "香蕉": 51,
    "苹果": 36,
    "梨": 36,
    "橙子": 43,
    "草莓": 40,
    "葡萄柚": 25,
    
    # 奶制品
    "牛奶": 27,
    "酸奶": 14,
    "冰淇淋": 51,
    
    # 豆类
    "红豆": 26,
    "绿豆": 27,
    "黄豆": 18,
    "豆腐": 15,
    
    # 坚果类
    "花生": 13,
    "核桃": 15,
    "杏仁": 15,
    
    # 糖类
    "葡萄糖": 100,
    "蔗糖": 65,
    "果糖": 23,
    "乳糖": 46,
    
    # 饮料
    "可乐": 63,
    "橙汁": 50,
    
    # 其他
    "巧克力": 49,
    "蜂蜜": 61,
}


def get_gi(food_name: str) -> float:
    """查询食物的 GI 值"""
    # 精确匹配
    if food_name in GI_DATABASE:
        return GI_DATABASE[food_name]
    
    # 模糊匹配
    food_name = food_name.lower()
    for name, gi in GI_DATABASE.items():
        if food_name in name.lower() or name.lower() in food_name:
            return gi
    
    return None


def calculate_gl(gi: float, carbs: float) -> float:
    """计算升糖负荷 (GL)"""
    return (gi * carbs) / 100


def get_food_info(food_name: str, carbs: float = None) -> dict:
    """获取食物的完整营养信息"""
    gi = get_gi(food_name)
    if gi is None:
        return None
    
    result = {
        "name": food_name,
        "gi": gi,
        "gi_category": "低" if gi < 55 else "中" if gi < 70 else "高"
    }
    
    if carbs is not None:
        result["gl"] = calculate_gl(gi, carbs)
        result["gl_category"] = "低" if result["gl"] < 10 else "中" if result["gl"] < 20 else "高"
    
    return result
