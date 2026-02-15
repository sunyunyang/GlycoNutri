"""
测试 CGM 数据解析
"""

import pytest
import pandas as pd
from io import StringIO


def parse_cgm_data(text):
    """模拟解析逻辑"""
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith('#')]
    
    if not lines:
        return None, "数据为空"
    
    first_line = lines[0]
    if '\t' in first_line:
        df = pd.read_csv(StringIO(text), sep='\t', on_bad_lines='skip')
    elif ',' in first_line:
        df = pd.read_csv(StringIO(text), on_bad_lines='skip')
    else:
        df = pd.read_csv(StringIO(text), sep=r'\s+', on_bad_lines='skip')
    
    time_col = next((c for c in df.columns if any(k in c.lower() for k in ['time', 'date', 'timestamp'])), None)
    glucose_col = next((c for c in df.columns if any(k in c.lower() for k in ['glucose', 'value', 'sg', '血糖', 'mg'])), None)
    
    if not time_col or not glucose_col:
        return None, f"未找到时间或血糖列。检测到的列: {list(df.columns)}"
    
    return df, None


def test_csv_standard():
    """测试标准 CSV 格式"""
    text = """timestamp,glucose
2026-02-15 07:00,92
2026-02-15 07:15,94"""
    df, err = parse_cgm_data(text)
    assert err is None
    assert len(df) == 2
    assert 'glucose' in df.columns


def test_csv_chinese_header():
    """测试中文列名"""
    text = """时间,血糖
2026-02-15 07:00,92
2026-02-15 07:15,94"""
    df, err = parse_cgm_data(text)
    assert err is None
    assert len(df) == 2


def test_csv_dexcom():
    """测试 Dexcom 格式"""
    text = """ExportDate,GlucoseValue,DisplayTime
2026-02-15 07:00,92,2026-02-15 07:00"""
    df, err = parse_cgm_data(text)
    assert err is None
    assert len(df) == 1


def test_csv_libre():
    """测试 Libre 格式"""
    text = """History,Scan, glucose
2026-02-15 07:00,2026-02-15 07:00,92"""
    df, err = parse_cgm_data(text)
    # Libre 格式复杂，可能需要特殊处理


def test_tsv_tab():
    """测试 TAB 分隔"""
    text = "timestamp\tglucose\n2026-02-15 07:00\t92"
    df, err = parse_cgm_data(text)
    assert err is None


def test_space_separated():
    """测试空格分隔"""
    text = "timestamp glucose\n2026-02-15 07:00 92"
    df, err = parse_cgm_data(text)
    assert err is None


def test_with_comments():
    """测试带注释"""
    text = """# Comment
timestamp,glucose
2026-02-15 07:00,92"""
    df, err = parse_cgm_data(text)
    assert err is None
    assert len(df) == 1


def test_bad_line():
    """测试错误行"""
    text = """timestamp,glucose
2026-02-15 07:00,92,extra
2026-02-15 07:15,94"""
    df, err = parse_cgm_data(text)
    # 应该跳过错误行
    assert df is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
