import text2vec
import faiss
import numpy as np

# ✅ 1. 讀取全文檔案
file_path = "./extracted_pdf_content2/full_text.txt"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# ✅ 2. 切割文本（每個段落作為一個檢索單位）
paragraphs = content.split("\n\n")  # 以雙換行符號分割段落

# ✅ 3. 載入 text2vec 模型
print("🚀 載入 `text2vec` 中文向量模型...")
encoder = text2vec.SentenceModel("shibing624/text2vec-base-chinese")


# ✅ 4. 向量化文本段落
print("🔍 轉換文本為向量...")
paragraph_vectors = encoder.encode(paragraphs)

# ✅ 5. 建立 FAISS 向量索引
dimension = paragraph_vectors.shape[1]  # 向量維度
faiss_index = faiss.IndexFlatL2(dimension)  # L2 距離索引
faiss_index.add(paragraph_vectors)  # 加入索引

# ✅ 6. 儲存 FAISS 索引 & 文本
faiss.write_index(faiss_index, "./faiss_index.bin")

np.save("./documents.npy", np.array(paragraphs, dtype=object))

print("✅ 向量索引已建立並存檔！")

