# [주피터 노트북의 1번 셀이라고 상상해 줘]
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# 1. 가상 데이터셋 대충 생성하기 (실제론 DB나 CSV에서 읽어오는 구간)
np.random.seed(42)
n = 1000
data = {
    'temp': np.random.normal(15, 10, n),               # 기온
    'rain': np.random.choice([0, 1], size=n, p=[0.8, 0.2]), # 비 여부
    'weekend': np.random.choice([0, 1], size=n, p=[0.7, 0.3]) # 주말 여부
}
df = pd.DataFrame(data)

# 따릉이 대여량 공식(가상): 기온 높으면 증가, 비 오면 급감, 주말이면 증가 + 노이즈
df['rentals'] = df['temp']*12 - df['rain']*60 + df['weekend']*40 + np.random.normal(0, 10, n)
df['rentals'] = df['rentals'].apply(lambda x: max(0, int(x))) # 대여량 음수 방지

# 2. 분석가가 대충 짜둔 전처리 로직
df = df.dropna() # 결측치 날리기

X = df[['temp', 'rain', 'weekend']]
y = df['rentals']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. 모델 학습 및 결과 출력
model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)

print(f"★ 모델 학습 완료! 평균 오차(MAE): {mae:.2f}대")