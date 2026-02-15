"""
测试食物 GI/GL 计算模块
"""

from glyconutri.food import get_gi, calculate_gl, get_food_info


def test_get_gi():
    """测试 GI 查询"""
    assert get_gi("米饭") == 73
    assert get_gi("苹果") == 36
    assert get_gi("不存在的事物") is None
    print("✓ GI 查询测试通过")


def test_calculate_gl():
    """测试 GL 计算"""
    # GL = (GI × 碳水) / 100
    gl = calculate_gl(73, 30)  # 米饭 30g 碳水
    assert abs(gl - 21.9) < 0.1, f"Expected 21.9, got {gl}"
    print("✓ GL 计算测试通过")


def test_get_food_info():
    """测试食物信息获取"""
    info = get_food_info("米饭", carbs=30)
    assert info['gi'] == 73
    assert info['gl'] == 21.9
    assert info['gi_category'] == "高"
    print("✓ 食物信息测试通过")


if __name__ == '__main__':
    test_get_gi()
    test_calculate_gl()
ood_info()
       test_get_f print("\n所有测试通过! ✓")
