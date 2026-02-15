"""
药物对血糖影响分析模块
分析口服降糖药和胰岛素的血糖效应
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional


# ============ 药物数据库 ============

# 口服降糖药
ORAL_MEDICATIONS = {
    "二甲双胍": {
        "type": "口服",
        "class": "双胍类",
        "onset_hours": 1,      # 起效时间
        "peak_hours": 2,        # 峰值时间
        "duration_hours": 6,    # 持续时间
        "effect": "减少肝糖输出，增加胰岛素敏感性",
        "hypo_risk": "低"
    },
    "阿卡波糖": {
        "type": "口服",
        "class": "α-糖苷酶抑制剂",
        "onset_hours": 0.5,
        "peak_hours": 1,
        "duration_hours": 4,
        "effect": "延缓碳水吸收",
        "hypo_risk": "低"
    },
    "伏格列波糖": {
        "type": "口服",
        "class": "α-糖苷酶抑制剂",
        "onset_hours": 0.5,
        "peak_hours": 1,
        "duration_hours": 4,
        "effect": "延缓碳水吸收",
        "hypo_risk": "低"
    },
    "格列本脲": {
        "type": "口服",
        "class": "磺脲类",
        "onset_hours": 1,
        "peak_hours": 3,
        "duration_hours": 12,
        "effect": "刺激胰岛素分泌",
        "hypo_risk": "高"
    },
    "格列齐特": {
        "type": "口服",
        "class": "磺脲类",
        "onset_hours": 1,
        "peak_hours": 3,
        "duration_hours": 10,
        "effect": "刺激胰岛素分泌",
        "hypo_risk": "中"
    },
    "格列吡嗪": {
        "type": "口服",
        "class": "磺脲类",
        "onset_hours": 0.5,
        "peak_hours": 2,
        "duration_hours": 8,
        "effect": "刺激胰岛素分泌",
        "hypo_risk": "中"
    },
    "格列美脲": {
        "type": "口服",
        "class": "磺脲类",
        "onset_hours": 0.5,
        "peak_hours": 2,
        "duration_hours": 10,
        "effect": "刺激胰岛素分泌",
        "hypo_risk": "中"
    },
    "瑞格列奈": {
        "type": "口服",
        "class": "格列奈类",
        "onset_hours": 0.25,
        "peak_hours": 1,
        "duration_hours": 4,
        "effect": "快速刺激胰岛素分泌",
        "hypo_risk": "中"
    },
    "那格列奈": {
        "type": "口服",
        "class": "格列奈类",
        "onset_hours": 0.25,
        "peak_hours": 1,
        "duration_hours": 3,
        "effect": "快速刺激胰岛素分泌",
        "hypo_risk": "中"
    },
    "吡格列酮": {
        "type": "口服",
        "class": "噻唑烷二酮类",
        "onset_hours": 1,
        "peak_hours": 3,
        "duration_hours": 24,
        "effect": "提高胰岛素敏感性",
        "hypo_risk": "低"
    },
    "罗格列酮": {
        "type": "口服",
        "class": "噻唑烷二酮类",
        "onset_hours": 1,
        "peak_hours": 3,
        "duration_hours": 24,
        "effect": "提高胰岛素敏感性",
        "hypo_risk": "低"
    },
    "西格列汀": {
        "type": "口服",
        "class": "DPP-4抑制剂",
        "onset_hours": 1,
        "peak_hours": 2,
        "duration_hours": 24,
        "effect": "促进胰岛素分泌，抑制胰高血糖素",
        "hypo_risk": "低"
    },
    "沙格列汀": {
        "type": "口服",
        "class": "DPP-4抑制剂",
        "onset_hours": 1,
        "peak_hours": 2,
        "duration_hours": 24,
        "effect": "促进胰岛素分泌，抑制胰高血糖素",
        "hypo_risk": "低"
    },
    "维格列汀": {
        "type": "口服",
        "class": "DPP-4抑制剂",
        "onset_hours": 1,
        "peak_hours": 2,
        "duration_hours": 24,
        "effect": "促进胰岛素分泌，抑制胰高血糖素",
        "hypo_risk": "低"
    },
    "恩格列净": {
        "type": "口服",
        "class": "SGLT-2抑制剂",
        "onset_hours": 1,
        "peak_hours": 2,
        "duration_hours": 24,
        "effect": "促进尿糖排泄",
        "hypo_risk": "低"
    },
    "卡格列净": {
        "type": "口服",
        "class": "SGLT-2抑制剂",
        "onset_hours": 1,
        "peak_hours": 2,
        "duration_hours": 24,
        "effect": "促进尿糖排泄",
        "hypo_risk": "低"
    },
    "达格列净": {
        "type": "口服",
        "class": "SGLT-2抑制剂",
        "onset_hours": 1,
        "peak_hours": 2,
        "duration_hours": 24,
        "effect": "促进尿糖排泄",
        "hypo_risk": "低"
    },
    "司美格鲁肽": {
        "type": "注射",
        "class": "GLP-1受体激动剂",
        "onset_hours": 1,
        "peak_hours": 3,
        "duration_hours": 168,  # 7天
        "effect": "促进胰岛素分泌，延缓胃排空",
        "hypo_risk": "低"
    },
    "度拉糖肽": {
        "type": "注射",
        "class": "GLP-1受体激动剂",
        "onset_hours": 1,
        "peak_hours": 3,
        "duration_hours": 168,
        "effect": "促进胰岛素分泌，延缓胃排空",
        "hypo_risk": "低"
    },
    "利拉鲁肽": {
        "type": "注射",
        "class": "GLP-1受体激动剂",
        "onset_hours": 1,
        "peak_hours": 3,
        "duration_hours": 24,
        "effect": "促进胰岛素分泌，延缓胃排空",
        "hypo_risk": "低"
    },
}

# 胰岛素类型
INSULIN_TYPES = {
    "速效": {
        "onset_min": 15,
        "peak_min": 60,
        "duration_hours": 3,
        "examples": "门冬胰岛素、赖脯胰岛素、谷赖胰岛素",
        "hypo_risk": "中"
    },
    "短效": {
        "onset_min": 30,
        "peak_min": 120,
        "duration_hours": 5,
        "examples": "普通胰岛素",
        "hypo_risk": "中"
    },
    "中效": {
        "onset_min": 60,
        "peak_min": 360,
        "duration_hours": 12,
        "examples": "NPH",
        "hypo_risk": "中"
    },
    "长效": {
        "onset_min": 120,
        "peak_min": None,  # 无明显峰值
        "duration_hours": 24,
        "examples": "甘精胰岛素、地特胰岛素、德谷胰岛素",
        "hypo_risk": "低"
    },
    "超长效": {
        "onset_min": 120,
        "peak_min": None,
        "duration_hours": 42,
        "examples": "德谷胰岛素",
        "hypo_risk": "低"
    },
    "预混": {
        "onset_min": 30,
        "peak_min": 120,
        "duration_hours": 12,
        "examples": "门冬胰岛素30、优泌林70/30",
        "hypo_risk": "中"
    },
}


class MedicationEvent:
    """药物事件"""
    
    def __init__(self, medication_name: str, dosage: float = None, 
                 unit: str = None, taken_time: datetime = None,
                 medication_type: str = "口服"):
        self.medication_name = medication_name
        self.dosage = dosage  # mg 或 U
        self.unit = unit
        self.taken_time = taken_time or datetime.now()
        self.medication_type = medication_type
        
        # 获取药物信息
        self.info = ORAL_MEDICATIONS.get(medication_name)
        
    @property
    def onset_time(self) -> datetime:
        """药物起效时间"""
        if self.info:
            hours = self.info.get('onset_hours', 1)
            return self.taken_time + timedelta(hours=hours)
        return self.taken_time + timedelta(hours=1)
    
    @property
    def peak_time(self) -> datetime:
        """药物峰值时间"""
        if self.info:
            hours = self.info.get('peak_hours', 2)
            return self.taken_time + timedelta(hours=hours)
        return self.taken_time + timedelta(hours=2)
    
    @property
    def end_time(self) -> datetime:
        """药效结束时间"""
        if self.info:
            hours = self.info.get('duration_hours', 6)
            return self.taken_time + timedelta(hours=hours)
        return self.taken_time + timedelta(hours=6)
    
    def to_dict(self) -> dict:
        return {
            "medication_name": self.medication_name,
            "dosage": self.dosage,
            "unit": self.unit,
            "type": self.medication_type,
            "taken_time": self.taken_time.isoformat(),
            "onset_time": self.onset_time.isoformat(),
            "peak_time": self.peak_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "class": self.info.get('class') if self.info else None,
            "effect": self.info.get('effect') if self.info else None,
            "hypo_risk": self.info.get('hypo_risk') if self.info else None
        }


class MedicationAnalysis:
    """药物血糖分析"""
    
    def __init__(self, medication: MedicationEvent, cgm_data: pd.DataFrame):
        self.medication = medication
        self.cgm_data = cgm_data
    
    def find_medication_window(self) -> pd.DataFrame:
        """找到服药后时间窗口的数据"""
        window = self.cgm_data[
            (self.cgm_data['timestamp'] >= self.medication.taken_time) & 
            (self.cgm_data['timestamp'] <= self.medication.end_time)
        ]
        return window
    
    def find_baseline_window(self, minutes: int = 30) -> pd.DataFrame:
        """找到服药前基线数据"""
        start = self.medication.taken_time - timedelta(minutes=minutes)
        window = self.cgm_data[
            (self.cgm_data['timestamp'] >= start) & 
            (self.cgm_data['timestamp'] < self.medication.taken_time)
        ]
        return window
    
    def calculate_baseline(self) -> Optional[float]:
        """计算服药前基线血糖"""
        baseline = self.find_baseline_window()
        if baseline.empty:
            return None
        return baseline['glucose'].mean()
    
    def calculate_response(self) -> Dict:
        """计算药物血糖响应"""
        baseline = self.calculate_baseline()
        
        if baseline is None:
            return {"error": "数据不足"}
        
        window = self.find_medication_window()
        
        results = {
            "medication": self.medication.to_dict(),
            "baseline": baseline
        }
        
        if window.empty:
            return {**results, "error": "时间窗口内无数据"}
        
        # 各阶段分析
        # 起效期
        onset_end = self.medication.onset_time
        onset_window = window[window['timestamp'] < onset_end]
        
        # 峰值期
        peak_start = self.medication.onset_time
        peak_end = self.medication.peak_time
        peak_window = window[(window['timestamp'] >= peak_start) & (window['timestamp'] < peak_end)]
        
        # 持续期
        duration_window = window[window['timestamp'] >= peak_end]
        
        if not onset_window.empty:
            results["onset"] = {
                "min": onset_window['glucose'].min(),
                "max": onset_window['glucose'].max(),
                "avg": onset_window['glucose'].mean()
            }
        
        if not peak_window.empty:
            results["peak"] = {
                "min": peak_window['glucose'].min(),
                "max": peak_window['glucose'].max(),
                "avg": peak_window['glucose'].mean(),
                "change_from_baseline": peak_window['glucose'].mean() - baseline
            }
        
        if not duration_window.empty:
            results["duration"] = {
                "min": duration_window['glucose'].min(),
                "max": duration_window['glucose'].max(),
                "avg": duration_window['glucose'].mean()
            }
        
        # 整体效果
        results["overall"] = {
            "min": window['glucose'].min(),
            "max": window['glucose'].max(),
            "avg": window['glucose'].mean(),
            "change_from_baseline": window['glucose'].mean() - baseline,
            "max_drop": baseline - window['glucose'].min()  # 最大降幅
        }
        
        return results
    
    def assess_efficacy(self) -> Dict:
        """评估药效"""
        response = self.calculate_response()
        
        if "error" in response:
            return {"efficacy": "未知", "score": 0}
        
        overall = response.get("overall", {})
        baseline = response.get("baseline")
        
        if not overall or baseline is None:
            return {"efficacy": "未知", "score": 0}
        
        # 计算效果评分
        score = 50
        change = overall.get("change_from_baseline", 0)
        max_drop = overall.get("max_drop", 0)
        
        # 降糖效果
        if change < -30:
            score += 30
        elif change < -15:
            score += 20
        elif change < 0:
            score += 10
        elif change > 20:
            score -= 20
        
        # 降幅
        if max_drop > 50:
            score += 20
        elif max_drop > 30:
            score += 10
        
        score = min(100, max(0, score))
        
        if score >= 80:
            efficacy = "显著"
        elif score >= 60:
            efficacy = "良好"
        elif score >= 40:
            efficacy = "一般"
        else:
            efficacy = "不佳"
        
        return {
            "efficacy": efficacy,
            "score": score,
            "change": change,
            "max_drop": max_drop
        }
    
    def generate_recommendations(self) -> List[str]:
        """生成用药建议"""
        response = self.calculate_response()
        efficacy = self.assess_efficacy()
        
        if "error" in response:
            return ["数据不足，无法生成建议"]
        
        recommendations = []
        med = self.medication
        
        # 基于药效
        if efficacy.get("efficacy") == "不佳":
            recommendations.append(f"{med.medication_name}降糖效果不佳，建议咨询医生调整用药")
        
        # 低血糖风险
        hypo_risk = med.info.get('hypo_risk') if med.info else "低"
        if hypo_risk == "高":
            recommendations.append("该药物低血糖风险较高，注意监测")
        elif hypo_risk == "中":
            recommendations.append("注意餐后血糖变化，警惕低血糖")
        
        # 基于血糖变化
        overall = response.get("overall", {})
        max_drop = overall.get("max_drop", 0)
        
        if max_drop > 50:
            recommendations.append("血糖降幅较大，关注延迟性低血糖")
        elif max_drop < 10:
            recommendations.append("降糖效果不明显，可能需要调整剂量")
        
        # 时间建议
        if med.medication_type == "口服":
            recommendations.append(f"起效时间约{med.info.get('onset_hours')}小时，持续约{med.info.get('duration_hours')}小时")
        
        if not recommendations:
            recommendations.append("血糖控制良好，继续保持")
        
        return recommendations
    
    def get_full_analysis(self) -> Dict:
        """完整分析"""
        response = self.calculate_response()
        efficacy = self.assess_efficacy()
        recs = self.generate_recommendations()
        
        return {
            "response": response,
            "efficacy": efficacy,
            "recommendations": recs
        }


# ============ 胰岛素专项分析 ============

class InsulinAnalysis:
    """胰岛素专项分析"""
    
    def __init__(self, insulin_type: str, units: float, injection_time: datetime, cgm_data: pd.DataFrame):
        self.insulin_type = insulin_type
        self.units = units
        self.injection_time = injection_time
        self.cgm_data = cgm_data
        self.info = INSULIN_TYPES.get(insulin_type, INSULIN_TYPES["短效"])
    
    @property
    def onset_time(self) -> datetime:
        return self.injection_time + timedelta(minutes=self.info["onset_min"])
    
    @property
    def peak_time(self) -> datetime:
        peak_min = self.info.get("peak_min")
        if peak_min:
            return self.injection_time + timedelta(minutes=peak_min)
        return self.injection_time + timedelta(hours=6)
    
    @property
    def end_time(self) -> datetime:
        return self.injection_time + timedelta(hours=self.info["duration_hours"])
    
    def calculate_onset_action_duration(self) -> Dict:
        """计算起效-峰值-持续时间"""
        window = self.cgm_data[
            (self.cgm_data['timestamp'] >= self.injection_time) & 
            (self.cgm_data['timestamp'] <= self.end_time)
        ]
        
        baseline_window = self.cgm_data[
            (self.cgm_data['timestamp'] >= self.injection_time - timedelta(minutes=30)) & 
            (self.cgm_data['timestamp'] < self.injection_time)
        ]
        
        baseline = baseline_window['glucose'].mean() if not baseline_window.empty else None
        
        result = {
            "insulin_type": self.insulin_type,
            "units": self.units,
            "injection_time": self.injection_time.isoformat(),
            "onset_time": self.onset_time.isoformat(),
            "peak_time": self.peak_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "onset_min": self.info["onset_min"],
            "peak_min": self.info.get("peak_min"),
            "duration_hours": self.info["duration_hours"]
        }
        
        if baseline:
            result["baseline"] = baseline
        
        if not window.empty:
            result["glucose"] = {
                "min": window['glucose'].min(),
                "max": window['glucose'].max(),
                "avg": window['glucose'].mean()
            }
            
            # 找最低点
            min_idx = window['glucose'].idxmin()
            min_row = window.loc[min_idx]
            result["lowest_point"] = {
                "glucose": min_row['glucose'],
                "time": min_row['timestamp'].isoformat()
            }
            
            if baseline:
                result["max_drop"] = baseline - min_row['glucose']
        
        return result
    
    def calculate_icar(self) -> Optional[float]:
        """计算胰岛素碳水比 (ICR)
        1U 胰岛素覆盖多少克碳水
        """
        # 需要用餐后碳水摄入量计算
        # 简化版：使用经验值
        # ICR ≈ 450 / 全天胰岛素总量 或 300 / 碳水系数
        # 这里假设 ICR = 10g/U 作为默认值
        return 10  # 需要根据个人情况调整
    
    def calculate_cir(self) -> Optional[float]:
        """计算碳水化合物胰岛素比 (CIR)
        同 ICR
        """
        return self.calculate_icar()
    
    def calculate_isf(self) -> float:
        """计算胰岛素敏感因子 (ISF)
        1U 胰岛素降低多少血糖
        """
        # 需要根据数据估算
        # 简化：使用体重计算 ISF = 1700 / (体重 × 0.55) / 总胰岛素
        # 这里假设 ISF = 50 mg/dL per unit
        return 50  # 需要根据个人情况调整
    
    def get_full_analysis(self) -> Dict:
        """完整分析"""
        oad = self.calculate_onset_action_duration()
        
        # 计算 ICR 和 ISF
        icar = self.calculate_icar()
        isf = self.calculate_isf()
        
        return {
            "insulin": oad,
            "icar": icar,
            "isf": isf,
            "recommendations": self._generate_recommendations(oad)
        }
    
    def _generate_recommendations(self, oad: Dict) -> List[str]:
        """生成建议"""
        recs = []
        
        # 基于胰岛素类型
        recs.append(f"{self.insulin_type}胰岛素：起效{self.info['onset_min']}分钟，峰值{self.info.get('peak_min', '无明显峰值')}分钟，持续{self.info['duration_hours']}小时")
        
        # 基于血糖变化
        max_drop = oad.get("max_drop", 0)
        if max_drop > 80:
            recs.append("血糖降幅较大，警惕低血糖")
        elif max_drop > 50:
            recs.append("降糖效果明显")
        
        # 低血糖
        lowest = oad.get("lowest_point", {})
        if lowest.get("glucose", 999) < 70:
            recs.append("出现低血糖，建议减少胰岛素剂量")
        
        if not recs:
            recs.append("胰岛素效果正常")
        
        return recs


# ============ 便捷函数 ============

def analyze_medication(medication_name: str, dosage: float, taken_time: datetime, 
                      cgm_data: pd.DataFrame) -> Dict:
    """分析药物血糖影响"""
    med = MedicationEvent(medication_name, dosage, taken_time=taken_time)
    analysis = MedicationAnalysis(med, cgm_data)
    return analysis.get_full_analysis()


def analyze_insulin(insulin_type: str, units: float, injection_time: datetime,
                   cgm_data: pd.DataFrame) -> Dict:
    """分析胰岛素效果"""
    analysis = InsulinAnalysis(insulin_type, units, injection_time, cgm_data)
    return analysis.get_full_analysis()


def get_available_medications() -> Dict:
    """获取可用药物列表"""
    return {
        "oral": list(ORAL_MEDICATIONS.keys()),
        "insulin": list(INSULIN_TYPES.keys())
    }
