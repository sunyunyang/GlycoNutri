"""
GlycoNutri Web - 完整版
"""

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import base64
import io

from glyconutri.cgm_adapters import load_cgm_data
from glyconutri.cgm import calculate_tir, calculate_gv
from glyconutri.food import get_food_info, search_foods, list_foods_by_gi_category
from glyconutri.analysis import analyze_glucose
from glyconutri.postmeal import PostMealAnalysis, create_meal_session, RepeatedMealAnalyzer

app = FastAPI(title="GlycoNutri", version="0.4")

# 确保上传目录存在
UPLOAD_DIR = "/tmp/glyconutri_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============ 首页 ============

HTML_HOME = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GlycoNutri - 血糖营养工具</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* 头部 */
        .header {
            text-align: center;
            color: white;
            padding: 40px 0;
        }
        .header h1 {
            font-size: 48px;
            background: linear-gradient(135deg, #00d9ff, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .header p { font-size: 18px; opacity: 0.8; }
        
        /* 主卡片 */
        .main-card {
            background: white;
            border-radius: 24px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        /* 标签页 */
        .tabs {
            display: flex;
            background: #f8f9fc;
            border-bottom: 1px solid #e5e7eb;
        }
        .tab {
            flex: 1;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            font-weight: 600;
            color: #6b7280;
            transition: all 0.3s;
            border-bottom: 3px solid transparent;
        }
        .tab:hover { background: #f3f4f6; }
        .tab.active {
            color: #a855f7;
            border-bottom-color: #a855f7;
            background: white;
        }
        
        /* 内容区 */
        .content { padding: 30px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        /* 表单元素 */
        .form-group { margin-bottom: 24px; }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #1f2937;
        }
        .help-text {
            font-size: 12px;
            color: #6b7280;
            margin-top: 4px;
        }
        input[type="text"], input[type="number"], input[type="datetime-local"], 
        input[type="date"], select, textarea {
            width: 100%;
            padding: 14px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s;
            background: #f9fafb;
        }
        input:focus, select:focus, textarea:focus {
            border-color: #a855f7;
            outline: none;
            background: white;
            box-shadow: 0 0 0 4px rgba(168,85,247,0.1);
        }
        
        /* 按钮 */
        .btn {
            background: linear-gradient(135deg, #a855f7, #6366f1);
            color: white;
            border: none;
            padding: 16px 32px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(168,85,247,0.3); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
        }
        .btn-secondary:hover { background: #e5e7eb; }
        
        .btn-danger {
            background: #fee2e2;
            color: #dc2626;
        }
        
        /* 文件上传 */
        .file-upload {
            border: 3px dashed #e5e7eb;
            border-radius: 16px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .file-upload:hover { border-color: #a855f7; background: #faf5ff; }
        .file-upload.dragover { border-color: #a855f7; background: #f3e8ff; }
        
        /* 食物列表 */
        .food-list { margin-bottom: 20px; }
        .food-item {
            display: flex;
            gap: 12px;
            margin-bottom: 12px;
            align-items: center;
            padding: 16px;
            background: #f9fafb;
            border-radius: 12px;
        }
        .food-item input { flex: 1; }
        .food-item .food-info {
            flex: 2;
            font-size: 14px;
            color: #6b7280;
        }
        .btn-remove {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            border: none;
            background: #fee2e2;
            color: #dc2626;
            cursor: pointer;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* 结果展示 */
        .result-card {
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
            border-radius: 16px;
            padding: 24px;
            margin-top: 24px;
        }
        .result-card h3 {
            color: #0369a1;
            margin-bottom: 20px;
            font-size: 20px;
        }
        
        .result-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
        }
        .result-item {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .result-item.highlight {
            background: linear-gradient(135deg, #a855f7, #6366f1);
            color: white;
        }
        .result-item .value {
            font-size: 32px;
            font-weight: bold;
        }
        .result-item .label {
            font-size: 13px;
            margin-top: 4px;
            opacity: 0.8;
        }
        
        /* 食物结果 */
        .food-result-item {
            background: white;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .food-result-item .name { font-weight: 600; }
        .food-result-item .details { font-size: 14px; color: #6b7280; }
        
        /* 标签 */
        .tag {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .tag-low { background: #dcfce7; color: #166534; }
        .tag-medium { background: #fef3c7; color: #92400e; }
        .tag-high { background: #fee2e2; color: #dc2626; }
        
        /* 加载动画 */
        .loading {
            text-align: center;
            padding: 40px;
            color: #6b7280;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #e5e7eb;
            border-top-color: #a855f7;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        /* 历史记录 */
        .history-item {
            padding: 16px;
            border-bottom: 1px solid #e5e7eb;
        }
        .history-item:last-child { border-bottom: none; }
        .history-time { font-size: 14px; color: #6b7280; }
        .history-foods { margin-top: 8px; }
        
        /* 页脚 */
        .footer {
            text-align: center;
            padding: 30px;
            color: rgba(255,255,255,0.6);
            font-size: 14px;
        }
        
        @media (max-width: 768px) {
            .header h1 { font-size: 32px; }
            .tabs { flex-wrap: wrap; }
            .tab { flex: none; width: 33.33%; }
            .food-item { flex-direction: column; align-items: stretch; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🩸 GlycoNutri</h1>
            <p>血糖营养计算工具 for 医生 & 患者</p>
        </div>
        
        <div class="main-card">
            <div class="tabs">
                <div class="tab active" data-tab="cgm">📊 CGM 分析</div>
                <div class="tab" data-tab="meal">🍽️ 餐后分析</div>
                <div class="tab" data-tab="meal-nutrition">🥗 餐食分析</div>
                <div class="tab" data-tab="exercise">🏃 运动分析</div>
                <div class="tab" data-tab="sleep">😴 睡眠分析</div>
                <div class="tab" data-tab="medication">💊 药物分析</div>
                <div class="tab" data-tab="food">🔍 食物查询</div>
                <div class="tab" data-tab="history">📋 历史记录</div>
            </div>
            
            <div class="content">
                <!-- CGM 分析 -->
                <div class="tab-content active" id="cgm">
                    <div class="file-upload" id="dropZone">
                        <input type="file" id="cgmFile" accept=".csv,.json,.txt" style="display:none">
                        <div style="font-size: 48px; margin-bottom: 16px;">📁</div>
                        <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">
                            点击或拖拽上传 CGM 数据
                        </div>
                        <div style="color: #6b7280;">
                            支持 CSV、JSON、TXT 格式 (Dexcom, Libre, Medtronic)
                        </div>
                    </div>
                    
                    <div class="form-group" style="margin-top: 24px;">
                        <label>或手动输入血糖数据</label>
                        <textarea id="cgmText" rows="4" placeholder="格式: timestamp,glucose
2026-02-15 08:00,95
2026-02-15 08:15,98
..."></textarea>
                    </div>
                    
                    <button class="btn" onclick="analyzeCGM()" style="width: 100%;">
                        分析血糖数据
                    </button>
                    
                    <div id="cgmResult"></div>
                </div>
                
                <!-- 餐后分析 -->
                <div class="tab-content" id="meal">
                    <div class="form-group">
                        <label>📅 餐食时间</label>
                        <input type="datetime-local" id="mealTime">
                    </div>
                    
                    <label>🍎 食物列表</label>
                    <div class="food-list" id="foodList">
                        <div class="food-item">
                            <input type="text" placeholder="食物名称 (如: 米饭)" class="food-name">
                            <input type="number" placeholder="重量(g)" class="food-weight" value="100">
                            <div class="food-info" id="foodInfo0"></div>
                            <button class="btn-remove" onclick="removeFood(this)">×</button>
                        </div>
                    </div>
                    
                    <button class="btn btn-secondary" onclick="addFood()" style="margin-bottom: 24px;">
                        + 添加食物
                    </button>
                    
                    <div class="form-group">
                        <label>📊 CGM 数据 (餐后分析必需)</label>
                        <div class="file-upload" id="cgmDropZone" style="padding: 20px;">
                            <input type="file" id="mealCgmFile" accept=".csv,.json,.txt" style="display:none">
                            <div>点击上传 CGM 数据文件</div>
                        </div>
                        <div class="help-text">或直接输入血糖数据</div>
                        <textarea id="mealCgmText" rows="3" placeholder="timestamp,glucose 格式"></textarea>
                    </div>
                    
                    <button class="btn" onclick="analyzeMeal()" style="width: 100%;">
                        分析餐后血糖响应
                    </button>
                    
                    <div id="mealResult"></div>
                </div>
                
                <!-- 餐食营养分析 (新) -->
                <div class="tab-content" id="meal-nutrition">
                    <div class="form-group">
                        <label>🍽️ 餐次</label>
                        <select id="nutritionMealType">
                            <option value="早餐">早餐</option>
                            <option value="午餐">午餐</option>
                            <option value="晚餐">晚餐</option>
                            <option value="加餐">加餐</option>
                        </select>
                    </div>
                    
                    <label>🥗 食物列表</label>
                    <div class="food-list" id="nutritionFoodList">
                        <div class="food-item">
                            <input type="text" placeholder="食物名称 (如: 米饭)" class="food-name-nutrition">
                            <input type="number" placeholder="重量(g)" class="food-weight-nutrition" value="100">
                            <button class="btn-remove" onclick="removeNutritionFood(this)">×</button>
                        </div>
                    </div>
                    
                    <button class="btn btn-secondary" onclick="addNutritionFood()" style="margin-bottom: 24px;">
                        + 添加食物
                    </button>
                    
                    <button class="btn" onclick="analyzeNutrition()" style="width: 100%;">
                        分析餐食营养
                    </button>
                    
                    <div id="nutritionResult"></div>
                </div>
                
                <!-- 运动分析 -->
                <div class="tab-content" id="exercise">
                    <div class="form-group">
                        <label>🏃 运动类型</label>
                        <select id="exerciseType">
                            <option value="走路">走路 - 轻度</option>
                            <option value="慢跑">慢跑 - 中度</option>
                            <option value="跑步">跑步 - 高强度</option>
                            <option value="骑行">骑行 - 中度</option>
                            <option value="游泳">游泳 - 中度</option>
                            <option value="瑜伽">瑜伽 - 轻度</option>
                            <option value="健身">健身 - 高强度</option>
                            <option value="球类">球类 - 高强度</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>⏱️ 时长 (分钟)</label>
                        <input type="number" id="exerciseDuration" value="30" min="5" max="180">
                    </div>
                    
                    <div class="form-group">
                        <label>📅 运动开始时间</label>
                        <input type="datetime-local" id="exerciseTime">
                    </div>
                    
                    <div class="form-group">
                        <label>📊 CGM 数据</label>
                        <textarea id="exerciseCgmText" rows="3" placeholder="上传或输入血糖数据"></textarea>
                    </div>
                    
                    <button class="btn" onclick="analyzeExercise()" style="width: 100%;">
                        分析运动血糖影响
                    </button>
                    
                    <div id="exerciseResult"></div>
                </div>
                
                <!-- 睡眠分析 -->
                <div class="tab-content" id="sleep">
                    <div class="form-group">
                        <label="😴 入睡时间</label>
                        <input type="datetime-local" id="sleepTime">
                    </div>
                    
                    <div class="form-group">
                        <label">☀️ 醒来时间</label>
                        <input type="datetime-local" id="wakeTime">
                    </div>
                    
                    <div class="form-group">
                        <label>📊 CGM 数据</label>
                        <textarea id="sleepCgmText" rows="3" placeholder="上传或输入血糖数据"></textarea>
                    </div>
                    
                    <button class="btn" onclick="analyzeSleep()" style="width: 100%;">
                        分析睡眠血糖
                    </button>
                    
                    <div id="sleepResult"></div>
                </div>
                
                <!-- 药物分析 -->
                <div class="tab-content" id="medication">
                    <div class="form-group">
                        <label>💊 药物类型</label>
                        <select id="medicationType" onchange="updateMedicationList()">
                            <option value="口服">口服降糖药</option>
                            <option value="胰岛素">胰岛素</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>💉 药物名称</label>
                        <select id="medicationName">
                            <option value="二甲双胍">二甲双胍</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>📝 剂量</label>
                        <input type="number" id="medicationDosage" placeholder="剂量(mg)或单位(U)" step="0.5">
                    </div>
                    
                    <div class="form-group">
                        <label>📅 服药时间</label>
                        <input type="datetime-local" id="medicationTime">
                    </div>
                    
                    <div class="form-group">
                        <label>📊 CGM 数据</label>
                        <textarea id="medicationCgmText" rows="3" placeholder="上传或输入血糖数据"></textarea>
                    </div>
                    
                    <button class="btn" onclick="analyzeMedication()" style="width: 100%;">
                        分析药物血糖影响
                    </button>
                    
                    <div id="medicationResult"></div>
                </div>
                
                <!-- 食物查询 -->
                <div class="tab-content" id="food">
                    <div class="form-group">
                        <label>🔍 搜索食物</label>
                        <input type="text" id="foodSearch" placeholder="输入食物名称，如：米饭、苹果、香蕉">
                    </div>
                    
                    <button class="btn" onclick="searchFood()" style="width: 100%; margin-bottom: 24px;">
                        搜索
                    </button>
                    
                    <div class="form-group">
                        <label>或按 GI 类别浏览</label>
                        <div style="display: flex; gap: 12px;">
                            <button class="btn btn-secondary" onclick="browseGI('低')">低 GI</button>
                            <button class="btn btn-secondary" onclick="browseGI('中')">中 GI</button>
                            <button class="btn btn-secondary" onclick="browseGI('高')">高 GI</button>
                        </div>
                    </div>
                    
                    <div id="foodResult"></div>
                </div>
                
                <!-- 历史记录 -->
                <div class="tab-content" id="history">
                    <div id="historyList">
                        <div class="loading">暂无历史记录</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            GlycoNutri v0.4 | 血糖营养计算工具
        </div>
    </div>
    
    <script>
        // 全局变量
        let cgmData = null;
        
        // Tab 切换
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab).classList.add('active');
            });
        });
        
        // 文件上传
        const setupFileUpload = (dropZoneId, fileInputId, callback) => {
            const dropZone = document.getElementById(dropZoneId);
            const fileInput = document.getElementById(fileInputId);
            
            dropZone.addEventListener('click', () => fileInput.click());
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });
            dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                if (e.dataTransfer.files.length) {
                    fileInput.files = e.dataTransfer.files;
                    callback(e.dataTransfer.files[0]);
                }
            });
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length) callback(fileInput.files[0]);
            });
        };
        
        setupFileUpload('dropZone', 'cgmFile', (file) => {
            document.getElementById('cgmResult').innerHTML = '<div class="loading"><div class="spinner"></div>正在读取文件...</div>';
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target.result;
                document.getElementById('cgmText').value = text;
                analyzeCGM();
            };
            reader.readAsText(file);
        });
        
        setupFileUpload('cgmDropZone', 'mealCgmFile', (file) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('mealCgmText').value = e.target.result;
            };
            reader.readAsText(file);
        });
        
        // 添加食物
        let foodCount = 1;
        function addFood() {
            const div = document.createElement('div');
            div.className = 'food-item';
            div.innerHTML = `
                <input type="text" placeholder="食物名称" class="food-name" onchange="updateFoodInfo(this)">
                <input type="number" placeholder="重量(g)" class="food-weight" value="100" onchange="updateFoodInfo(this)">
                <div class="food-info" id="foodInfo${foodCount}"></div>
                <button class="btn-remove" onclick="removeFood(this)">×</button>
            `;
            document.getElementById('foodList').appendChild(div);
            foodCount++;
        }
        
        function removeFood(btn) {
            const items = document.querySelectorAll('#foodList .food-item');
            if (items.length > 1) btn.parentElement.remove();
        }
        
        // 餐食营养分析 - 添加食物
        let nutritionFoodCount = 1;
        function addNutritionFood() {
            const div = document.createElement('div');
            div.className = 'food-item';
            div.innerHTML = `
                <input type="text" placeholder="食物名称" class="food-name-nutrition">
                <input type="number" placeholder="重量(g)" class="food-weight-nutrition" value="100">
                <button class="btn-remove" onclick="removeNutritionFood(this)">×</button>
            `;
            document.getElementById('nutritionFoodList').appendChild(div);
            nutritionFoodCount++;
        }
        
        function removeNutritionFood(btn) {
            const items = document.querySelectorAll('#nutritionFoodList .food-item');
            if (items.length > 1) btn.parentElement.remove();
        }
        
        // 餐食营养分析
        async function analyzeNutrition() {
            const mealType = document.getElementById('nutritionMealType').value;
            const foodItems = document.querySelectorAll('#nutritionFoodList .food-item');
            
            const foods = [];
            foodItems.forEach(item => {
                const name = item.querySelector('.food-name-nutrition').value;
                const weight = parseFloat(item.querySelector('.food-weight-nutrition').value) || 100;
                if (name) foods.push({name, weight});
            });
            
            if (foods.length === 0) {
                alert('请添加食物');
                return;
            }
            
            document.getElementById('nutritionResult').innerHTML = '<div class="loading"><div class="spinner"></div>分析中...</div>';
            
            try {
                const res = await fetch('/api/meal/nutrition', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        meal_name: mealType,
                        foods: foods
                    })
                });
                const data = await res.json();
                
                if (data.error) {
                    document.getElementById('nutritionResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">${data.error}</p></div>`;
                    return;
                }
                
                const m = data.meal.summary;
                const balance = data.nutrition_balance;
                const glycemic = data.glycemic_risk;
                const recs = data.recommendations;
                
                let foodsHtml = data.meal.foods.map(f => `
                    <div class="food-result-item">
                        <div>
                            <div class="name">${f.name} (${f.weight}g)</div>
                            <div class="details">碳水: ${f.carbs}g | 蛋白: ${f.protein}g | 脂肪: ${f.fat}g</div>
                        </div>
                        <span class="tag tag-${f.gl < 10 ? 'low' : f.gl < 20 ? 'medium' : 'high'}">GL: ${f.gl}</span>
                    </div>
                `).join('');
                
                document.getElementById('nutritionResult').innerHTML = `
                    <div class="result-card">
                        <h3>🥗 ${mealType} 营养分析</h3>
                        
                        <h4 style="margin:16px 0 8px">食物列表</h4>
                        ${foodsHtml}
                        
                        <h4 style="margin:16px 0 8px">营养汇总</h4>
                        <div class="result-grid">
                            <div class="result-item">
                                <div class="value">${m.total_carbs}g</div>
                                <div class="label">碳水</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${m.total_protein}g</div>
                                <div class="label">蛋白质</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${m.total_fat}g</div>
                                <div class="label">脂肪</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${m.total_fiber}g</div>
                                <div class="label">纤维</div>
                            </div>
                        </div>
                        
                        <h4 style="margin:16px 0 8px">升糖效应</h4>
                        <div class="result-grid">
                            <div class="result-item">
                                <div class="value">${m.weighted_gi}</div>
                                <div class="label">加权GI</div>
                            </div>
                            <div class="result-item highlight">
                                <div class="value">${m.total_gl}</div>
                                <div class="label">总GL</div>
                            </div>
                        </div>
                        
                        <h4 style="margin:16px 0 8px">营养结构</h4>
                        <div style="display:flex;gap:8px;margin-bottom:8px">
                            <span class="tag" style="background:#fef3c7">碳水 ${balance.ratio.carbs}%</span>
                            <span class="tag" style="background:#dbeafe">蛋白 ${balance.ratio.protein}%</span>
                            <span class="tag" style="background:#fce7f3">脂肪 ${balance.ratio.fat}%</span>
                        </div>
                        
                        <h4 style="margin:16px 0 8px">评估</h4>
                        <div style="padding:12px;background:#f0fdf4;border-radius:8px;margin-bottom:16px">
                            <strong>${recs.summary}</strong>
                        </div>
                        
                        ${recs.recommendations.length > 0 ? `
                        <h4 style="margin:16px 0 8px">建议</h4>
                        <ul style="padding-left:20px;color:#374151">
                            ${recs.recommendations.map(r => `<li style="margin-bottom:4px">${r.suggestion}</li>`).join('')}
                        </ul>
                        ` : ''}
                    </div>
                `;
                
                // 保存到历史记录
                saveToHistory('meal-nutrition', mealType, data);
                
            } catch (e) {
                document.getElementById('nutritionResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">错误: ${e.message}</p></div>`;
            }
        }
        
        // 保存到历史记录
        
        // 更新食物信息
        async function updateFoodInfo(input) {
            const item = input.parentElement;
            const name = item.querySelector('.food-name').value;
            const weight = parseFloat(item.querySelector('.food-weight').value) || 100;
            const infoDiv = item.querySelector('.food-info');
            
            if (!name) return;
            
            try {
                const res = await fetch(`/api/food/info?name=${encodeURIComponent(name)}&weight=${weight}`);
                const data = await res.json();
                
                if (data.gi) {
                    const gl = (data.gi * (data.carbs || 0) / 100).toFixed(1);
                    infoDiv.innerHTML = `
                        <span class="tag tag-${data.gi_category === '低' ? 'low' : data.gi_category === '中' ? 'medium' : 'high'}">
                            GI: ${data.gi}
                        </span>
                        ${data.carbs ? `<span style="margin-left:8px">碳水: ${data.carbs.toFixed(1)}g</span>` : ''}
                        ${gl > 0 ? `<span style="margin-left:8px">GL: ${gl}</span>` : ''}
                    `;
                }
            } catch (e) {}
        }
        
        // 分析 CGM
        async function analyzeCGM() {
            const text = document.getElementById('cgmText').value;
            if (!text.trim()) {
                alert('请上传 CGM 文件或输入数据');
                return;
            }
            
            document.getElementById('cgmResult').innerHTML = '<div class="loading"><div class="spinner"></div>分析中...</div>';
            
            try {
                const res = await fetch('/api/cgm/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({data: text})
                });
                const data = await res.json();
                
                if (data.error) {
                    document.getElementById('cgmResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">${data.error}</p></div>`;
                    return;
                }
                
                const r = data.results;
                cgmData = data.cgm_data;
                
                document.getElementById('cgmResult').innerHTML = `
                    <div class="result-card">
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
                                <div class="value">${r.mean_glucose.toFixed(0)}</div>
                                <div class="label">平均血糖</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${r.std_glucose.toFixed(1)}</div>
                                <div class="label">标准差</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${r.min_glucose.toFixed(0)}</div>
                                <div class="label">最低血糖</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${r.max_glucose.toFixed(0)}</div>
                                <div class="label">最高血糖</div>
                            </div>
                        </div>
                        <div style="margin-top:16px; font-size:14px; color:#6b7280">
                            数据点数: ${data.data_points} | 时间: ${data.time_range}
                        </div>
                    </div>
                `;
                
                // 保存到历史
                saveHistory('cgm', {results: r, time_range: data.time_range});
                
            } catch (e) {
                document.getElementById('cgmResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">错误: ${e}</p></div>`;
            }
        }
        
        // 分析餐后血糖
        async function analyzeMeal() {
            const mealTime = document.getElementById('mealTime').value;
            const foodItems = document.querySelectorAll('#foodList .food-item');
            const cgmText = document.getElementById('mealCgmText').value;
            
            const foods = [];
            foodItems.forEach(item => {
                const name = item.querySelector('.food-name').value;
                const weight = parseFloat(item.querySelector('.food-weight').value) || 100;
                if (name) foods.push({name, weight});
            });
            
            if (!mealTime || foods.length === 0) {
                alert('请填写餐食时间和食物');
                return;
            }
            
            document.getElementById('mealResult').innerHTML = '<div class="loading"><div class="spinner"></div>分析中...</div>';
            
            try {
                const res = await fetch('/api/meal/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        meal_time: mealTime,
                        foods: foods,
                        cgm_data: cgmText || (cgmData ? JSON.stringify(cgmData) : null)
                    })
                });
                const data = await res.json();
                
                if (data.error) {
                    document.getElementById('mealResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">${data.error}</p></div>`;
                    return;
                }
                
                const m = data.meal;
                const g = data.glucose_response;
                
                let foodsHtml = m.foods.map(f => `
                    <div class="food-result-item">
                        <div>
                            <div class="name">${f.food_name} (${f.weight}g)</div>
                            <div class="details">GI: ${f.gi} | 碳水: ${f.carbs?.toFixed(1)}g</div>
                        </div>
                        <span class="tag tag-${f.gl < 10 ? 'low' : f.gl < 20 ? 'medium' : 'high'}">GL: ${f.gl?.toFixed(1)}</span>
                    </div>
                `).join('');
                
                document.getElementById('mealResult').innerHTML = `
                    <div class="result-card">
                        <h3>🍽️ 餐后血糖分析</h3>
                        <div style="margin-bottom:16px">
                            <strong>餐食时间:</strong> ${mealTime}
                        </div>
                        <div style="margin-bottom:16px">
                            <strong>食物:</strong>
                            ${foodsHtml}
                        </div>
                        <div class="result-grid">
                            <div class="result-item">
                                <div class="value">${m.total_carbs?.toFixed(1)}g</div>
                                <div class="label">总碳水</div>
                            </div>
                            <div class="result-item highlight">
                                <div class="value">${m.total_gl?.toFixed(1)}</div>
                                <div class="label">总 GL</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${m.weighted_gi?.toFixed(0)}</div>
                                <div class="label">加权 GI</div>
                            </div>
                        </div>
                        ${g.baseline ? `
                        <div style="margin-top:16px; padding-top:16px; border-top:1px solid #e5e7eb">
                            <strong>血糖响应:</strong>
                            <div class="result-grid" style="margin-top:12px">
                                <div class="result-item">
                                    <div class="value">${g.baseline?.toFixed(0)}</div>
                                    <div class="label">餐前基线</div>
                                </div>
                                <div class="result-item">
                                    <div class="value">${g.peak?.toFixed(0)}</div>
                                    <div class="label">餐后峰值</div>
                                </div>
                                <div class="result-item">
                                    <div class="value">${g.response_magnitude?.toFixed(0)}</div>
                                    <div class="label">血糖增幅</div>
                                </div>
                            </div>
                        </div>
                        ` : '<div style="margin-top:16px; color:#6b7280">⚠️ 请提供 CGM 数据以获取血糖响应分析</div>'}
                    </div>
                `;
                
                saveHistory('meal', {meal_time: mealTime, foods: m.foods, glucose_response: g});
                
            } catch (e) {
                document.getElementById('mealResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">错误: ${e}</p></div>`;
            }
        }
        
        // 搜索食物
        async function searchFood() {
            const query = document.getElementById('foodSearch').value;
            if (!query) return;
            
            const res = await fetch(`/api/foods/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            
            let html = '<div class="result-card">';
            if (data.results && data.results.length > 0) {
                data.results.forEach(f => {
                    html += `
                        <div class="food-result-item">
                            <div>
                                <div class="name">${f.name}</div>
                                <div class="details">GI: ${f.gi} | 碳水: ${f.carbs_per_100g || 'N/A'}g/100g</div>
                            </div>
                            <span class="tag tag-${f.gi_category === '低' ? 'low' : f.gi_category === '中' ? 'medium' : 'high'}">${f.gi_category}GI</span>
                        </div>
                    `;
                });
            } else {
                html += '<p>未找到匹配的食物</p>';
            }
            html += '</div>';
            document.getElementById('foodResult').innerHTML = html;
        }
        
        async function browseGI(category) {
            const res = await fetch(`/api/foods/category/${category}`);
            const data = await res.json();
            
            let html = `<div class="result-card"><h3>${category}GI 食物</h3>`;
            data.foods.forEach(f => {
                html += `
                    <div class="food-result-item">
                        <div>
                            <div class="name">${f.name}</div>
                            <div class="details">GI: ${f.gi} | 碳水: ${f.carbs_per_100g || 'N/A'}g</div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            document.getElementById('foodResult').innerHTML = html;
        }
        
        // 历史记录
        function saveHistory(type, data) {
            const history = JSON.parse(localStorage.getItem('glyconutri_history') || '[]');
            history.unshift({type, data, time: new Date().toISOString()});
            localStorage.setItem('glyconutri_history', JSON.stringify(history.slice(0, 20)));
        }
        
        function loadHistory() {
            const history = JSON.parse(localStorage.getItem('glyconutri_history') || '[]');
            if (history.length === 0) {
                document.getElementById('historyList').innerHTML = '<div class="loading">暂无历史记录</div>';
                return;
            }
            
            let html = '';
            history.forEach(h => {
                const time = new Date(h.time).toLocaleString('zh-CN');
                if (h.type === 'cgm') {
                    html += `
                        <div class="history-item">
                            <div class="history-time">📊 ${time}</div>
                            <div>TIR: ${h.data.results?.tir?.toFixed(1)}% | 平均血糖: ${h.data.results?.mean_glucose?.toFixed(0)}</div>
                        </div>
                    `;
                } else if (h.type === 'meal') {
                    const foods = h.data.foods?.map(f => f.food_name).join(', ') || '';
                    html += `
                        <div class="history-item">
                            <div class="history-time">🍽️ ${time}</div>
                            <div>${foods}</div>
                            <div class="history-foods">GL: ${h.data.glucose_response?.total_gl || 'N/A'}</div>
                        </div>
                    `;
                }
            });
            document.getElementById('historyList').innerHTML = html;
        }
        
        // 运动分析
        async function analyzeExercise() {
            const exerciseType = document.getElementById('exerciseType').value;
            const duration = parseInt(document.getElementById('exerciseDuration').value) || 30;
            const exerciseTime = document.getElementById('exerciseTime').value;
            const cgmText = document.getElementById('exerciseCgmText').value;
            
            if (!exerciseTime) {
                alert('请选择运动时间');
                return;
            }
            if (!cgmText.trim()) {
                alert('请输入血糖数据');
                return;
            }
            
            document.getElementById('exerciseResult').innerHTML = '<div class="loading"><div class="spinner"></div>分析中...</div>';
            
            try {
                const res = await fetch('/api/activity/exercise', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        exercise_type: exerciseType,
                        duration_minutes: duration,
                        start_time: exerciseTime,
                        cgm_data: cgmText
                    })
                });
                const data = await res.json();
                
                if (data.error) {
                    document.getElementById('exerciseResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">${data.error}</p></div>`;
                    return;
                }
                
                const ex = data.exercise;
                const recs = data.recommendations;
                
                document.getElementById('exerciseResult').innerHTML = `
                    <div class="result-card">
                        <h3>🏃 运动血糖分析</h3>
                        <div class="result-grid">
                            <div class="result-item">
                                <div class="value">${ex.exercise_type}</div>
                                <div class="label">运动类型</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${ex.duration_minutes}分钟</div>
                                <div class="label">运动时长</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${ex.baseline?.toFixed(0) || 'N/A'}</div>
                                <div class="label">运动前血糖</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${ex.during_min?.toFixed(0) || 'N/A'}</div>
                                <div class="label">运动中最低</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${ex.change_from_baseline?.toFixed(0) || 'N/A'}</div>
                                <div class="label">血糖变化</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${ex.hypoglycemia_risk || 'N/A'}</div>
                                <div class="label">低血糖风险</div>
                            </div>
                        </div>
                        
                        <h4 style="margin:16px 0 8px">建议</h4>
                        <ul style="padding-left:20px;color:#374151">
                            ${recs.map(r => `<li style="margin-bottom:4px">${r}</li>`).join('')}
                        </ul>
                    </div>
                `;
                
                saveHistory('exercise', data);
                
            } catch (e) {
                document.getElementById('exerciseResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">错误: ${e.message}</p></div>`;
            }
        }
        
        // 睡眠分析
        async function analyzeSleep() {
            const sleepTime = document.getElementById('sleepTime').value;
            const wakeTime = document.getElementById('wakeTime').value;
            const cgmText = document.getElementById('sleepCgmText').value;
            
            if (!sleepTime || !wakeTime) {
                alert('请选择入睡和醒来时间');
                return;
            }
            if (!cgmText.trim()) {
                alert('请输入血糖数据');
                return;
            }
            
            document.getElementById('sleepResult').innerHTML = '<div class="loading"><div class="spinner"></div>分析中...</div>';
            
            try {
                const res = await fetch('/api/activity/sleep', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        sleep_time: sleepTime,
                        wake_time: wakeTime,
                        cgm_data: cgmText
                    })
                });
                const data = await res.json();
                
                if (data.error) {
                    document.getElementById('sleepResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">${data.error}</p></div>`;
                    return;
                }
                
                const m = data.metrics;
                const q = data.quality;
                const recs = data.recommendations;
                
                document.getElementById('sleepResult').innerHTML = `
                    <div class="result-card">
                        <h3>😴 睡眠血糖分析</h3>
                        <div class="result-grid">
                            <div class="result-item">
                                <div class="value">${m.sleep?.duration_hours || 'N/A'}小时</div>
                                <div class="label">睡眠时长</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${m.mean?.toFixed(0) || 'N/A'}</div>
                                <div class="label">平均血糖</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${m.min?.toFixed(0) || 'N/A'}</div>
                                <div class="label">最低血糖</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${m.max?.toFixed(0) || 'N/A'}</div>
                                <div class="label">最高血糖</div>
                            </div>
                            <div class="result-item highlight">
                                <div class="value">${q.score}</div>
                                <div class="label">睡眠质量</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${q.quality}</div>
                                <div class="label">评级</div>
                            </div>
                        </div>
                        
                        ${m.time_in_range ? `
                        <div style="margin-top:12px">
                            <div>Time in Range: <strong>${m.time_in_range.toFixed(1)}%</strong></div>
                        </div>
                        ` : ''}
                        
                        ${m.low_episodes ? `
                        <div style="margin-top:12px;color:#dc2626">
                            ⚠️ 夜间低血糖: ${m.low_episodes} 次
                        </div>
                        ` : ''}
                        
                        ${m.dawn_phenomenon ? `
                        <div style="margin-top:12px;color:#f59e0b">
                            ⚠️ 黎明现象: 血糖上升 ${m.dawn_phenomenon} mg/dL
                        </div>
                        ` : ''}
                        
                        <h4 style="margin:16px 0 8px">建议</h4>
                        <ul style="padding-left:20px;color:#374151">
                            ${recs.map(r => `<li style="margin-bottom:4px">${r}</li>`).join('')}
                        </ul>
                    </div>
                `;
                
                saveHistory('sleep', data);
                
            } catch (e) {
                document.getElementById('sleepResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">错误: ${e.message}</p></div>`;
            }
        }
        
        // 更新药物列表
        function updateMedicationList() {
            const type = document.getElementById('medicationType').value;
            const select = document.getElementById('medicationName');
            
            const oralMed = ['二甲双胍', '阿卡波糖', '伏格列波糖', '格列本脲', '格列齐特', '格列吡嗪', '格列美脲', '瑞格列奈', '那格列奈', '吡格列酮', '罗格列酮', '西格列汀', '沙格列汀', '维格列汀', '恩格列净', '卡格列净', '达格列净', '司美格鲁肽', '度拉糖肽', '利拉鲁肽'];
            const insulinMed = ['速效', '短效', '中效', '长效', '超长效', '预混'];
            
            const meds = type === '口服' ? oralMed : insulinMed;
            select.innerHTML = meds.map(m => `<option value="${m}">${m}</option>`).join('');
            
            // 更新剂量占位符
            document.getElementById('medicationDosage').placeholder = type === '口服' ? '剂量(mg)' : '剂量(U)';
        }
        
        // 药物分析
        async function analyzeMedication() {
            const medicationType = document.getElementById('medicationType').value;
            const medicationName = document.getElementById('medicationName').value;
            const dosage = parseFloat(document.getElementById('medicationDosage').value);
            const medicationTime = document.getElementById('medicationTime').value;
            const cgmText = document.getElementById('medicationCgmText').value;
            
            if (!medicationTime) {
                alert('请选择服药时间');
                return;
            }
            if (!cgmText.trim()) {
                alert('请输入血糖数据');
                return;
            }
            
            document.getElementById('medicationResult').innerHTML = '<div class="loading"><div class="spinner"></div>分析中...</div>';
            
            try {
                const res = await fetch('/api/medication/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        medication_type: medicationType,
                        medication_name: medicationName,
                        dosage: dosage,
                        taken_time: medicationTime,
                        cgm_data: cgmText
                    })
                });
                const data = await res.json();
                
                if (data.error) {
                    document.getElementById('medicationResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">${data.error}</p></div>`;
                    return;
                }
                
                const resp = data.response;
                const eff = data.efficacy;
                const recs = data.recommendations;
                
                const med = resp.medication || {};
                
                document.getElementById('medicationResult').innerHTML = `
                    <div class="result-card">
                        <h3>💊 药物血糖分析</h3>
                        <div class="result-grid">
                            <div class="result-item">
                                <div class="value">${med.medication_name || medicationName}</div>
                                <div class="label">药物</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${med.dosage || dosage || 'N/A'}</div>
                                <div class="label">剂量</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${med.baseline?.toFixed(0) || 'N/A'}</div>
                                <div class="label">服药前血糖</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${eff.efficacy}</div>
                                <div class="label">药效</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${eff.score}</div>
                                <div class="label">效果评分</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${med.hypo_risk || '低'}</div>
                                <div class="label">低血糖风险</div>
                            </div>
                        </div>
                        
                        ${resp.overall ? `
                        <h4 style="margin:16px 0 8px">血糖变化</h4>
                        <div class="result-grid">
                            <div class="result-item">
                                <div class="value">${resp.overall.min?.toFixed(0) || 'N/A'}</div>
                                <div class="label">最低</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${resp.overall.max?.toFixed(0) || 'N/A'}</div>
                                <div class="label">最高</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${resp.overall.change_from_baseline?.toFixed(0) || 'N/A'}</div>
                                <div class="label">变化</div>
                            </div>
                            <div class="result-item">
                                <div class="value">${resp.overall.max_drop?.toFixed(0) || 'N/A'}</div>
                                <div class="label">最大降幅</div>
                            </div>
                        </div>
                        ` : ''}
                        
                        <h4 style="margin:16px 0 8px">建议</h4>
                        <ul style="padding-left:20px;color:#374151">
                            ${recs.map(r => `<li style="margin-bottom:4px">${r}</li>`).join('')}
                        </ul>
                    </div>
                `;
                
                saveHistory('medication', data);
                
            } catch (e) {
                document.getElementById('medicationResult').innerHTML = `<div class="result-card" style="background:#fee2e2"><p style="color:#dc2626">错误: ${e.message}</p></div>`;
            }
        }
        
        // 初始化
        document.getElementById('mealTime').value = new Date().toISOString().slice(0, 16);
        
        // 设置默认睡眠时间 (昨晚11点到今早7点)
        const now = new Date();
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        document.getElementById('sleepTime').value = new Date(yesterday.setHours(23, 0, 0, 0)).toISOString().slice(0, 16);
        document.getElementById('wakeTime').value = new Date(now.setHours(7, 0, 0, 0)).toISOString().slice(0, 16);
        document.getElementById('exerciseTime').value = new Date(now.setHours(now.getHours() - 1, 0, 0, 0)).toISOString().slice(0, 16);
        document.getElementById('medicationTime').value = new Date().toISOString().slice(0, 16);
        
        loadHistory();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_HOME

# ============ API 端点 ============

@app.post("/api/cgm/analyze")
async def api_cgm_analyze(request: Request):
    """分析 CGM 数据"""
    body = await request.json()
    text = body.get('data', '')
    
    try:
        # 解析数据 - 过滤空行和注释
        lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith('#')]
        
        # 跳过可能的前几行元数据，找表头
        header_idx = 0
        for i, line in enumerate(lines):
            # 表头应该包含时间或血糖相关关键词（中英文）
            # 且不能是纯中文名字或其他非数据行
            lower_line = line.lower()
            is_header = any(k in lower_line for k in ['time', 'date', 'glucose', 'value', '血糖', '时间', 'sg', 'glucose'])
            # 跳过纯中文行（名字、标题等）
            is_chinese_only = all('\u4e00' <= c <= '\u9fff' for c in line.replace(',', '').replace('\t', '').replace(' ', ''))
            # 也跳过纯数字开头的行（可能是无表头的数据行）
            is_data_row = line[0].isdigit() if line else False
            if is_data_row:
                header_idx = i
                break
            if is_header and not is_chinese_only:
                header_idx = i
                break  # 找到表头就跳出
        
        # 取表头行之后的数据
        data_text = '\n'.join(lines[header_idx:])
        
        if not lines:
            return {"error": "数据为空"}
        
        # 检测分隔符
        first_line = lines[header_idx]
        import io
        if '\t' in first_line:
            # TAB 分隔 (TXT)
            df = pd.read_csv(io.StringIO(data_text), sep='\t', on_bad_lines='skip')
        elif ',' in first_line:
            # CSV 格式
            df = pd.read_csv(io.StringIO(data_text), on_bad_lines='skip')
        else:
            # 空格分隔 - 可能是无表头数据
            df = pd.read_csv(io.StringIO(data_text), sep=r'\s+', on_bad_lines='skip', header=None)
        
        # 标准化列名
        cols = df.columns.tolist()
        
        # 无表头时尝试识别：第1列是ID，第2+3列是时间，第4列是葡萄糖
        if len(cols) >= 4 and not any('time' in str(c).lower() or 'date' in str(c).lower() or 'glucose' in str(c).lower() for c in cols):
            # 根据实际列数命名
            col_names = ['id', 'date', 'time', 'record_type', 'glucose'][:len(cols)]
            df.columns = col_names
        
        time_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['timestamp', 'datetime', '日期时间'])), None)
        if not time_col:
            # 尝试找日期+时间组合
            if 'date' in df.columns and 'time' in df.columns:
                df['datetime'] = df['date'].astype(str) + ' ' + df['time'].astype(str)
                time_col = 'datetime'
            else:
                time_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['time', 'date', '时间', '日期'])), None)
        
        glucose_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['glucose', 'value', 'sg', '血糖', 'mg', 'mmol'])), None)
        
        if not time_col or not glucose_col:
            return {"error": f"未找到时间或血糖列。检测到的列: {list(df.columns)}"}
        
        df['timestamp'] = pd.to_datetime(df[time_col])
        df['glucose'] = pd.to_numeric(df[glucose_col], errors='coerce')
        
        # mmol/L 转 mg/dL (如果值小于 30，说明是 mmol/L)
        if df['glucose'].max() < 30:
            df['glucose'] = df['glucose'] * 18
        
        df = df.dropna(subset=['glucose']).sort_values('timestamp')
        
        results = analyze_glucose(df)
        
        # 返回简洁的 CGM 数据
        cgm_data = df[['timestamp', 'glucose']].to_dict('records')
        
        # 转换 numpy 类型为 Python 原生类型
        def convert(obj):
            import math
            if hasattr(obj, 'item'):  # numpy types
                obj = obj.item()
            if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                return None
            return obj
        
        results_clean = {k: convert(v) for k, v in results.items()}
        
        return {
            "success": True,
            "data_points": len(df),
            "time_range": f"{df['timestamp'].min().strftime('%m-%d %H:%M')} ~ {df['timestamp'].max().strftime('%m-%d %H:%M')}",
            "results": results_clean,
            "cgm_data": cgm_data
        }
        
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/foods/search")
def api_search_foods(q: str):
    """搜索食物"""
    results = search_foods(q)
    return {"results": results[:15]}


