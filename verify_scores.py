import pandas as pd
import glob
import os

def verify_scores():
    data_dir = "data"
    all_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    for filename in sorted(all_files):
        print(f"\n--- Analyzing {os.path.basename(filename)} ---")
        df = pd.read_csv(filename)
        
        # Clean numeric columns
        df['Runs'] = pd.to_numeric(df['Runs'], errors='coerce').fillna(0)
        
        # Check Exras
        if 'Run of Extra' in df.columns:
            df['Run of Extra'] = pd.to_numeric(df['Run of Extra'], errors='coerce').fillna(0)
            extras = df['Run of Extra'].sum()
        else:
            extras = 0
            print("WARNING: 'Run of Extra' column not found!")
            
        bat_runs = df['Runs'].sum()
        total_score = bat_runs + extras
        
        # Group by innings if multiple innings in one file (usually these files seem to be one innings per file or mixed)
        if 'Innings' in df.columns:
            innings_groups = df.groupby('Innings')
            for inn, group in innings_groups:
                inn_bat = group['Runs'].sum()
                inn_extra = 0
                if 'Run of Extra' in group.columns:
                    inn_extra = pd.to_numeric(group['Run of Extra'], errors='coerce').fillna(0).sum()
                
                print(f"Innings {inn}: Bat {inn_bat} + Extras {inn_extra} = {inn_bat + inn_extra}")
                print(f"  (Rows: {len(group)})")
        else:
             print(f"Total: Bat {bat_runs} + Extras {extras} = {total_score}")

if __name__ == "__main__":
    verify_scores()
