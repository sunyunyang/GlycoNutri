"""
GlycoNutri - 血糖营养计算工具 CLI
"""

import click
from glyconutri.cgm import load_cgm_data, calculate_tir, calculate_gv
from glyconutri.food import get_gi, calculate_gl
from glyconutri.analysis import analyze_glucose
from glyconutri.report import generate_report


@click.group()
def cli():
    """GlycoNutri - 血糖营养计算工具"""
    pass


@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
def analyze(filepath):
    """分析 CGM 数据文件"""
    data = load_cgm_data(filepath)
    results = analyze_glucose(data)
    
    click.echo(f"\n=== 血糖分析结果 ===")
    click.echo(f"Time in Range (TIR): {results['tir']:.1f}%")
    click.echo(f"血糖波动 (GV): {results['gv']:.1f}%")
    click.echo(f"平均血糖: {results['mean_glucose']:.1f} mg/dL")
    click.echo(f"标准差: {results['std_glucose']:.1f} mg/dL")


@cli.command()
@click.argument('food_name')
def gi(food_name):
    """查询食物的升糖指数 (GI)"""
    gi_value = get_gi(food_name)
    if gi_value:
        click.echo(f"{food_name} 的 GI 值: {gi_value}")
    else:
        click.echo(f"未找到 {food_name} 的 GI 数据")


@cli.command()
@click.argument('food_name')
@click.argument('carbs', type=float)
def gl(food_name, carbs):
    """计算食物的升糖负荷 (GL)"""
    gi_value = get_gi(food_name)
    if gi_value:
        gl_value = calculate_gl(gi_value, carbs)
        click.echo(f"{food_name} (碳水 {carbs}g) 的 GL 值: {gl_value:.1f}")
    else:
        click.echo(f"未找到 {food_name} 的 GI 数据")


if __name__ == '__main__':
    cli()
