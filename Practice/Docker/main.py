import practice.Docker.data_loader as dl
import practice.Docker.preprocess as prep
import practice.Docker.model as mdl

def main():
    print("--- [서울시 따릉이 대여량 예측 파이프라인 가동] ---")

    # Step 1. 재료 썰어오기
    df = dl.get_bike_data()

    # Step 2. 재료 다듬고 Train/Test 찢기
    X_train, X_test, y_train, y_test = prep.split_train_test(df)

    # Step 3. 요리해서 학습 모델이랑 오차율 받아오기
    trained_model, result_mae = mdl.train_and_evaluate(X_train, X_test, y_train, y_test)

    print(
        f"★ 파이프라인 최종 가동 완료! 모델 평균 오차: {result_mae:.2f}대"
    )


if __name__ == "__main__":
    main()