import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path, output_txt_path=None):
    """
    從PDF檔案中提取文字並選擇性地保存到文字檔
    
    Args:
        pdf_path (str): PDF文件的路徑
        output_txt_path (str, optional): 輸出文字檔的路徑，若不提供則不保存檔案
        
    Returns:
        str: 從PDF提取的全部文字內容
    """
    # 檢查檔案是否存在
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"找不到PDF檔案: {pdf_path}")
    
    # 創建PDF閱讀器物件
    reader = PdfReader(pdf_path)
    
    # 獲取PDF資訊
    info = reader.metadata
    num_pages = len(reader.pages)
    print(f"PDF資訊: {info}")
    print(f"頁數: {num_pages}")
    
    # 提取所有頁面的文字
    all_text = ""
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        all_text += f"\n--- 第 {i+1} 頁 ---\n"
        all_text += text + "\n"
    
    # 如果提供了輸出路徑，則將文字保存到文件
    if output_txt_path:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(all_text)
        print(f"文字已保存到: {output_txt_path}")
    
    return all_text

# 使用範例
if __name__ == "__main__":
    pdf_file = "example.pdf"
    output_file = "extracted_text.txt"
    
    text = extract_text_from_pdf(pdf_file, output_file)
    print(f"提取的文字長度: {len(text)} 字元")