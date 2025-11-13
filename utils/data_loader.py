import pandas as pd

def load_shutsuba_data(file_path: str):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"CSV読み込みエラー: {e}")
        return None