@app.get("/api/foods/category/{category}")
def api_foods_by_category(category: str):
    """按类别获取食物"""
    foods = list_foods_by_gi_category(category)
    return {"foods": foods[:30]}


@app.get("/api/food/info")
def api_food_info(name: str, weight: float = 100):
    """获取食物详细信息"""
    from glyconutri.gi_database import get_carbs
    
    carbs_per_100g = get_carbs(name)
    carbs = carbs_per_100g * weight / 100 if carbs_per_100g else None
    
    info = get_food_info(name, carbs)
    return info or {"error": "未找到"}


@app.post("/api/meal/analyze")
async def api_meal_analyze(request: Request):
    """餐后血糖分析"""
    body = await request.json()
    
    meal_time = body.get('meal_time')
    foods = body.get('foods', [])
    cgm_text = body.get('cgm_data')
    
    if not meal_time or not foods:
        return {"error": "请提供餐食时间和食物"}
    
    # 计算食物营养
    meal_session = create_meal_session(foods, datetime.fromisoformat(meal_time.replace('Z', '+00:00')))
    
    result = {
        "success": True,
        "meal": {
            "foods": [m.to_dict() for m in meal_session.meals],
            "total_carbs": meal_session.total_carbs,
            "total_gl": meal_session.total_gl,
            "weighted_gi": meal_session.weighted_gi
        }
    }
    
    # 如果有 CGM 数据，进行血糖响应分析
    if cgm_text:
        try:
            if isinstance(cgm_text, str):
                cgm_text = json.loads(cgm_text)
            
            if isinstance(cgm_text, list):
                df = pd.DataFrame(cgm_text)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            else:
                return {**result, "glucose_response": {}, "error": "CGM 数据格式有误"}
            
            analysis = PostMealAnalysis(meal_session.meals[0], df)
            
            result["glucose_response"] = {
                "baseline": analysis.calculate_baseline(),
                "peak": analysis.calculate_peak(),
                "response_magnitude": analysis.response_magnitude(),
                "iauc_2h": analysis.calculate_incremental_auc()
            }
            
        except Exception as e:
            result["glucose_response"] = {}
            result["cgm_error"] = str(e)
    else:
        result["glucose_response"] = {}
    
    return result


