# -*- coding: utf-8 -*-
"""将 Markdown 论文转换为 Word 文档，保留所有引用标记和格式"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import re

def add_paragraph_with_format(doc, text, style='Normal', bold_ranges=None, font_size=None):
    """添加段落，支持部分文字加粗"""
    p = doc.add_paragraph()
    if style != 'Normal':
        p.style = doc.styles[style]
    
    if not text.strip():
        return p
    
    # 处理加粗标记 **text**
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = p.add_run(part[2:-2])
            run.bold = True
            if font_size:
                run.font.size = Pt(font_size)
        else:
            run = p.add_run(part)
            if font_size:
                run.font.size = Pt(font_size)
    return p


def md_to_docx(md_path, docx_path):
    doc = Document()
    
    # 设置默认字体
    style = doc.styles['Normal']
    font = style.font
    font.name = '宋体'
    font.size = Pt(12)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # 一级标题 #
        if line.startswith('# ') and not line.startswith('## '):
            h = doc.add_heading(line[2:], level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in h.runs:
                run.font.size = Pt(18)
                
        # 二级标题 ##
        elif line.startswith('## '):
            h = doc.add_heading(line[3:], level=2)
            for run in h.runs:
                run.font.size = Pt(15)
                
        # 三级标题 ###
        elif line.startswith('### '):
            h = doc.add_heading(line[4:], level=3)
            for run in h.runs:
                run.font.size = Pt(13)
            
        # 分隔线
        elif line.strip() == '---':
            doc.add_paragraph('─' * 60)
            
        # 参考文献标题后，逐行添加每条参考文献
        elif line.strip() == '## 参考文献':
            h = doc.add_heading('参考文献', level=2)
            for run in h.runs:
                run.font.size = Pt(15)
            # 读取后续所有参考文献行
            i += 1
            while i < len(lines):
                ref_line = lines[i].strip()
                if ref_line and ref_line.startswith('['):
                    p = doc.add_paragraph(ref_line)
                    p.style = doc.styles['Normal']
                    p.paragraph_format.first_line_indent = Cm(-0.7)
                    p.paragraph_format.left_indent = Cm(0.7)
                    for run in p.runs:
                        run.font.size = Pt(10)
                        run.font.name = 'Times New Roman'
                elif ref_line == '':
                    pass  # skip empty lines within references
                else:
                    break  # exit reference section
                i += 1
            continue
            
        # 关键词行
        elif line.startswith('**关键词：**'):
            p = doc.add_paragraph()
            run = p.add_run('关键词：')
            run.bold = True
            run.font.size = Pt(11)
            rest = line.replace('**关键词：**', '')
            run2 = p.add_run(rest)
            run2.font.size = Pt(11)
            
        # 空行
        elif line.strip() == '':
            i += 1
            continue
            
        # 普通文本段落（包括带 ** 加粗的）
        else:
            add_paragraph_with_format(doc, line, font_size=12)
        
        i += 1
    
    # 保存
    doc.save(docx_path)
    print(f'✅ Word 文档已生成: {docx_path}')


if __name__ == '__main__':
    md_to_docx(
        r'd:\Desktop\smartzhengguan\论文_AIoT协同计算架构_优化版.md',
        r'd:\Desktop\smartzhengguan\论文_AIoT协同计算架构.docx'
    )
