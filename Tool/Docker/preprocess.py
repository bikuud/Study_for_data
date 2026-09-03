import pandas as pd
from sklearn.model_selection import train_test_split

def split_train_test(df:pd.DataFrame) -> tuple:
    df = df.dropna() # 결측치 날리기
    X = df[['temp', 'rain', 'weekend']]
    y = df['rentals']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test