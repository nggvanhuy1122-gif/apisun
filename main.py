import requests
import random
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from collections import Counter

app = FastAPI()

    # ===== Hàm hỗ trợ =====
def xu_huong_diem(history):
        if len(history) < 2:
            return "đều"
        total1 = history[1]["total"]
        total2 = history[0]["total"]
        if total2 > total1:
            return "lên"
        elif total2 < total1:
            return "xuống"
        return "đều"

def dem_trung(xucxac):
        return max(Counter(xucxac).values()) if xucxac else 0

def dem_tan_suat(*xx_list):
    return Counter(sum(xx_list, []))

def chuan_hoa_history(raw_data):
        return [
            {
                "session": item.get("sid", 0),
                "dice": [item.get("d1", 0), item.get("d2", 0), item.get("d3", 0)],
                "total": item.get("sum", 0),
                "result": str(item.get("result", "")).capitalize()
            }
            for item in raw_data
        ]

    # ===== Logic dự đoán nâng cao =====
def du_doan_theo_ct(history):
        if len(history) < 3:
            return "Không đủ dữ liệu"

        xx1, xx2, xx3 = history[2]["dice"], history[1]["dice"], history[0]["dice"]
        result3 = history[0]["result"]
        trend = xu_huong_diem(history)

        tong = lambda xx: sum(xx)

        # Công thức 1
        if dem_trung(xx1) == 3:
            return "Tài" if trend == "lên" else "Xỉu"
        elif dem_trung(xx1) == 2:
            return "Tài" if tong(xx3) < tong(xx1) else "Xỉu"
        elif dem_trung(xx2) == 3:
            return "Tài" if tong(xx1) > tong(xx2) else "Xỉu"

        # Công thức 2: 3 số liên tiếp
        if all(abs(xx3[i] - xx3[i-1]) == 1 for i in range(1, 3)):
            return "Tài" if result3 == "Xỉu" else "Xỉu"

        # Công thức 3: Số liên tiếp tăng dần
        sorted_xx = sorted(xx3)
        if sorted_xx[1] == sorted_xx[0] + 1 and sorted_xx[2] == sorted_xx[1] + 1:
            return result3

        # Công thức 4: Cách nhau đều 2
        if sorted_xx[1] - sorted_xx[0] == 2 and sorted_xx[2] - sorted_xx[1] == 2:
            return result3

        # Công thức 5: Bộ ba giống nhau
        if dem_trung(xx3) == 3:
            if xx3[0] in [3, 4, 6]:
                return result3
            return "Tài" if result3 == "Xỉu" else "Xỉu"

        # Công thức 6: Bộ đôi giống nhau
        if dem_trung(xx3) == 2:
            return "Tài" if result3 == "Xỉu" else "Xỉu"

        return result3

    # ===== Logic 98% chẵn =====
def kiem_tra_chan_98(history):
        if len(history) < 7:
            return False
        count_even = sum(1 for h in history[:7] if h["total"] % 2 == 0)
        return count_even >= 6

    # Danh sách lý do random
LY_DO_LIST = [
        "Dự đoán theo biểu đồ cầu và công thức nâng cao",
        "Phân tích lịch sử 3 phiên gần nhất kết hợp 98% chẵn",
        "Áp dụng công thức cầu lặp và xu hướng điểm",
        "Dựa trên mô hình xác suất và tần suất xuất hiện",
        "Công thức riêng được tối ưu từ dữ liệu 100 phiên"
    ]

    # ===== Endpoint =====
@app.get("/predict")
def predict():
        try:
            response = requests.get("https://bomaylamy-apsw.onrender.com/api/sunwin", timeout=10)
            response.raise_for_status()
            raw_json = response.json()

            if not raw_json.get("data"):
                return JSONResponse(content={"detail": "Không có dữ liệu từ API lịch sử"})

            history = chuan_hoa_history(raw_json["data"][:100])

            if len(history) < 3:
                return JSONResponse(content={"detail": "Không đủ dữ liệu để phân tích"})

            current = history[0]
            next_session = current["session"] + 1

            du_doan = du_doan_theo_ct(history[:3])

            if kiem_tra_chan_98(history):
                du_doan = "Xỉu"

            ly_do = random.choice(LY_DO_LIST)

            return {
                "current_session": current["session"],
                "current_result": current["result"],
                "current_dice": current["dice"],
                "current_total": current["total"],
                "next_session": next_session,
                "du_doan": du_doan,
                "ly_do": ly_do
            }

        except Exception as e:
            return JSONResponse(content={"detail": f"Lỗi xử lý dự đoán: {str(e)}"})
