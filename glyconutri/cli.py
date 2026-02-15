"""
GlycoNutri - 血糖营养计算工具 CLI
"""

import click
import json
from datetime import datetime
from glyconutri.cgm_adapters import load_cgm_data
from glyconutri.cgm import calculate_tir, calculate_gv
from glyconutri.food import get_gi, calculate_gl, get_food_info, search_foods, list_foods_by_gi_category
from glyconutri.analysis import analyze_glucose
from glyconutri.report import generate_report
from glyconutri.postmeal import MealSession, PostMealAnalysis, RepeatedMealAnalyzer, create_meal_session


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


# ============ 餐后血糖分析命令 ============

@cli.command()
@click.argument('cgm_file', type=click.Path(exists=True))
@click.option('--food', '-f', multiple=True, help='食物项，格式: 食物名:重量(g)')
@click.option('--time', '-t', help='餐食时间，格式: YYYY-MM-DD HH:MM:SS')
@click.option('--json', '-j', is_flag=True, help='输出 JSON 格式')
def meal(cgm_file, food, time, json):
    """餐后血糖分析
    
    分析餐后血糖响应，计算个体化 GI/GL
    
    示例:
        glyconutri meal data/cgm.csv -f "米饭:100g" -f "苹果:150g"
        glyconutri meal data/cgm.csv -f "米饭:100g" -t "2026-02-15 12:00:00"
    """
    try:
        # 加载 CGM 数据
        df = load_cgm_data(cgm_file)
        
        # 解析时间
        if time:
            meal_time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        else:
            # 使用最后一条记录的时间
            meal_time = df['timestamp'].max()
        
        # 解析食物
        foods = []
        for f in food:
            if ':' in f:
                name, weight_str = f.rsplit(':', 1)
                weight = float(weight_str.replace('g', '').replace('G', ''))
                foods.append({"name": name.strip(), "weight": weight})
        
        if not foods:
            click.echo("请至少提供一种食物，格式: -f 食物名:重量(g)", err=True)
            return
        
        # 创建餐次
        session = create_meal_session(foods, meal_time)
        
        # 分析
        analysis = PostMealAnalysis(session.meals[0], df)
        
        baseline = analysis.calculate_baseline()
        peak = analysis.calculate_peak()
        response = analysis.response_magnitude()
        iauc = analysis.calculate_incremental_auc()
        
        if json:
            result = {
                "meal_time": meal_time.isoformat(),
                "foods": [m.to_dict() for m in session.meals],
                "total_carbs": session.total_carbs,
                "total_gl": session.total_gl,
                "weighted_gi": session.weighted_gi,
                "baseline_glucose": baseline,
                "peak_glucose": peak,
                "response_magnitude": response,
                "iauc_2h": iauc
            }
            click.echo(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            click.echo(f"\n{'='*50}")
            click.echo(f"           餐后血糖分析")
            click.echo(f"{'='*50}")
            click.echo(f"餐食时间: {meal_time}")
            click.echo(f"\n--- 食物信息 ---")
            for m in session.meals:
                click.echo(f"  {m.food_name}: {m.weight}g, 碳水 {m.carbs}g, GI {m.gi}, GL {m.gl:.1f}")
            click.echo(f"\n--- 汇总 ---")
            click.echo(f"总碳水: {session.total_carbs:.1f}g")
            click.echo(f"总 GL: {session.total_gl:.1f}")
            click.echo(f"加权 GI: {session.weighted_gi:.1f}")
            click.echo(f"\n--- 血糖响应 ---")
            click.echo(f"餐前基线: {baseline:.1f} mg/dL" if baseline else "餐前基线: N/A")
            click.echo(f"餐后峰值: {peak:.1f} mg/dL" if peak else "餐后峰值: N/A")
            click.echo(f"血糖增幅: {response:.1f} mg/dL" if response else "血糖增幅: N/A")
            click.echo(f"iAUC (2h): {iauc:.1f}" if iauc else "iAUC (2h): N/A")
            
    except Exception as e:
        click.echo(f"错误: {e}", err=True)


@cli.command()
@click.argument('cgm_file', type=click.Path(exists=True))
@click.option('--food', '-f', multiple=True, help='食物项，格式: 食物名:重量(g)')
@click.option('--count', '-n', default=3, help='重复次数')
@click.option('--json', '-j', is_flag=True, help='输出 JSON 格式')
def meal_repeat(cgm_file, food, count, json):
    """多次餐后血糖分析（取平均值）
    
    对同一种餐食进行多次测量，计算平均值和标准差
    
    示例:
        glyconutri meal-repeat data/cgm.csv -f "米饭:100g" -n 5
    """
    try:
        df = load_cgm_data(cgm_file)
        
        # 解析食物
        foods = []
        for f in food:
            if ':' in f:
                name, weight_str = f.rsplit(':', 1)
                weight = float(weight_str.replace('g', '').replace('G', ''))
                foods.append({"name": name.strip(), "weight": weight})
        
        if not foods:
            click.echo("请至少提供一种食物", err=True)
            return
        
        # 模拟多次餐食（这里简化处理，实际应该是多次独立的餐食时间）
        analyzer = RepeatedMealAnalyzer()
        
        # 获取所有餐后时间段的数据进行模拟
        meal_times = df['timestamp'].dt.floor('H').unique()[-count:]
        
        for meal_time in meal_times:
            session = create_meal_session(foods, pd.Timestamp(meal_time).to_pydatetime())
            analyzer.add_session(session)
        
        results = analyzer.analyze_repeated(df)
        
        if json:
            click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            click.echo(f"\n{'='*50}")
            click.echo(f"       多次餐后血糖分析 (n={count})")
            click.echo(f"{'='*50}")
            click.echo(f"\n--- 食物 ---")
            for f in foods:
                info = get_food_info(f['name'])
                if info:
                    carbs = info.get('carbs_per_100g', 0) * f['weight'] / 100
                    gl = (info.get('gi', 0) * carbs / 100) if carbs else 0
                    click.echo(f"  {f['name']}: {f['weight']}g (碳水 {carbs:.1f}g, GL {gl:.1f})")
            
            click.echo(f"\n--- 血糖响应 (平均 ± 标准差) ---")
            
            resp = results.get('response_magnitude', {})
            if resp.get('mean'):
                click.echo(f"血糖增幅: {resp['mean']:.1f} ± {resp['std']:.1f} mg/dL")
            
            peak = results.get('peak_glucose', {})
            if peak.get('mean'):
                click.echo(f"峰值血糖: {peak['mean']:.1f} ± {peak['std']:.1f} mg/dL")
            
            iauc = results.get('iauc_2h', {})
            if iauc.get('mean'):
                click.echo(f"iAUC (2h): {iauc['mean']:.1f} ± {iauc['std']:.1f}")
            
    except Exception as e:
        click.echo(f"错误: {e}", err=True)


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
