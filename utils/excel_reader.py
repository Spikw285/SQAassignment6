import pandas as pd

def read_testdata(path: str, sheet_name: str = 'login'):
    df = pd.read_excel(path, sheet_name=sheet_name, engine='openpyxl')
    df = df.rename(columns=lambda c: c.strip())
    return df.to_dict(orient='records')
