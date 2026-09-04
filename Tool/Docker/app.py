from fastapi import FastAPI
import joblib
import pandas as pd 

app=FastAPI(title='따릉이 대여량 예측 APIR')


try:
    model=joblib.load("final_bike_model.pkl")
    print('피클 모델 로드 완료!')
except FileNotFoundError:
    print('에러: final_bike_model.pkl 파일이 없습니다.')
    model=None
    
@app.get("/")
def read_root():
    return {"message": "환영합니다! 따릉이 대여량 예측 AI 서버가 정상 가동 중입니다."}

# 4. ★ 핵심 예측 API (주문받는 곳)
@app.get("/predict")
def predict_bike(temp: float, rain: int, weekend: int):
    """
    프론트엔드에서 기온(temp), 비 여부(rain), 주말 여부(weekend)를 보내면
    예측된 대여량을 반환합니다.
    """
    if model is None:
        return {"error": "모델이 준비되지 않았습니다."}
        
    # 1. 프론트엔드가 보낸 숫자를 판다스 표(DataFrame)로 포장
    input_data = pd.DataFrame({
        "temp": [temp],
        "rain": [rain],
        "weekend": [weekend]
    })
    
    # 2. 모델에게 예측 지시
    prediction = model.predict(input_data)
    
    # 3. 예측 결과를 딕셔너리로 깔끔하게 반환 (JSON 형태로 프론트엔드에 전달됨)
    return {"expected_rentals": int(prediction[0])}