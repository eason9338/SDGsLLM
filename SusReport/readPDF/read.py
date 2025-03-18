import fitz  # PyMuPDF
import re
import os
from collections import defaultdict

def extract_pdf_with_data(pdf_path, output_folder=None):

    if output_folder and not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 打開PDF文件
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    
    results = {
        "metadata": {
            "filename": os.path.basename(pdf_path),
            "pages": num_pages,
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
        },
        "pages": []
    }
    
    # 處理每一頁
    for page_num in range(num_pages):
        try:
            page = doc[page_num]
            page_result = extract_page_data(page, page_num)
            results["pages"].append(page_result)
            
            # 輸出到文件
            if output_folder:
                # 保存純文字
                with open(os.path.join(output_folder, f"page_{page_num+1}_text.txt"), "w", encoding="utf-8") as f:
                    f.write(page_result["text"])
                
                # 保存提取的數據
                if page_result["data_blocks"]:
                    with open(os.path.join(output_folder, f"page_{page_num+1}_data.txt"), "w", encoding="utf-8") as f:
                        for item in page_result["data_blocks"]:
                            f.write(f"數值: {item.get('value', '')}\n")
                            f.write(f"單位: {item.get('unit', '')}\n")
                            f.write(f"描述: {item.get('description', '')}\n")
                            f.write("-" * 30 + "\n")
        except Exception as e:
            print(f"處理第 {page_num+1} 頁時發生錯誤: {e}")
            results["pages"].append({
                "page_number": page_num + 1,
                "text": "提取失敗",
                "error": str(e),
                "data_blocks": []
            })
    
    # 保存完整的文字檔
    if output_folder:
        with open(os.path.join(output_folder, "full_text.txt"), "w", encoding="utf-8") as f:
            for page in results["pages"]:
                f.write(f"\n===== 第 {page['page_number']} 頁 =====\n")
                f.write(page["text"])
                f.write("\n")
    
    return results

def extract_page_data(page, page_num):
    text = page.get_text("text")
    
    # 獲取頁面佈局類型
    page_type = analyze_simple_layout(page)
    
    # 提取數據塊
    data_blocks = []
    
    # 獲取區塊結構
    blocks = page.get_text("dict")["blocks"]
    
    # 處理區塊
    for block in blocks:
        if block["type"] != 0:  # 跳過非文字塊
            continue
        
        # 處理每個文字塊
        block_text = ""
        for line in block["lines"]:
            for span in line["spans"]:
                block_text += span["text"] + " "
        
        block_text = block_text.strip()
        if not block_text:
            continue
        
        # 檢查是否包含數字+單位
        data = extract_data_from_text(block_text, block["bbox"])
        if data:
            data_blocks.append(data)
    
    # 關聯數據與描述
    related_data = associate_data_with_descriptions(data_blocks, blocks)
    
    return {
        "page_number": page_num + 1,
        "text": text,
        "page_type": page_type,
        "data_blocks": related_data
    }

def analyze_simple_layout(page):

    width, height = page.rect.width, page.rect.height
    
    blocks = page.get_text("dict")["blocks"]
    text_areas = []
    
    for block in blocks:
        if block["type"] == 0:  # 文字塊
            for line in block["lines"]:
                for span in line["spans"]:
                    text_areas.append({
                        "rect": [span["bbox"][0], span["bbox"][1], span["bbox"][2], span["bbox"][3]],
                        "text": span["text"]
                    })
    
    # 檢查是否有密集的小區塊 (如儀表板)
    if len(text_areas) > 20 and any(len(area["text"]) < 5 for area in text_areas):
        return "dashboard"
    
    # 分析是否是多欄佈局
    x_positions = [area["rect"][0] for area in text_areas]
    if len(x_positions) > 10:
        x_positions.sort()
        gaps = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
        large_gaps = [gap for gap in gaps if gap > width * 0.1]
        if len(large_gaps) > len(gaps) * 0.1:
            return "multi_column"
    
    return "normal_text"

def extract_data_from_text(text, bbox):

    patterns = [
        # 數字後跟單位的模式
        r'([\d,.]+)\s*(%|萬|億度|兆|元|美元|度|噸|個|項|人次|億)',
        # 百分比模式
        r'([\d,.]+)\s*%',
        # 金額模式
        r'([\d,.]+)\s*(元|美元|台幣)',
        # 數量模式
        r'([\d,.]+)\s*(個|台|件|套|張)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return {
                "value": match.group(1),
                "unit": match.group(2),
                "text": text,
                "bbox": bbox
            }
    
    return None

def associate_data_with_descriptions(data_blocks, blocks):

    if not data_blocks:
        return []
    
    text_blocks = []
    for block in blocks:
        if block["type"] != 0:  # 跳過非文字塊
            continue
        
        block_text = ""
        for line in block["lines"]:
            for span in line["spans"]:
                block_text += span["text"] + " "
        
        block_text = block_text.strip()
        if block_text:
            text_blocks.append({
                "text": block_text,
                "bbox": block["bbox"]
            })
    
    # 為每個數據區塊尋找最相關的描述
    for data in data_blocks:
        data_bbox = data["bbox"]
        
        # 檢查是否已包含描述
        data_text = data["text"]
        value_unit = data["value"] + data["unit"]
        
        # 從數據文本中移除數值和單位，看是否有剩餘文字作為描述
        description = data_text.replace(value_unit, "").strip()
        
        # 如果沒有足夠的描述，尋找附近的區塊
        if len(description) < 5:
            # 找尋下方最近的區塊作為描述
            closest_block = find_closest_block(text_blocks, data_bbox)
            if closest_block:
                description = closest_block["text"]
        
        data["description"] = description
    
    return data_blocks

def find_closest_block(blocks, data_bbox, max_vertical_gap=50):
    """
    找出與數據區塊最接近的下方區塊
    
    Args:
        blocks: 文字區塊列表
        data_bbox: 數據區塊的邊界框
        max_vertical_gap: 最大垂直間距
    
    Returns:
        dict: 最近的區塊
    """
    x0, y0, x1, y1 = data_bbox
    candidates = []
    
    for block in blocks:
        bx0, by0, bx1, by1 = block["bbox"]
        
        # 檢查區塊是否在下方且水平位置重疊
        if by0 > y1 and by0 - y1 <= max_vertical_gap:
            # 檢查水平重疊
            if (bx0 < x1 and bx1 > x0):
                # 計算垂直距離
                distance = by0 - y1
                candidates.append((distance, block))
    
    # 按距離排序
    candidates.sort(key=lambda x: x[0])
    
    # 返回最近的區塊
    if candidates:
        return candidates[0][1]
    return None


# 使用範例
if __name__ == "__main__":
    pdf_file = "example2.pdf"
    output_folder = "extracted_pdf_content2"
    
    # 選項1: 提取數據和文本
    results = extract_pdf_with_data(pdf_file, output_folder)
    print(f"已完成 {len(results['pages'])} 頁的處理")
    
    # 統計找到的數據量
    data_count = sum(len(page.get('data_blocks', [])) for page in results['pages'])
    print(f"共找到 {data_count} 個數據項")

