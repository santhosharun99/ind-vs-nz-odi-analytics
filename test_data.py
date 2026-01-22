import sys
import os
sys.path.append('.')
from src.data_processor import load_data, get_wagon_wheel_data

def test():
    data_dir = "data"
    df = load_data(data_dir)
    if df.empty:
        print("FAILED: Dataframe is empty")
        return
        
    df = get_wagon_wheel_data(df)
    print(f"SUCCESS: Loaded {len(df)} rows.")
    print("Columns:", df.columns.tolist())
    print("Sample Angles:", df['Angle'].head().tolist())
    print("Sample Matches:", df['Match'].unique())

if __name__ == "__main__":
    test()