@app.post("/api/meal/nutrition")
async def api_meal_nutrition(request: Request):
    """餐食营养分析 (无需CGM)"""
    from glyconutri.meal import analyze_meal
    
    body = await request.json()
    
    foods = body.get('foods', [])
    meal_name = body.get('meal_name', '早餐')
    timestamp = body.get('timestamp')
    
    if not foods:
        return {"error": "请提供食物列表"}
    
    try:
        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.now()
        result = analyze_meal(foods, ts, meal_name)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/activity/exercise")
async def api_exercise_analyze(request: Request):
    """运动血糖分析"""
    from glyconutri.activity import ExerciseEvent, ExerciseAnalysis
    
    body = await request.json()
    
    exercise_type = body.get('exercise_type')
    duration_minutes = body.get('duration_minutes', 30)
    start_time = body.get('start_time')
    cgm_text = body.get('cgm_data')
    
    if not exercise_type or not start_time:
        return {"error": "请提供运动类型和时间"}
    
    if not cgm_text:
        return {"error": "请提供血糖数据"}
    
    try:
        lines = [l.strip() for l in cgm_text.split('\n') if l.strip() and not l.startswith('#')]
        import io
        if '\t' in lines[0]:
            df = pd.read_csv(io.StringIO('\n'.join(lines)), sep='\t', on_bad_lines='skip')
        elif ',' in lines[0]:
            df = pd.read_csv(io.StringIO('\n'.join(lines)), on_bad_lines='skip')
        else:
            df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=r'\s+', on_bad_lines='skip', header=None)
        
        time_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['time', 'date', '时间'])), df.columns[0])
        glucose_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['glucose', 'value', 'sg', '血糖'])), df.columns[-1])
        
        df['timestamp'] = pd.to_datetime(df[time_col])
        df['glucose'] = pd.to_numeric(df[glucose_col], errors='coerce')
        if df['glucose'].max() < 30:
            df['glucose'] = df['glucose'] * 18
        df = df.dropna(subset=['glucose']).sort_values('timestamp')
        
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        exercise = ExerciseEvent(exercise_type, duration_minutes, start_dt)
        analysis = ExerciseAnalysis(exercise, df)
        return analysis.get_full_analysis()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/activity/sleep")
