import text2vec
import faiss
import numpy as np
import re

# ✅ 1. 讀取 FAISS 索引 & 企業報告文本
print("🚀 載入 FAISS 向量索引...")
faiss_index = faiss.read_index("./faiss_index.bin")
documents = np.load("./documents.npy", allow_pickle=True)

# ✅ 2. 載入 text2vec 模型
encoder = text2vec.SentenceModel("shibing624/text2vec-base-chinese")

# ✅ 3. 問答函數
def search_best_answer(question, top_k=3):
    query_vector = encoder.encode([question])  # 轉換問題為向量
    distances, indices = faiss_index.search(query_vector, top_k)  # 搜索最相似的內容
    best_matches = [documents[idx] for idx in indices[0]]  # 取得最佳匹配的句子

    # 取出最佳答案，限制輸出字數
    best_answer = best_matches[0]  # 只取第一個最相關的段落
    best_answer = re.sub(r"\n+", "\n", best_answer).strip()  # 移除多餘換行
    best_answer = best_answer[:300]  # 限制輸出前 300 個字

    return best_answer

# ✅ 4. 進行問答
while True:
    question = input("\n📝 請輸入你的問題（輸入 'exit' 結束）：")
    if question.lower() == "exit":
        break
    best_answer = search_best_answer(question)
    print(f"\n🤖 AI 回答：\n{best_answer}")

