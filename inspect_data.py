import pandas as pd
import sys
sys.path.append('.')
from src.data_processor import load_data

def inspect_uniques():
    df = load_data("data")
    
    print("--- unique Type of Ball Bowled ---")
    if 'Type of Ball Bowled' in df.columns:
        lengths = df['Type of Ball Bowled'].unique()
        for l in sorted(lengths):
            print(l)
    
    print("\n--- unique Shot Played At ---")
    if 'Shot Played At' in df.columns:
        shots = df['Shot Played At'].unique()
        for s in sorted(shots):
            print(s)

if __name__ == "__main__":
    inspect_uniques()
