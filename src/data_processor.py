import pandas as pd
import numpy as np
import os
import glob

def load_data(data_dir):
    """
    Loads all CSV files from the data directory and combines them.
    Adds a 'Match' column based on filename.
    """
    all_files = glob.glob(os.path.join(data_dir, "*.csv"))
    df_list = []
    
    for filename in all_files:
        df = pd.read_csv(filename)
        # Extract match name from filename (e.g., "Ind vs Nz 1st ODI")
        match_name = os.path.basename(filename).split(' - ')[0]
        df['Match'] = match_name
        df_list.append(df)
        
    if not df_list:
        return pd.DataFrame()
        
    combined_df = pd.concat(df_list, ignore_index=True)
    
    # Handle column name typos if present
    if 'Short Played At' in combined_df.columns and 'Shot Played At' not in combined_df.columns:
        combined_df = combined_df.rename(columns={'Short Played At': 'Shot Played At'})
    elif 'Short Played At' in combined_df.columns and 'Shot Played At' in combined_df.columns:
        combined_df['Shot Played At'] = combined_df['Shot Played At'].fillna(combined_df['Short Played At'])
        combined_df = combined_df.drop(columns=['Short Played At'])
        
    return clean_data(combined_df)

def clean_data(df):
    """
    Cleans the dataframe: handles NaNs, ensures numeric types.
    """
    # Fill NaN in Runs with 0
    df['Runs'] = df['Runs'].fillna(0)
    
    # Ensure Runs is numeric, coerce errors just in case
    df['Runs'] = pd.to_numeric(df['Runs'], errors='coerce').fillna(0)
    
    # Normalize text columns
    text_cols = ['Batsman', 'Bowler', 'Type of Ball Bowled', 'Shot Played At', 'Wicket', 'Type of Wicket']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' string with actual empty string or keep as is, but strip helps
            df[col] = df[col].replace('nan', 'Unknown')

    # Apply standardization
    if 'Type of Ball Bowled' in df.columns:
        df['Length Category'] = df['Type of Ball Bowled'].apply(standardize_length)
    if 'Shot Played At' in df.columns:
        df['Shot Category'] = df['Shot Played At'].apply(standardize_shot)
        
    return df

def standardize_length(length_desc):
    """
    Standardizes the bowling length into broader categories.
    """
    l = length_desc.lower()
    
    if 'full' in l or 'overpitched' in l or 'yorker' in l or 'pitched up' in l or 'slot' in l or 'half-volley' in l:
        if 'yorker' in l: return 'Yorker'
        if 'toss' in l: return 'Full Toss'
        return 'Full'
        
    if 'short' in l or 'bouncer' in l or 'bang' in l or 'head' in l:
        return 'Short'
        
    if 'length' in l or 'good' in l or 'back of' in l:
        if 'back of' in l: return 'Back of Length'
        return 'Good Length'
        
    return 'Other'

def standardize_shot(shot_desc):
    """
    Standardizes the shot type into broader categories.
    """
    s = shot_desc.lower()
    
    if 'drive' in s or 'driven' in s or 'cover' in s or 'mid-off' in s or 'long-off' in s:
        return 'Drive'
    if 'pull' in s or 'hook' in s or 'midwicket' in s or 'long-on' in s:
        return 'Pull/On-Drive'
    if 'cut' in s or 'point' in s or 'third' in s:
        return 'Cut/Guide'
    if 'sweep' in s or 'scoop' in s or 'paddle' in s:
        return 'Sweep/Scoop'
    if 'flick' in s or 'leg' in s or 'glance' in s:
        return 'Flick'
    if 'defended' in s or 'block' in s or 'left' in s:
        return 'Defensive'
        
    return 'Other'

