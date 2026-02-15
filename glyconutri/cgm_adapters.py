"""
CGM 设备适配器
支持 Dexcom, FreeStyle Libre, Medtronic 等主流 CGM 设备
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import re


class CGMDeviceAdapter:
    """CGM 设备适配器基类"""
    
    def parse(self, filepath: str) -> pd.DataFrame:
        """解析 CGM 数据文件"""
        raise NotImplementedError


class DexcomG6Adapter(CGMDeviceAdapter):
    """Dexcom G6 适配器"""
    
    def parse(self, filepath: str) -> pd.DataFrame:
        """解析 Dexcom G6 导出数据"""
        if filepath.endswith('.csv'):
            # Dexcom CSV 格式
            df = pd.read_csv(filepath)
            
            # 查找时间列和血糖列
            time_col = None
            glucose_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'timestamp' in col_lower or 'time' in col_lower or 'date' in col_lower:
                    time_col = col
                if 'glucose' in col_lower or 'sensor glucose' in col_lower or 'sg' in col_lower:
                    glucose_col = col
            
            if time_col and glucose_col:
                df['timestamp'] = pd.to_datetime(df[time_col])
                df['glucose'] = pd.to_numeric(df[glucose_col], errors='coerce')
                return df[['timestamp', 'glucose']].dropna()
            
        elif filepath.endswith('.json'):
            df = pd.read_json(filepath)
            return self._parse_json(df)
        
        raise ValueError("不支持的 Dexcom 文件格式")


class DexcomG7Adapter(CGMDeviceAdapter):
    """Dexcom G7 适配器"""
    
    def parse(self, filepath: str) -> pd.DataFrame:
        """解析 Dexcom G7 导出数据"""
        return DexcomG6Adapter().parse(filepath)  # G7 格式与 G6 相同


class FreeStyleLibreAdapter(CGMDeviceAdapter):
    """FreeStyle Libre 适配器"""
    
    def parse(self, filepath: str) -> pd.DataFrame:
        """解析 Libre 数据"""
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
            
            # Libre 通常有这些列名
            time_col = None
            glucose_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'timestamp' in col_lower or 'time' in col_lower:
                    time_col = col
                if 'glucose' in col_lower or 'historic glucose' in col_lower or 'scan glucose' in col_lower:
                    glucose_col = col
            
            if time_col and glucose_col:
                df['timestamp'] = pd.to_datetime(df[time_col])
                df['glucose'] = pd.to_numeric(df[glucose_col], errors='coerce')
                return df[['timestamp', 'glucose']].dropna()
        
        elif filepath.endswith('.json'):
            df = pd.read_json(filepath)
            return self._parse_json(df)
        
        raise ValueError("不支持的 Libre 文件格式")


class MedtronicAdapter(CGMDeviceAdapter):
    """Medtronic CGM 适配器"""
    
    def parse(self, filepath: str) -> pd.DataFrame:
        """解析 Medtronic CGM 数据"""
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
            
            time_col = None
            glucose_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'timestamp' in col_lower or 'time' in col_lower:
                    time_col = col
                if 'sensor glucose' in col_lower or 'sg' in col_lower:
                    glucose_col = col
            
            if time_col and glucose_col:
                df['timestamp'] = pd.to_datetime(df[time_col])
                df['glucose'] = pd.to_numeric(df[glucose_col], errors='coerce')
                return df[['timestamp', 'glucose']].dropna()
        
        raise ValueError("不支持的 Medtronic 文件格式")


class ManualInputAdapter(CGMDeviceAdapter):
    """手动输入适配器 - 支持常见格式"""
    
    def parse(self, filepath: str) -> pd.DataFrame:
        """解析手动记录的血糖数据"""
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
            
            # 尝试自动识别列
            cols = df.columns.tolist()
            
            # 时间列
            time_col = next((c for c in cols if any(k in c.lower() for k in ['time', 'date', 'timestamp'])), None)
            # 血糖列
            glucose_col = next((c for c in cols if any(k in c.lower() for k in ['glucose', 'blood sugar', 'bs', 'bg'])), None)
            
            if time_col and glucose_col:
                df['timestamp'] = pd.to_datetime(df[time_col])
                df['glucose'] = pd.to_numeric(df[glucose_col], errors='coerce')
                return df[['timestamp', 'glucose']].dropna()
        
        raise ValueError("无法解析文件，请检查格式")


# 设备适配器注册表
ADAPTERS = {
    'dexcom': DexcomG6Adapter,
    'dexcom_g6': DexcomG6Adapter,
    'dexcom_g7': DexcomG7Adapter,
    'libre': FreeStyleLibreAdapter,
    'freestyle': FreeStyleLibreAdapter,
    'medtronic': MedtronicAdapter,
    'manual': ManualInputAdapter,
}


def detect_device(filepath: str) -> str:
    """自动检测 CGM 设备类型"""
    filename = filepath.lower()
    
    if 'dexcom' in filename:
        return 'dexcom'
    elif 'libre' in filename or 'freestyle' in filename:
        return 'libre'
    elif 'medtronic' in filename:
        return 'medtronic'
    else:
        return 'manual'


def load_cgm_data(filepath: str, device: str = None) -> pd.DataFrame:
    """加载 CGM 数据，自动检测设备类型
    
    Args:
        filepath: CGM 数据文件路径
        device: 设备类型，可选 (会自动检测)
    
    Returns:
        包含 timestamp 和 glucose 列的 DataFrame
    """
    if device is None:
        device = detect_device(filepath)
    
    if device not in ADAPTERS:
        raise ValueError(f"不支持的设备类型: {device}")
    
    adapter = ADAPTERS[device]()
    df = adapter.parse(filepath)
    
    # 排序并去重
    df = df.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
    
    return df.reset_index(drop=True)


# 便捷函数
def load_dexcom(filepath: str) -> pd.DataFrame:
    """加载 Dexcom 数据"""
    return load_cgm_data(filepath, 'dexcom')


def load_libre(filepath: str) -> pd.DataFrame:
    """加载 FreeStyle Libre 数据"""
    return load_cgm_data(filepath, 'libre')
