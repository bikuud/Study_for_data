import pandas as pd
import numpy as np

def get_bike_data(n:int=1000) -> pd.DataFrame:
    np.random.seed(42)
    data = {
    'temp': np.random.normal(15, 10, n),               # 기온
    'rain': np.random.choice([0, 1], size=n, p=[0.8, 0.2]), # 비 여부
    'weekend': np.random.choice([0, 1], size=n, p=[0.7, 0.3]) # 주말 여부
    }
    df = pd.DataFrame(data)
    df['rentals'] = df['temp']*12 - df['rain']*60 + df['weekend']*40 + np.random.normal(0, 10, n)
    df['rentals'] = df['rentals'].apply(lambda x: max(0, int(x))) # 대여량 음수 방지

    return df