import requests
import random
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# ===== HÀM CHUẨN HÓA LỊCH SỬ =====
def chuan_hoa_history(raw_data):
    history = []
    for item in raw_data:
        history.append({
            "session": item["sid"],
            "dice": [item["d1"], item["d2"], item["d3"]],
            "total": item["sum"],
            "result": item["result"].capitalize()
        })
    return history

# ===== CÁC CẦU =====
def check_1_1(history):
    if history[0]["result"] == history[1]["result"]:
        return history[0]["result"], "Cầu 1-1"
    return None, None

def check_2_2(history):
    if len(history) >= 4 and history[0]["result"] == history[1]["result"] and history[2]["result"] == history[3]["result"]:
        return history[0]["result"], "Cầu 2-2"
    return None, None

def check_3_3(history):
    if len(history) >= 6 and len(set(h["result"] for h in history[:3])) == 1 and len(set(h["result"] for h in history[3:6])) == 1:
        return history[0]["result"], "Cầu 3-3"
    return None, None

def check_2_1_2(history):
    if len(history) >= 5 and history[0]["result"] == history[1]["result"] and history[2]["result"] != history[0]["result"] and history[3]["result"] == history[4]["result"] == history[0]["result"]:
        return history[0]["result"], "Cầu 2-1-2"
    return None, None

def check_3_1_3(history):
    if len(history) >= 7 and len(set(h["result"] for h in history[0:3])) == 1 and history[3]["result"] != history[0]["result"] and len(set(h["result"] for h in history[4:7])) == 1:
        return history[0]["result"], "Cầu 3-1-3"
    return None, None

def check_bet(history):
    if len(set(h["result"] for h in history[:5])) == 1:
        return history[0]["result"], "Cầu bệt"
    return None, None

def check_hoi(history):
    if history[1]["result"] == history[2]["result"] and history[0]["result"] != history[1]["result"]:
        return history[0]["result"], "Cầu hồi"
    return None, None

def check_1_2_3(history):
    seq = ["Tài", "Xỉu", "Tài"] if history[2]["result"] == "Tài" else ["Xỉu", "Tài", "Xỉu"]
    if [h["result"] for h in history[0:3]] == seq:
        return "Xỉu" if history[2]["result"] == "Tài" else "Tài", "Cầu 1-2-3"
    return None, None

def check_3_2_1(history):
    seq = ["Tài", "Tài", "Xỉu"] if history[2]["result"] == "Tài" else ["Xỉu", "Xỉu", "Tài"]
    if [h["result"] for h in history[0:3]] == seq:
        return "Xỉu" if history[2]["result"] == "Tài" else "Tài", "Cầu 3-2-1"
    return None, None

def check_kep(history):
    dice = history[0]["dice"]
    if dice[0] == dice[1] or dice[1] == dice[2] or dice[0] == dice[2]:
        return history[0]["result"], "Cầu kép"
    return None, None

# ===== LOGIC BẺ CẦU CHUẨN =====
def be_cau_chuan(history, du_doan):
    last_results = [h["result"] for h in history]

    if len(set(last_results[:4])) == 1:
        return "Tài" if last_results[0] == "Xỉu" else "Xỉu", "Bẻ cầu do bệt >=4"

    streak = 1
    for i in range(1, len(last_results)):
        if last_results[i] == last_results[0]:
            streak += 1
        else:
            break
    if streak >= 3 and last_results[0] != last_results[1]:
        return "Tài" if last_results[0] == "Xỉu" else "Xỉu", "Bẻ cầu sau khi vừa đứt"

    if all(r == du_doan for r in last_results[:3]):
        return "Tài" if du_doan == "Xỉu" else "Xỉu", "Bẻ cầu do trùng dự đoán 3 phiên"

    return du_doan, None

# ===== DỰ ĐOÁN THEO CẦU =====
def du_doan_theo_cau(history):
    patterns = [
        check_1_1, check_2_2, check_3_3, check_2_1_2, check_3_1_3,
        check_bet, check_hoi, check_1_2_3, check_3_2_1, check_kep
    ]
    for func in patterns:
        du_doan, ly_do = func(history)
        if du_doan:
            du_doan, be_ly_do = be_cau_chuan(history, du_doan)
            if be_ly_do:
                ly_do += f" + {be_ly_do}"
            return du_doan, ly_do
    du_doan = random.choice(["Tài", "Xỉu"])
    du_doan, be_ly_do = be_cau_chuan(history, du_doan)
    return du_doan, be_ly_do if be_ly_do else "Không rõ cầu, dự đoán ngẫu nhiên"

# ===== API =====
@app.get("/predict")
def predict():
    try:
        response = requests.get("https://bomaylamy-apsw.onrender.com/api/sunwin")
        response.raise_for_status()
        raw_json = response.json()

        if "data" not in raw_json or not raw_json["data"]:
            return JSONResponse(content={"detail": "Không có dữ liệu từ API lịch sử"})

        history = chuan_hoa_history(raw_json["data"][:100])

        if len(history) < 3:
            return JSONResponse(content={"detail": "Không đủ dữ liệu để phân tích"})

        current = history[0]
        next_session = current["session"] + 1

        du_doan, ly_do = du_doan_theo_cau(history[:10])

        return {
            "phien": current["session"],
            "xuc_xac": current["dice"],
            "ket_qua": current["result"],
            "du_doan": du_doan,
            "ly_do": ly_do
        }

    except Exception as e:
        return JSONResponse(content={"detail": f"Lỗi xử lý: {str(e)}"})
