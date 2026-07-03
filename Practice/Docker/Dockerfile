FROM python:3.10-slim
WORKDIR /app
RUN pip install fastapi uvicorn pandas xgboost scikit-learn joblib requests
COPY . .
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]