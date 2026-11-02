import requests
import os
from bs4 import BeautifulSoup
import chardet

def detect_encoding(content):
    """检测文件编码"""
    result = chardet.detect(content)
    return result['encoding'] or 'utf-8'

def extract_text_from_html(html_content):
    """从HTML中提取正文内容"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除脚本和样式
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()
    
    # 尝试找到正文区域
    content_div = soup.find('div', class_='content') or \
                  soup.find('div', id='content') or \
                  soup.find('article') or \
                  soup.find('main')
    
    if content_div:
        text = content_div.get_text(strip=False)
    else:
        text = soup.get_text(strip=False)
    
    # 清理多余空白
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            cleaned_lines.append(stripped)
    
    return '\n\n'.join(cleaned_lines)

def download_and_parse(url, file_name, save_dir):
    """下载页面并提取正文"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 检测编码并解码
        encoding = detect_encoding(response.content)
        html_content = response.content.decode(encoding, errors='replace')
        
        # 提取正文
        text = extract_text_from_html(html_content)
        
        # 保存为txt文件
        save_path = os.path.join(save_dir, f"{file_name}.txt")
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"✅ 下载成功: {file_name}.txt")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {file_name} - {str(e)}")
        return False

def main():
    save_dir = '研究生文件规定_解析版'
    os.makedirs(save_dir, exist_ok=True)
    
    files = [
        ("山东大学研究生奖学金评审办法", "https://www.grad.sdu.edu.cn/info/1029/19997.htm"),
        ("山东大学研究生助学金管理办法", "https://www.ygb.sdu.edu.cn/info/1026/10964.htm"),
        ("山东大学研究生学籍管理规定", "https://www.grad.sdu.edu.cn/info/1029/16901.htm"),
        ("山东大学研究生奖助体系改革方案", "https://www.ygb.sdu.edu.cn/info/1026/6217.htm"),
        ("研究生助研助教助管工作管理办法", "https://www.ygb.sdu.edu.cn/info/1026/6218.htm"),
        ("山东大学研究生学术之星奖评选办法", "https://www.grad.sdu.edu.cn/info/1029/15812.htm"),
        ("山东大学研究生课程教学管理办法", "https://www.grad.sdu.edu.cn/info/1029/3126.htm"),
        ("山东大学研究生出国管理暂行规定", "https://www.grad.sdu.edu.cn/info/1029/3124.htm"),
    ]
    
    print("📥 开始下载并解析文件...")
    print("=" * 60)
    
    success_count = 0
    for name, url in files:
        if download_and_parse(url, name, save_dir):
            success_count += 1
    
    print("=" * 60)
    print(f"\n📊 下载完成！成功: {success_count}/{len(files)}")
    print(f"📁 文件保存位置: {os.path.abspath(save_dir)}")
    print("\n💡 提示：文件已提取为纯文本格式，可以直接用记事本打开阅读")

if __name__ == '__main__':
    main()