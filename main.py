import requests
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from collections import Counter

app = FastAPI()

# ===== Hàm hỗ trợ =====
def xu_huong_diem(history):
    total1 = history[1]["total"]
    total2 = history[0]["total"]
    if total2 > total1:
        return "lên"
    elif total2 < total1:
        return "xuống"
    else:
        return "đều"

def dem_trung(xucxac):
    return max(xucxac.count(i) for i in xucxac)

def dem_tan_suat(xx1, xx2, xx3):
    return Counter(xx1 + xx2 + xx3)

def chuan_hoa_history(raw_data):
    history = []
    for item in raw_data:
        history.append({
            "session": item["sid"],
            "dice": [item["d1"], item["d2"], item["d3"]],
            "total": item["sum"],
            "result": item["result"].capitalize()  # "TÀI"/"XỈU" -> "Tài"/"Xỉu"
        })
    return history

# ===== Logic dự đoán nâng cao =====
def du_doan_theo_ct(history):
    xx1 = history[2]["dice"]
    xx2 = history[1]["dice"]
    xx3 = history[0]["dice"]
    total2 = history[1]["total"]
    total3 = history[0]["total"]
    result3 = history[0]["result"]
    trend = xu_huong_diem(history)

    def tong(xx): return sum(xx)
    freq = dem_tan_suat(xx1, xx2, xx3)
    top_xx1 = max(xx1, key=lambda x: freq[x])
    top_xx2 = max(xx2, key=lambda x: freq[x])
    top_xx3 = max(xx3, key=lambda x: freq[x])

    # Công thức 1
    if dem_trung(xx1) == 3:
        return "Tài" if trend == "lên" else "Xỉu"
    elif dem_trung(xx1) == 2:
        return "Tài" if tong(xx3) < tong(xx1) else "Xỉu"
    elif dem_trung(xx2) == 3:
        return "Tài" if tong(xx1) > tong(xx2) else "Xỉu"

    # Công thức 2
    if (abs(xx3[0] - xx3[1]) == 1 and abs(xx3[2] - xx3[1]) == 1) or \
       (abs(xx3[1] - xx3[2]) == 1 and abs(xx3[0] - xx3[1]) == 1):
        return "Tài" if result3 == "Xỉu" else "Xỉu"

    # Công thức 3
    sorted_xx = sorted(xx3)
    if sorted_xx[1] == sorted_xx[0] + 1 and sorted_xx[2] == sorted_xx[1] + 1:
        return result3

    # Công thức 4
    if sorted_xx[1] - sorted_xx[0] == 2 and sorted_xx[2] - sorted_xx[1] == 2:
        return result3

    # Công thức 5
    if dem_trung(xx3) == 3:
        if xx3[0] in [3, 4, 6]:
            return result3
        else:
            return "Tài" if result3 == "Xỉu" else "Xỉu"

    # Công thức 6
    if dem_trung(xx3) == 2:
        return "Tài" if result3 == "Xỉu" else "Xỉu"

    return result3

# ===== Logic 98% chẵn =====
def kiem_tra_chan_98(history):
    last7 = history[:7]
    count_even = sum(1 for h in last7 if h["total"] % 2 == 0)
    if count_even >= 6:
        return True
    return False

# ===== Endpoint =====
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
            return JSONResponse(content={"detail": "Không đủ dữ liệu để phân tích theo công thức"})

        current = history[0]
        next_session = current["session"] + 1

        # Dự đoán theo công thức nâng cao
        du_doan = du_doan_theo_ct(history[:3])

        # Áp dụng 98% chẵn
        if kiem_tra_chan_98(history):
            du_doan = "Xỉu"

        return {
            "current_session": current["session"],
            "current_result": current["result"],
            "current_dice": current["dice"],
            "current_total": current["total"],
            "next_session": next_session,
            "du_doan": du_doan,
            "ly_do": "Dự đoán theo biểu đồ cầu, công thức nâng cao và 98% chẵn"
        }

    except Exception as e:
        return JSONResponse(content={"detail": f"Lỗi xử lý dự đoán: {str(e)}"})
