"""
GlycoNutri - 血糖营养计算工具 CLI
"""

import click
from glyconutri.cgm_adapters import load_cgm_data
from glyconutri.cgm import calculate_tir, calculate_gv
from glyconutri.food import get_gi, calculate_gl, get_food_info, search_foods, list_foods_by_gi_category
from glyconutri.analysis import analyze_glucose
from glyconutri.report import generate_report


@click.group()
def cli():
    """GlycoNutri - 血糖营养计算工具 for 医生"""
    pass


# ============ CGM 命令 ============

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--device', '-d', type=click.Choice(['auto', 'dexcom', 'libre', 'medtronic', 'manual']),
              default='auto', help='CGM 设备类型')
def analyze(filepath, device):
    """分析 CGM 数据文件
    
    支持格式: CSV, JSON
    自动检测 Dexcom, Libre, Medtronic 数据
    """
    try:
        if device == 'auto':
            df = load_cgm_data(filepath)
        else:
            df = load_cgm_data(filepath, device)
        
        results = analyze_glucose(df)
        
        click.echo(f"\n{'='*50}")
        click.echo(f"           血糖分析结果")
        click.echo(f"{'='*50}")
        click.echo(f"数据点数: {len(df)}")
        click.echo(f"时间范围: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
        click.echo(f"\n--- 核心指标 ---")
        click.echo(f"Time in Range (TIR): {results['tir']:.1f}%")
        click.echo(f"血糖波动 (GV): {results['gv']:.1f}%")
        click.echo(f"平均血糖: {results['mean_glucose']:.1f} mg/dL")
        click.echo(f"标准差: {results['std_glucose']:.1f} mg/dL")
        click.echo(f"\n--- 血糖分布 ---")
        click.echo(f"< 70 mg/dL (低血糖): {results['time_below_70']:.1f}%")
        click.echo(f"> 180 mg/dL (高血糖): {results['time_above_180']:.1f}%")
        click.echo(f"> 250 mg/dL (严重高血糖): {results['time_above_250']:.1f}%")
        
    except Exception as e:
        click.echo(f"错误: {e}", err=True)


# ============ 食物 GI/GL 命令 ============

@cli.command()
@click.argument('food_name')
def gi(food_name):
    """查询食物的升糖指数 (GI)
    
    示例: glyconutri gi 米饭
    """
    info = get_food_info(food_name)
    if info:
        click.echo(f"\n{info['name']}")
        click.echo(f"GI: {info['gi']} ({info['gi_category']}GI)")
    else:
        # 尝试搜索
        results = search_foods(food_name)
        if results:
            click.echo(f"\n未找到'{food_name}'，以下是搜索结果:")
            for r in results[:5]:
                click.echo(f"  - {r['name']}: GI {r['gi']} ({r['gi_category']}GI)")
        else:
            click.echo(f"未找到 '{food_name}' 的 GI 数据")


@cli.command()
@click.argument('food_name')
@click.argument('carbs', type=float, required=False)
@click.option('--weight', '-w', type=float, help='食物重量 (g)，自动计算碳水')
def gl(food_name, carbs, weight):
    """计算食物的升糖负荷 (GL)
    
    示例: 
        glyconutri gl 米饭 30      # 30g 碳水
        glyconutri gl 米饭 -w 100  # 100g 米饭
    """
    # 如果提供了重量，尝试获取碳水
    if weight and carbs is None:
        from glyconutri.gi_database import get_carbs
        carbs = get_carbs(food_name)
        if carbs:
            carbs = carbs * weight / 100
            click.echo(f"按 {weight}g 计算，碳水含量: {carbs:.1f}g")
    
    if carbs is None:
        click.echo("请提供碳水含量 (carbs) 或使用 --weight 指定重量", err=True)
        return
    
    info = get_food_info(food_name, carbs)
    if info and 'gl' in info:
        click.echo(f"\n{info['name']} (碳水 {carbs:.1f}g)")
        click.echo(f"GI: {info['gi']} | GL: {info['gl']:.1f} ({info['gl_category']}GL)")
    else:
        click.echo(f"未找到 '{food_name}' 的数据", err=True)


@cli.command()
@click.argument('category', type=click.Choice(['低', '中', '高']))
def list_gi(category):
    """按 GI 类别列出食物
    
    示例: glyconutri list 低
    """
    foods = list_foods_by_gi_category(category)
    click.echo(f"\n{category}GI 食物 ({len(foods)} 个):")
    click.echo("-" * 40)
    for f in foods[:20]:
        carbs_str = f"{f['carbs_per_100g']}g/100g" if f['carbs_per_100g'] else "N/A"
        click.echo(f"  {f['name']:15} GI: {f['gi']:3}  碳水: {carbs_str}")
    
    if len(foods) > 20:
        click.echo(f"  ... 还有 {len(foods) - 20} 个")


@cli.command()
@click.argument('keyword')
def search(keyword):
    """搜索食物
    
    示例: glyconutri search 苹果
    """
    results = search_foods(keyword)
    if results:
        click.echo(f"\n搜索 '{keyword}' 结果 ({len(results)} 个):")
        click.echo("-" * 50)
        for r in results[:15]:
            gl_str = f"GL: {r.get('gl', 'N/A')}" if r.get('gl') else ""
            carbs_str = f"碳水: {r.get('carbs_per_100g', 'N/A')}g" if r.get('carbs_per_100g') else ""
            click.echo(f"  {r['name']:12} GI: {r['gi']:3} ({r['gi_category']})  {carbs_str}")
    else:
        click.echo(f"未找到匹配 '{keyword}' 的食物")


# ============ 报告命令 ============

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--name', '-n', default='患者', help='患者姓名')
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
def report(filepath, name, output):
    """生成血糖分析报告"""
    df = load_cgm_data(filepath)
    results = analyze_glucose(df)
    report_text = generate_report(results, name)
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(report_text)
        click.echo(f"报告已保存到: {output}")
    else:
        click.echo(report_text)


# ============ 版本信息 ============

@cli.command()
def version():
    """显示版本信息"""
    from glyconutri import __version__
    click.echo(f"GlycoNutri v{__version__}")
    click.echo("血糖营养计算工具 for 医生")


if __name__ == '__main__':
    cli()