async def api_sleep_analyze(request: Request):
    """睡眠血糖分析"""
    from glyconutri.activity import SleepEvent, SleepAnalysis
    
    body = await request.json()
    
    sleep_time = body.get('sleep_time')
    wake_time = body.get('wake_time')
    cgm_text = body.get('cgm_data')
    
    if not sleep_time or not wake_time:
        return {"error": "请提供入睡和醒来时间"}
    if not cgm_text:
        return {"error": "请提供血糖数据"}
    
    try:
        lines = [l.strip() for l in cgm_text.split('\n') if l.strip() and not l.startswith('#')]
        import io
        if '\t' in lines[0]:
            df = pd.read_csv(io.StringIO('\n'.join(lines)), sep='\t', on_bad_lines='skip')
        elif ',' in lines[0]:
            df = pd.read_csv(io.StringIO('\n'.join(lines)), on_bad_lines='skip')
        else:
            df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=r'\s+', on_bad_lines='skip', header=None)
        
        time_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['time', 'date', '时间'])), df.columns[0])
        glucose_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['glucose', 'value', 'sg', '血糖'])), df.columns[-1])
        
        df['timestamp'] = pd.to_datetime(df[time_col])
        df['glucose'] = pd.to_numeric(df[glucose_col], errors='coerce')
        if df['glucose'].max() < 30:
            df['glucose'] = df['glucose'] * 18
        df = df.dropna(subset=['glucose']).sort_values('timestamp')
        
        sleep_dt = datetime.fromisoformat(sleep_time.replace('Z', '+00:00'))
        wake_dt = datetime.fromisoformat(wake_time.replace('Z', '+00:00'))
        sleep = SleepEvent(sleep_dt, wake_dt)
        analysis = SleepAnalysis(sleep, df)
        return analysis.get_full_analysis()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/medication/analyze")
