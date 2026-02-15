"""
报告生成模块
"""

from typing import Dict
from glyconutri.analysis import get_glucose_status


def generate_report(analysis_results: Dict, patient_name: str = None) -> str:
    """生成患者报告"""
    name = patient_name or "患者"
    status = get_glucose_status(analysis_results['tir'])
    
    report = f"""
================================================================================
                        血糖分析报告
================================================================================
患者: {name}
--------------------------------------------------------------------------------
【总体评估】
血糖控制状态: {status}
Time in Range (TIR): {analysis_results['tir']:.1f}%

--------------------------------------------------------------------------------
【血糖统计】
平均血糖: {analysis_results['mean_glucose']:.1f} mg/dL
中位数血糖: {analysis_results['median_glucose']:.1f} mg/dL
标准差: {analysis_results['std_glucose']:.1f} mg/dL
最低血糖: {analysis_results['min_glucose']:.1f} mg/dL
最高血糖: {analysis_results['max_glucose']:.1f} mg/dL

--------------------------------------------------------------------------------
【时间分布】
低于 70 mg/dL (低血糖): {analysis_results['time_below_70']:.1f}%
低于 54 mg/dL (严重低血糖): {analysis_results['time_below_54']:.1f}%
高于 180 mg/dL (高血糖): {analysis_results['time_above_180']:.1f}%
高于 250 mg/dL (严重高血糖): {analysis_results['time_above_250']:.1f}%

--------------------------------------------------------------------------------
【血糖波动】
波动系数 (GV): {analysis_results['gv']:.1f}%

================================================================================
"""
    return report


def generate_clinical_summary(analysis_results: Dict) -> str:
    """生成临床摘要"""
    tir = analysis_results['tir']
    gv = analysis_results['gv']
    
    recommendations = []
    
    if tir < 50:
        recommendations.append("⚠️ TIR 偏低，建议调整治疗方案")
    elif tir < 70:
        recommendations.append("📊 TIR 有待提高，可考虑饮食和运动调整")
    
    if gv > 36:
        recommendations.append("⚠️ 血糖波动较大，需关注")
    
    if analysis_results['time_below_54'] > 1:
        recommendations.append("🚨 严重低血糖时间需关注")
    
    if not recommendations:
        recommendations.append("✅ 血糖控制良好")
    
    summary = f"""
【临床摘要】

TIR: {tir:.1f}% | GV: {gv:.1f}%

建议:
"""
    summary += "\n".join(f"  {r}" for r in recommendations)
    
    return summary
