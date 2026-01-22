import pandas as pd
import glob
import os

def check_3rd_odi():
    filename = "data/Ind vs Nz 1st ODI - Sheet1.csv"
    if not os.path.exists(filename):
        print("File not found")
        return
        
    df = pd.read_csv(filename)
    df = df[df['Innings'] == 1]
    
    df['Runs'] = pd.to_numeric(df['Runs'], errors='coerce').fillna(0)
    df['Run of Extra'] = pd.to_numeric(df['Run of Extra'], errors='coerce').fillna(0)
    
    print("Total Runs (Bat):", df['Runs'].sum())
    print("Total Extras:", df['Run of Extra'].sum())
    print("Grand Total:", df['Runs'].sum() + df['Run of Extra'].sum())
    
    print("\nRows with Extras:")
    extras_df = df[df['Run of Extra'] > 0]
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(extras_df[['Ball', 'Runs', 'Type of Extra', 'Run of Extra']])

if __name__ == "__main__":
    check_3rd_odi()
