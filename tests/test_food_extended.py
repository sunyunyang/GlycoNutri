"""
测试食物 GI/GL 扩展功能
"""

from glyconutri.food import get_gi, calculate_gl, get_food_info, search_foods, list_foods_by_gi_category


def test_search_foods():
    """测试食物搜索"""
    results = search_foods("米")
    assert len(results) > 0, "应该能找到米饭相关食物"
    print(f"✓ 搜索'米'找到 {len(results)} 个结果")
    
    results = search_foods("apple")
    assert len(results) > 0, "应该能找到苹果"
    print(f"✓ 搜索'apple'找到 {len(results)} 个结果")


def test_list_by_category():
    """测试按类别列出食物"""
    low_gi = list_foods_by_gi_category("低")
    assert len(low_gi) > 0, "应该有低 GI 食物"
    print(f"✓ 低 GI 食物: {len(low_gi)} 个")
    
    high_gi = list_foods_by_gi_category("高")
    assert len(high_gi) > 0, "应该有高 GI 食物"
    print(f"✓ 高 GI 食物: {len(high_gi)} 个")


def test_get_food_info():
    """测试获取完整食物信息"""
    info = get_food_info("米饭")
    assert info is not None, "应该能找到米饭信息"
    assert info['gi'] == 73
    assert info['gi_category'] == "高"
    print(f"✓ 米饭信息: GI={info['gi']}, 类别={info['gi_category']}")


def test_gl_calculation():
    """测试 GL 计算"""
    # 米饭 100g (约28g碳水)
    gl = calculate_gl(73, 28)
    assert 20 < gl < 22, f"GL 应该约 20, 实际 {gl}"
    print(f"✓ 米饭 100g 的 GL: {gl:.1f}")


if __name__ == '__main__':
    test_search_foods()
    test_list_by_category()
    test_get_food_info()
    test_gl_calculation()
    print("\n所有测试通过! ✓")
