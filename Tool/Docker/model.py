import joblib
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error

def train_and_evaluate(X_train, X_test, y_train, y_test) ->tuple:
    model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    
    joblib.dump(model, "final_bike_model.pkl")
    print("모델 파일(final_bike_model.pkl) 저장 완료!")
    
    return model,mae