def map_shot_to_angle(shot_desc):
    """
    Maps a shot description to an angle (degrees) for the Wagon Wheel.
    0 degrees is behind the wicket (keeper), 90 point, 180 straight, 270 square leg.
    This is an approximation.
    """
    shot = shot_desc.lower()
    
    # Off-side (0 to 180)
    if 'third' in shot or 'fine' in shot and 'leg' not in shot: # Third man / Deep third
        return 45
    if 'point' in shot:
        return 90
    if 'cover' in shot:
        return 135
    if 'mid-off' in shot or 'mid off' in shot:
        return 160
    if 'long-off' in shot or 'long off' in shot:
        return 170
    if 'off side' in shot:
        return 110 # General off side
        
    # Straight
    if 'bowler' in shot or 'punched back' in shot or 'straight' in shot or 'driven' in shot and 'cover' not in shot and 'on' not in shot:
        return 180
    if 'down ground' in shot or 'down pitch' in shot:
        return 180
        
    # On-side (180 to 360)
    if 'long-on' in shot or 'long on' in shot:
        return 190
    if 'mid-on' in shot or 'mid on' in shot:
        return 200
    if 'midwicket' in shot or 'mid-wicket' in shot:
        return 225
    if 'cow corner' in shot:
        return 240
    if 'square' in shot: # Square leg / Deep square
        return 270
    if 'leg side' in shot:
        return 290
    if 'fine leg' in shot or 'fine-leg' in shot:
        return 315
    if 'behind square' in shot:
        return 300
    if 'sweep' in shot: # Sweeps are usually behind square leg to fine leg
        return 300
    if 'hook' in shot or 'pull' in shot: # Usually square or midwicket
        return 250
        
    # Behind / Edges
    if 'edge' in shot or 'slip' in shot or 'keeper' in shot:
        return 0
    if 'defended' in shot or 'block' in shot:
        return -1 # Encode as -1 to filter out or put in center
        
    return -1 # Unknown

def get_wagon_wheel_data(df):
    """
    Adds 'Angle' and 'Region' columns to the dataframe.
    """
    df['Angle'] = df['Shot Played At'].apply(map_shot_to_angle)
    # We can handle distance if we had it, but we don't. 
    # We can simulate distance based on runs: 4/6 are far, 1s are medium, 0s are close.
    
    def simulate_distance(row):
        runs = row['Runs']
        angle = row['Angle']
        if angle == -1: return 0
        if runs >= 6: return 80 + np.random.randint(0, 10)
        if runs == 4: return 70 + np.random.randint(0, 5)
        if runs == 3: return 60
        if runs == 2: return 50
        if runs == 1: return 40
        return 10 # Dot ball / small defensive shot
        
    df['Distance'] = df.apply(simulate_distance, axis=1)
    
    # Add Phases
    df['Over Number'] = df['Ball'].apply(lambda x: int(str(x).split('.')[0]) + 1)
    df['Phase'] = df['Over Number'].apply(get_phase)
    
    # Add Control Metric
    df['In Control'] = df.apply(check_control, axis=1)
    df['Sector'] = df['Angle'].apply(get_sector_name)
    
    return df

def get_phase(over):
    if over <= 10:
        return 'Powerplay (1-10)'
    elif over <= 40:
        return 'Middle Overs (11-40)'
    else:
        return 'Death Overs (41-50)'

def check_control(row):
    """
    Determines if a shot was in control based on description.
    Returns 1 for control, 0 for edge/miss/beaten.
    """
    desc = (str(row.get('Shot Played At', '')) + " " + str(row.get('Type of Wicket', ''))).lower()
    
    # Keywords indicating lack of control
    uncontrolled_keywords = [
        'edge', 'beaten', 'missed', 'dropped', 'mistimed', 'slog', 'leading edge', 
        'thick edge', 'inside edge', 'outside edge', 'play and miss', 'struck on pad',
        'lbw', 'bowled'
    ]
    
    if any(k in desc for k in uncontrolled_keywords):
        return 0
    return 1 # Assume control otherwise

def get_sector_name(angle):
    """Maps angle to cricket field sector name."""
    if angle == 0: return "Behind Wicket (Keeper/Slips)"
    if angle == 45: return "Third Man"
    if angle == 90: return "Point"
    if angle == 110: return "Off Side"
    if angle == 135: return "Cover"
    if angle == 160: return "Mid-Off"
    if angle == 170: return "Long-Off"
    if angle == 180: return "Straight"
    if angle == 190: return "Long-On"
    if angle == 200: return "Mid-On"
    if angle == 225: return "Mid-Wicket"
    if angle == 240: return "Cow Corner"
    if angle == 250: return "Deep Mid-Wicket"
    if angle == 270: return "Square Leg"
    if angle == 290: return "Leg Side"
    if angle == 300: return "Behind Square"
    if angle == 315: return "Fine Leg"
    return "Unknown"