async def api_medication_analyze(request: Request):
    """药物血糖分析"""
    from glyconutri.medication import MedicationEvent, MedicationAnalysis, InsulinAnalysis
    
    body = await request.json()
    
    medication_type = body.get('medication_type', '口服')
    medication_name = body.get('medication_name')
    dosage = body.get('dosage')
    taken_time = body.get('taken_time')
    cgm_text = body.get('cgm_data')
    
    if not medication_name or not taken_time:
        return {"error": "请提供药物名称和时间"}
    if not cgm_text:
        return {"error": "请提供血糖数据"}
    
    try:
        lines = [l.strip() for l in cgm_text.split('\n') if l.strip() and not l.startswith('#')]
        import io
        if '\t' in lines[0]:
            df = pd.read_csv(io.StringIO('\n'.join(lines)), sep='\t', on_bad_lines='skip')
        elif ',' in lines[0]:
            df = pd.read_csv(io.StringIO('\n'.join(lines)), on_bad_lines='skip')
        else:
            df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=r'\s+', on_bad_lines='skip', header=None)
        
        time_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['time', 'date', '时间'])), df.columns[0])
        glucose_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['glucose', 'value', 'sg', '血糖'])), df.columns[-1])
        
        df['timestamp'] = pd.to_datetime(df[time_col])
        df['glucose'] = pd.to_numeric(df[glucose_col], errors='coerce')
        if df['glucose'].max() < 30:
            df['glucose'] = df['glucose'] * 18
        df = df.dropna(subset=['glucose']).sort_values('timestamp')
        
        taken_dt = datetime.fromisoformat(taken_time.replace('Z', '+00:00'))
        
        if medication_type == "胰岛素":
            analysis = InsulinAnalysis(medication_name, dosage or 1, taken_dt, df)
            return analysis.get_full_analysis()
        else:
            med = MedicationEvent(medication_name, dosage, taken_time=taken_dt, medication_type=medication_type)
            analysis = MedicationAnalysis(med, df)
            return analysis.get_full_analysis()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
