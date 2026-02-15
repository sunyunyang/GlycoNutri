"""
测试 CGM 数据处理模块
"""

import pandas as pd
from glyconutri.cgm import calculate_tir, calculate_gv


def test_calculate_tir():
    """测试 TIR 计算"""
    # 模拟数据: 70% 在范围内 (70-140)
    df = pd.DataFrame({
        'glucose': [80, 90, 100, 110, 120, 130, 150, 160, 170, 180]
    })
    
    tir = calculate_tir(df)
    assert tir == 60.0, f"Expected 60.0, got {tir}"
    print("✓ TIR 计算测试通过")


def test_calculate_gv():
    """测试血糖波动计算"""
    df = pd.DataFrame({
        'glucose': [100, 110, 120, 130, 140]
    })
    
    gv = calculate_gv(df)
    assert gv > 0, "GV should be positive"
    print(f"✓ GV 计算测试通过: {gv:.1f}%")


if __name__ == '__main__':
    test_calculate_tir()
    test_calculate_gv()
    print("\n所有测试通过! ✓")
