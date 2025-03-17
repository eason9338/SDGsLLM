import pdfplumber

def extract_text_from_pdf(pdf_path, output_txt_path):
    try:
        # 讀取 PDF
        with pdfplumber.open(pdf_path) as pdf:
            # 開啟 txt 檔案準備寫入
            with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
                # 遍歷所有頁面
                for page_num, page in enumerate(pdf.pages, 1):
                    # 提取文字
                    text = page.extract_text()
                    if text:
                        # 寫入頁碼和內容
                        txt_file.write(f'=== 第 {page_num} 頁 ===\n')
                        txt_file.write(text)
                        txt_file.write('\n\n')
        
        print(f"已成功將內容輸出至: {output_txt_path}")
        return True
        
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        return False

# 使用範例
if __name__ == "__main__":
    pdf_path = "example.pdf"  # 請替換成您的 PDF 檔案路徑
    output_txt_path = "輸出結果.txt"  # 輸出的 txt 檔案名稱
    extract_text_from_pdf(pdf_path, output_txt_path)