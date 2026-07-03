import requests
import pandas as pd
from datetime import datetime
import sqlite3 # ✅ CSV 탈출! 파이썬 내장 데이터베이스

def fetch_weather_and_predict():
    # 1. 기상청 API 찌르기 (서울 날씨)
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&current_weather=true"
    print("🌐 기상청 API에 데이터 요청 중...")
    response = requests.get(url)
    data = response.json()
    
    current = data['current_weather']
    temp = current['temperature']
    windspeed = current['windspeed']
    
    # 2. 우리 API 서버에 보낼 재료 준비
    rain = 0 # (일단 비 안 온다고 가정)
    weekend = 1 if datetime.now().weekday() >= 5 else 0
    
    # ★ 핵심: 사무실에서 만든 예측 API 서버(app.py) 찌르기!
    api_url = f"http://127.0.0.1:8000/predict?temp={temp}&rain={rain}&weekend={weekend}"
    
    try:
        print("🚀 로컬 API 서버에 예측 요청 중...")
        api_response = requests.get(api_url)
        # 서버가 준 JSON 답변에서 'expected_rentals' 값만 쏙 빼오기
        expected_rentals = api_response.json().get('expected_rentals', 0)
        print(f"🎯 서버 응답 완료! 지금 날씨({temp}도)의 예상 대여량: {expected_rentals}대")
    except Exception:
        print("⚠️ API 서버가 꺼져 있어서 예상 대여량은 '0'으로 임시 기록합니다.")
        expected_rentals = 0

    # 3. 판다스 표(DataFrame)로 포장 (예측 대여량 컬럼 추가!)
    df = pd.DataFrame([{
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'temperature': temp,
        'windspeed': windspeed,
        'expected_rentals': expected_rentals 
    }])
    
    # 4. ★ CSV 탈출하고 진짜 DB(SQLite)에 밀어 넣기!
    # DB 자물쇠 열기 (파일이 없으면 자기가 알아서 만듭니다)
    conn = sqlite3.connect("bike_pipeline.db") 
    
    # DB 안의 'weather_predict_log'라는 테이블에 데이터 추가 (append)
    df.to_sql("weather_predict_log", conn, if_exists="append", index=False)
    
    # 자물쇠 닫기
    conn.close() 
    print("💾 DB 저장 완료! [bike_pipeline.db] 파일에 차곡차곡 쌓이고 있습니다.")

if __name__ == "__main__":
    fetch_weather_and_predict()