"""
GlycoNutri Web API
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Optional
import pandas as pd
import json
from datetime import datetime

from glyconutri.cgm_adapters import load_cgm_data
from glyconutri.cgm import calculate_tir, calculate_gv
from glyconutri.food import get_food_info, search_foods
from glyconutri.analysis import analyze_glucose
from glyconutri.postmeal import PostMealAnalysis, create_meal_session

app = FastAPI(title="GlycoNutri API")

# ============ API 端点 ============

@app.get("/api/foods/search")
def api_search_foods(q: str):
    """搜索食物"""
    results = search_foods(q)
    return {"results": results[:10]}


@app.get("/api/foods/{food_name}")
def api_get_food(food_name: str, weight: float = None):
    """获取食物信息"""
    carbs = None
    if weight:
        from glyconutri.gi_database import get_carbs
        carbs_per_100g = get_carbs(food_name)
        if carbs_per_100g:
            carbs = carbs_per_100g * weight / 100
    
    info = get_food_info(food_name, carbs)
    return info or {"error": "未找到该食物"}


@app.post("/api/analyze")
async def api_analyze(
    file: UploadFile = File(None),
    device: str = Form("auto")
):
    """分析 CGM 数据"""
    if not file:
        return {"error": "请上传 CGM 数据文件"}
    
    # 保存临时文件
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        df = load_cgm_data(tmp_path, device)
        results = analyze_glucose(df)
        
        return {
            "success": True,
            "data_points": len(df),
            "time_range": {
                "start": df['timestamp'].min().isoformat(),
                "end": df['timestamp'].max().isoformat()
            },
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        os.unlink(tmp_path)


@app.post("/api/meal/analyze")
def api_meal_analyze(
    cgm_data: str = Form(...),
    foods: str = Form(...),
    meal_time: str = Form(...)
):
    """餐后血糖分析"""
    try:
        # 解析 CGM 数据
        cgm_json = json.loads(cgm_data)
        df = pd.DataFrame(cgm_json)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 解析食物
        foods_list = json.loads(foods)
        
        # 解析时间
        time_obj = datetime.fromisoformat(meal_time.replace('Z', '+00:00'))
        
        # 创建餐次
        session = create_meal_session(foods_list, time_obj)
        
        # 分析
        if not session.meals:
            return {"error": "食物列表为空"}
        
        analysis = PostMealAnalysis(session.meals[0], df)
        
        baseline = analysis.calculate_baseline()
        peak = analysis.calculate_peak()
        response = analysis.response_magnitude()
        iauc = analysis.calculate_incremental_auc()
        
        return {
            "success": True,
            "meal": {
                "time": meal_time,
                "foods": [m.to_dict() for m in session.meals],
                "total_carbs": session.total_carbs,
                "total_gl": session.total_gl,
                "weighted_gi": session.weighted_gi
            },
            "glucose_response": {
                "baseline": baseline,
                "peak": peak,
                "response_magnitude": response,
                "iauc_2h": iauc
            }
        }
    except Exception as e:
        return {"error": str(e)}


# ============ HTML 页面 ============

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GlycoNutri - 血糖营养计算工具</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 14px; }
        
        .tabs {
            display: flex;
            border-bottom: 1px solid #eee;
        }
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #667eea;
            color: #667eea;
            font-weight: 600;
        }
        
        .content { padding: 30px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
        input[type="text"], input[type="number"], input[type="datetime-local"], select {
            width: 100%;
            padding: 12px;
            border: 2px solid #eee;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus { border-color: #667eea; outline: none; }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 30px;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        
        .food-item {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
            align-items: center;
        }
        .food-item input { flex: 1; }
        .food-item .weight { width: 100px; }
        .btn-add {
            background: #eee;
            color: #333;
            padding: 10px;
            margin-bottom: 20px;
        }
        .btn-remove {
            background: #ff6b6b;
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 8px;
            cursor: pointer;
        }
        
        .result {
            background: #f8f9ff;
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }
        .result h3 { color: #667eea; margin-bottom: 15px; }
        .result-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        .result-item {
            background: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .result-item .value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .result-item .label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .result-item.highlight {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .result-item.highlight .value, .result-item.highlight .label { color: white; }
        
        .food-result {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .food-result .name { font-weight: 600; color: #333; }
        .food-result .info { font-size: 14px; color: #666; margin-top: 5px; }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        @media (max-width: 600px) {
            .result-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🩸 GlycoNutri</h1>
            <p>血糖营养计算工具 for 医生</p>
        </div>
        
        <div class="tabs">
            <div class="tab active" data-tab="cgm">CGM 分析</div>
            <div class="tab" data-tab="meal">餐后分析</div>
            <div class="tab" data-tab="food">食物查询</div>
        </div>
        
        <div class="content">
            <!-- CGM 分析 -->
            <div class="tab-content active" id="cgm">
                <div class="form-group">
                    <label>上传 CGM 数据文件</label>
                    <input type="file" id="cgmFile" accept=".csv,.json">
                </div>
                <div class="form-group">
                    <label>设备类型</label>
                    <select id="cgmDevice">
                        <option value="auto">自动检测</option>
                        <option value="dexcom">Dexcom</option>
                        <option value="libre">FreeStyle Libre</option>
                        <option value="medtronic">Medtronic</option>
                    </select>
                </div>
                <button class="btn" onclick="analyzeCGM()">分析血糖数据</button>
                <div id="cgmResult"></div>
            </div>
            
            <!-- 餐后分析 -->
            <div class="tab-content" id="meal">
                <div class="form-group">
                    <label>餐食时间</label>
                    <input type="datetime-local" id="mealTime">
                </div>
                <div class="form-group">
                    <label>食物列表</label>
                    <div id="foodList">
                        <div class="food-item">
                            <input type="text" placeholder="食物名称" class="food-name">
                            <input type="number" placeholder="重量(g)" class="food-weight">
                            <button class="btn-remove" onclick="this.parentElement.remove()">×</button>
                        </div>
                    </div>
                    <button class="btn btn-add" onclick="addFood()">+ 添加食物</button>
                </div>
                <button class="btn" onclick="analyzeMeal()">分析餐后血糖</button>
                <div id="mealResult"></div>
            </div>
            
            <!-- 食物查询 -->
            <div class="tab-content" id="food">
                <div class="form-group">
                    <label>搜索食物</label>
                    <input type="text" id="foodSearch" placeholder="输入食物名称，如：米饭、苹果">
                </div>
                <button class="btn" onclick="searchFood()">搜索</button>
                <div id="foodResult"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab 切换
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab).classList.add('active');
            });
        });
        
        // 添加食物
        function addFood() {
            const div = document.createElement('div');
            div.className = 'food-item';
            div.innerHTML = `
                <input type="text" placeholder="食物名称" class="food-name">
                <input type="number" placeholder="重量(g)" class="food-weight">
                <button class="btn-remove" onclick="this.parentElement.remove()">×</button>
            `;
            document.getElementById('foodList').appendChild(div);
        }
        
        // 搜索食物
        async function searchFood() {
            const query = document.getElementById('foodSearch').value;
            if (!query) return;
            
            const res = await fetch(`/api/foods/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            
            let html = '<div class="result">';
            html += '<h3>搜索结果</h3>';
            if (data.results && data.results.length > 0) {
                data.results.forEach(f => {
                    html += `
                        <div class="food-result">
                            <div class="name">${f.name}</div>
                            <div class="info">GI: ${f.gi} (${f.gi_category}GI) | 碳水: ${f.carbs_per_100g || 'N/A'}g/100g</div>
                        </div>
                    `;
                });
            } else {
                html += '<p>未找到匹配的食物</p>';
            }
            html += '</div>';
            document.getElementById('foodResult').innerHTML = html;
        }
        
        // 分析 CGM
        async function analyzeCGM() {
            const fileInput = document.getElementById('cgmFile');
            const device = document.getElementById('cgmDevice').value;
            
            if (!fileInput.files[0]) {
                alert('请选择 CGM 数据文件');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('device', device);
            
            document.getElementById('cgmResult').innerHTML = '<div class="loading">分析中...</div>';
            
            try {
                const res = await fetch('/api/analyze', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                
                if (data.error) {
                    document.getElementById('cgmResult').innerHTML = `<div class="result"><p style="color:red">${data.error}</p></div>`;
                    return;
                }
                
                const r = data.results;
                document.getElementById('cgmResult').innerHTML = `
                    <div class="result">
                        <h3>📊 血糖分析结果</h3>
                        <div class="result-grid">
                            <div class="result-item highlight">
                                <div class="value">${r.tir.toFixed(1)}%</div>
                                <div class="label">Time in Range</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${r.gv.toFixed(1)}%</div>
                                <div class="label">血糖波动</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${r.mean_glucose.toFixed(1)}</div>
                                <div class="label">平均血糖 (mg/dL)</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${r.std_glucose.toFixed(1)}</div>
                                <div class="label">标准差</div>
                            </div>
                        </div>
                    </div>
                `;
            } catch (e) {
                document.getElementById('cgmResult').innerHTML = `<div class="result"><p style="color:red">错误: ${e}</p></div>`;
            }
        }
        
        // 分析餐后血糖
        async function analyzeMeal() {
            const mealTime = document.getElementById('mealTime').value;
            const foodItems = document.querySelectorAll('#foodList .food-item');
            
            const foods = [];
            foodItems.forEach(item => {
                const name = item.querySelector('.food-name').value;
                const weight = parseFloat(item.querySelector('.food-weight').value) || 100;
                if (name) foods.push({name, weight});
            });
            
            if (!mealTime || foods.length === 0) {
                alert('请填写餐食时间和至少一种食物');
                return;
            }
            
            // 这里需要 CGM 数据，暂时模拟
            document.getElementById('mealResult').innerHTML = '<div class="loading">请先上传 CGM 数据进行餐后分析</div>';
        }
        
        // 设置默认时间
        document.getElementById('mealTime').value = new Date().toISOString().slice(0, 16);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
