"""
PDF 报告生成模块
"""

from datetime import datetime
from typing import Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io


class PDFReportGenerator:
    """PDF 报告生成器"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """设置样式"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f2937'),
            spaceBefore=20,
            spaceAfter=10
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8
        )
    
    def generate_report(self, data: Dict, report_type: str = 'weekly') -> bytes:
        """
        生成 PDF 报告
        
        Args:
            data: 报告数据
            report_type: weekly 或 monthly
        
        Returns:
            PDF 字节数据
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        
        # 标题
        title = 'GlycoNutri 血糖分析报告'
        if report_type == 'weekly':
            title += ' - 周报'
        else:
            title += ' - 月报'
        
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # 生成日期
        date_str = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        story.append(Paragraph(f'生成日期: {date_str}', self.normal_style))
        story.append(Spacer(1, 20))
        
        # 概览
        if 'overview' in data:
            story.append(Paragraph('📊 数据概览', self.heading_style))
            
            overview = data['overview']
            
            # 基本信息表格
            info_data = [
                ['指标', '数值'],
                ['总记录数', str(overview.get('total_readings', 'N/A'))],
                ['平均血糖', f"{overview.get('mean_glucose', 'N/A')} mg/dL"],
                ['TIR', f"{overview.get('tir', 'N/A')}%"],
                ['TBR', f"{overview.get('tbr', 'N/A')}%"],
                ['TAR', f"{overview.get('tar', 'N/A')}%"],
            ]
            
            if 'gv' in overview:
                info_data.append(['血糖波动', f"{overview.get('gv', 'N/A')}%"])
            
            table = Table(info_data, colWidths=[2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
        
        # 每日/每周趋势
        if 'daily_summary' in data:
            story.append(Paragraph('📅 每日趋势', self.heading_style))
            
            daily_data = [['日期', '平均', '最低', '最高']]
            for day in data['daily_summary'][:7]:
                daily_data.append([
                    day.get('date', ''),
                    str(day.get('mean', '')),
                    str(day.get('min', '')),
                    str(day.get('max', ''))
                ])
            
            table = Table(daily_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
        
        # 建议
        if 'recommendations' in data and data['recommendations']:
            story.append(Paragraph('💡 建议', self.heading_style))
            
            for rec in data['recommendations']:
                story.append(Paragraph(f'• {rec}', self.normal_style))
            story.append(Spacer(1, 20))
        
        # 目标达成
        if 'goals' in data and data['goals']:
            story.append(Paragraph('🎯 目标达成', self.heading_style))
            
            for goal in data['goals']:
                # 添加 emoji 颜色
                color = colors.green if '✅' in goal else colors.orange if '⚠️' in goal else colors.black
                story.append(Paragraph(f'<font color="{color.hexval()}">{goal}</font>', self.normal_style))
        
        # 页脚
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            '<font color="#9ca3af" fontSize=8>Generated by GlycoNutri - 血糖营养计算工具</font>',
            self.normal_style
        ))
        
        # 构建 PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer.read()


def generate_pdf(data: Dict, report_type: str = 'weekly') -> bytes:
    """生成 PDF 报告"""
    generator = PDFReportGenerator()
    return generator.generate_report(data, report_type)
