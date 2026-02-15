"""
食物 GI/GL 计算模块 - 扩展版
"""

from glyconutri.gi_database import GI_DATABASE, CARBS_DATABASE, get_carbs


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


def get_gi_category(gi: float) -> str:
    """根据 GI 值判断类别"""
    if gi < 55:
        return "低"
    elif gi < 70:
        return "中"
    else:
        return "高"


def calculate_gl(gi: float, carbs: float) -> float:
    """计算升糖负荷 (GL)"""
    return (gi * carbs) / 100


def get_gl_category(gl: float) -> str:
    """根据 GL 值判断类别"""
    if gl < 10:
        return "低"
    elif gl < 20:
        return "中"
    else:
        return "高"


def get_food_info(food_name: str, carbs: float = None) -> dict:
    """获取食物的完整营养信息"""
    gi = get_gi(food_name)
    if gi is None:
        return None
    
    # 如果未提供碳水，尝试从数据库获取
    if carbs is None:
        carbs = get_carbs(food_name)
    
    result = {
        "name": food_name,
        "gi": gi,
        "gi_category": get_gi_category(gi),
        "carbs_per_100g": carbs
    }
    
    if carbs is not None:
        result["gl"] = calculate_gl(gi, carbs)
        result["gl_category"] = get_gl_category(result["gl"])
    
    return result


def search_foods(keyword: str) -> list:
    """搜索食物"""
    keyword = keyword.lower()
    results = []
    for name, gi in GI_DATABASE.items():
        if keyword in name.lower():
            carbs = get_carbs(name)
            results.append({
                "name": name,
                "gi": gi,
                "gi_category": get_gi_category(gi),
                "carbs_per_100g": carbs
            })
    return results


def list_foods_by_gi_category(category: str) -> list:
    """按 GI 类别列出食物"""
    category = category.lower()
    results = []
    for name, gi in GI_DATABASE.items():
        cat = get_gi_category(gi).lower()
        if cat == category:
            carbs = get_carbs(name)
            results.append({
                "name": name,
                "gi": gi,
                "carbs_per_100g": carbs
            })
    return sorted(results, key=lambda x: x['gi'])
