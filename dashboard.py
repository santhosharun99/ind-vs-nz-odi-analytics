import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import importlib

# Force Plotly to use White template globally
pio.templates.default = "plotly_white"

import src.data_processor
importlib.reload(src.data_processor)
from src.data_processor import load_data, get_wagon_wheel_data

# Page Config
st.set_page_config(page_title="IND vs NZ Cricket Analytics", page_icon="🏏", layout="wide")

# Custom CSS - Clean Light Theme (India/NZ Palette)
st.markdown("""
<style>
    /* Global Settings */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Poppins', sans-serif;
        color: #333333;
    }
    
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Branding Colors */
    :root {
        --india-blue: #005DA0;
        --india-orange: #FF9933;
        --nz-black: #000000;
        --nz-teal: #00B1B1;
        --card-bg: #F8F9FA;
        --text-primary: #1A1A1A;
    }
    
    /* Headers */
    .main-header {
        font-family: 'Poppins', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--india-blue); /* Default to Blue, can dynamically change */
        border-bottom: 3px solid var(--india-orange);
        display: inline-block;
        margin-bottom: 20px;
        padding-bottom: 5px;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #F0F2F6;
        border-right: 1px solid #E0E0E0;
    }
    
    /* Metric Cards - Clean Light */
    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #E0E0E0;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        color: var(--text-primary);
        border-left: 4px solid var(--india-blue); /* Accent */
    }
    div[data-testid="metric-container"] label {
        color: #666;
        font-weight: 500;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: var(--india-blue);
        font-weight: 700;
    }
    
    /* Charts */
    .stPlotlyChart {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #F0F0F0;
        padding: 10px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 1px solid #eee;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 0px;
        background-color: transparent;
        color: #555;
        border: none;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--india-blue);
        border-bottom: 2px solid var(--india-blue);
    }
    
</style>
""", unsafe_allow_html=True)

# Load Data
@st.cache_data
def get_data_v5():
    data_dir = "data"
    df = load_data(data_dir)
    df = get_wagon_wheel_data(df)
    return df

try:
    df = get_data_v5()
    
    # PATCH: Ensure Over Number and Phase exist (Fallback for reload issues)
    if 'Over Number' not in df.columns and 'Ball' in df.columns:
        df['Over Number'] = df['Ball'].apply(lambda x: int(str(x).split('.')[0]) + 1)
        
    if 'Phase' not in df.columns and 'Over Number' in df.columns:
        def get_phase_local(over):
            if over <= 10: return 'Powerplay (1-10)'
            elif over <= 40: return 'Middle Overs (11-40)'
            else: return 'Death Overs (41-50)'
        df['Phase'] = df['Over Number'].apply(get_phase_local)
        
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if df.empty:
    st.warning("No data found in 'data/' directory. Please verify that CSV files are present.")
    st.stop()

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Match Overview", "Batting Stats", "Bowling Stats", "Player Deep Dive"])

st.sidebar.markdown("---")
st.sidebar.header("Global Filters")

# Match Filter
match_options = list(df['Match'].unique())
selected_match = st.sidebar.selectbox("Select Match", match_options)

# Filter by Match
match_df = df[df['Match'] == selected_match]

# Innings Filter
innings_options = sorted(match_df['Innings'].unique())
selected_innings = st.sidebar.radio("Select Innings", innings_options, format_func=lambda x: f"Innings {x}")

# Filter by Innings
innings_df = match_df[match_df['Innings'] == selected_innings]
filtered_df = innings_df.copy() # Base for further filtering

# --- Global Metrics Logic ---
total_runs_from_bat = innings_df['Runs'].sum()
double_counted_mask = innings_df['Type of Extra'].isin(['Bye', 'Leg Bye', 'Leg bye', 'bye', 'leg bye'])
adj_bat_runs = innings_df.loc[~double_counted_mask, 'Runs'].sum()
extra_runs = pd.to_numeric(innings_df['Run of Extra'], errors='coerce').fillna(0).sum() if 'Run of Extra' in innings_df.columns else 0

# PATCH: 3rd ODI Innings 1 missing Bye
if selected_match == "Ind vs Nz 3rd ODI" and selected_innings == 1:
    extra_runs += 1

total_score = adj_bat_runs + extra_runs
wickets = innings_df[innings_df['Wicket'].notna() & (innings_df['Wicket'] != '') & (innings_df['Wicket'] != 'Unknown')].shape[0]

# --- Page Rendering ---

# Helper for Realistic Pitch Map
def create_pitch_hotspot(df, title="Pitch Hotspot Analysis"):
    # Aggregating by Length Category
    zone_stats = df.groupby('Length Category').agg(
        Balls=('Ball', 'count'),
        Runs=('Runs', 'sum'),
        Wickets=('Wicket', lambda x: x[x != 'Unknown'].count())
    ).reset_index()
    
    total_balls = zone_stats['Balls'].sum()
    zone_stats['Percentage'] = (zone_stats['Balls'] / total_balls * 100).fillna(0)
    zone_stats['Economy'] = (zone_stats['Runs'] / zone_stats['Balls'] * 6).fillna(0)
    
    # Define Zones (Y-coordinates in meters from batting stumps)
    # Pitch is approx 20m long.
    # Yorker: 0-2m, Full: 2-6m, Good: 6-10m, Short: 10m+
    zones = {
        'Yorker': {'y0': 0, 'y1': 2, 'color': 'rgba(255, 0, 0, 0.2)'},
        'Full': {'y0': 2, 'y1': 6, 'color': 'rgba(255, 165, 0, 0.2)'},
        'Good Length': {'y0': 6, 'y1': 10, 'color': 'rgba(255, 255, 0, 0.2)'},
        'Back of Length': {'y0': 10, 'y1': 14, 'color': 'rgba(0, 255, 0, 0.2)'},
        'Short': {'y0': 14, 'y1': 20, 'color': 'rgba(0, 0, 255, 0.2)'},
        'Full Toss': {'y0': 0.5, 'y1': 1.5, 'color': 'rgba(128, 0, 128, 0.2)'} # Overlap yorker slightly
    }
    
    # Map stats to zones
    # We need to draw shapes for each zone
    shapes = []
    annotations = []
    
    # Background Field
    shapes.append(dict(type="rect", x0=-4, y0=-5, x1=4, y1=25, layer="below", line=dict(width=0), fillcolor="#4CAF50")) # Green Grass
    
    # Pitch Strip
    shapes.append(dict(type="rect", x0=-1.52, y0=0, x1=1.52, y1=20.12, layer="below", line=dict(color="#8D6E63", width=2), fillcolor="#E0C9A6")) # Tan Pitch
    
    # Stumps
    # Batting End (Bottom)
    shapes.append(dict(type="rect", x0=-0.11, y0=-0.1, x1=0.11, y1=0, fillcolor="Black", line=dict(width=0)))
    # Bowling End (Top)
    shapes.append(dict(type="rect", x0=-0.11, y0=20.12, x1=0.11, y1=20.22, fillcolor="Black", line=dict(width=0)))
    # Crease Lines
    shapes.append(dict(type="line", x0=-1.3, y0=0, x1=1.3, y1=0, line=dict(color="White", width=2))) # Popping crease
    shapes.append(dict(type="line", x0=-1.3, y0=20.12, x1=1.3, y1=20.12, line=dict(color="White", width=2))) # Bowling crease?
    
    # Heatmap Zones
    max_pct = zone_stats['Percentage'].max() if not zone_stats.empty else 1
    
    for index, row in zone_stats.iterrows():
        length = row['Length Category']
        if length in zones:
            z = zones[length]
            # Intensity based on percentage (Alpha)
            intensity = row['Percentage'] / 100
            # Color scale: Red (More frequent)
            # Or use fixed colors but vary opacity? User asked for Hotspot.
            # Let's use Red for everything but vary opacity based on frequency.
            fill_color = f"rgba(255, 0, 0, {min(0.8, intensity + 0.1)})"
            
            shapes.append(dict(
                type="rect",
                x0=-1.52, y0=z['y0'], x1=1.52, y1=z['y1'],
                line=dict(width=0),
                fillcolor=fill_color,
                layer="above"
            ))
            
            # Annotation text
            label = f"<b>{length}</b><br>{row['Percentage']:.1f}%<br>{row['Runs']} Runs<br>{row['Wickets']} Wkts"
            
            # Fix Overlap: Shift "Full Toss" text to the side, keep "Yorker" in center
            text_x = 0
            if length == 'Full Toss':
                text_x = 2.5 # Shift to right margin
                # Draw a line pointing to it? Optional.
            elif length == 'Yorker':
                text_x = 0 # Center
            
            # Specific adjustments for clarity if zones are close
            
            annotations.append(dict(
                x=text_x, y=(z['y0'] + z['y1'])/2,
                text=label,
                showarrow=False,
                font=dict(color="White" if intensity > 0.4 and length != 'Full Toss' else "Black", size=11),
                bgcolor="rgba(255,255,255,0.7)" if length == 'Full Toss' else None,
                bordercolor="black" if length == 'Full Toss' else None,
                borderwidth=1 if length == 'Full Toss' else 0
            ))

    fig = go.Figure()
    
    # Dummy scatter for hover info? Or just shapes.
    # Add shapes
    fig.update_layout(
        title=title,
        shapes=shapes,
        annotations=annotations,
        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-3, 3]),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-2, 22], autorange="reversed"),
        height=700,
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig

if page == "Match Overview":
    st.markdown(f"<div class='main-header'>🏏 {selected_match} - Innings {selected_innings}</div>", unsafe_allow_html=True)
    
    # Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Score", f"{int(total_score)}/{wickets}")
    c2.metric("Overs", f"{innings_df['Over Number'].max()}")
    c3.metric("Extras", int(extra_runs))
    
    # Run Rate
    balls = len(innings_df)
    rr = (total_score / balls) * 6 if balls > 0 else 0
    c4.metric("Run Rate", f"{rr:.2f}")

    # Worm Graph
    st.markdown("### Match Momentum (Worm Graph)")
    match_progress = innings_df.copy()
        
    runs_per_over = match_progress.groupby('Over Number')['Runs'].sum().reset_index()
    if 'Run of Extra' in match_progress.columns:
        extras_per_over = match_progress.groupby('Over Number')['Run of Extra'].sum().reset_index()
        runs_per_over = pd.merge(runs_per_over, extras_per_over, on='Over Number', how='left').fillna(0)
        runs_per_over['Total Runs'] = runs_per_over['Runs'] + runs_per_over['Run of Extra']
    else:
        runs_per_over['Total Runs'] = runs_per_over['Runs']
        
    runs_per_over['Cumulative Runs'] = runs_per_over['Total Runs'].cumsum()
    
    fig_worm = px.line(runs_per_over, x='Over Number', y='Cumulative Runs', title="Run Progression", markers=True)
    fig_worm.update_layout(height=500, template="plotly_white")
    
    # Add Wickets
    wickets_df = match_progress[match_progress['Wicket'].notna() & (match_progress['Wicket'] != 'Unknown')]
    if not wickets_df.empty:
         wickets_plot = pd.merge(wickets_df[['Over Number']], runs_per_over[['Over Number', 'Cumulative Runs']], on='Over Number', how='left')
         fig_worm.add_trace(go.Scatter(
            x=wickets_plot['Over Number'], 
            y=wickets_plot['Cumulative Runs'],
            mode='markers',
            marker=dict(color='red', size=12, symbol='x'),
            name='Wickets'
        ))
    
    st.plotly_chart(fig_worm, use_container_width=True, theme=None)
    
    # Phase Analysis
    st.markdown("### Phase Analysis")
    phase_stats = innings_df.groupby('Phase').agg(
        Runs=('Runs', 'sum'),
        Balls=('Ball', 'count'),
        Wickets=('Wicket', lambda x: x[x != 'Unknown'].count())
    ).reset_index()
    phase_stats['Run Rate'] = phase_stats['Runs'] / (phase_stats['Balls'] / 6)
    
    phase_order = ['Powerplay (1-10)', 'Middle Overs (11-40)', 'Death Overs (41-50)']
    phase_stats['Phase'] = pd.Categorical(phase_stats['Phase'], categories=phase_order, ordered=True)
    phase_stats = phase_stats.sort_values('Phase')
    
    c1, c2 = st.columns(2)
    
    fig_rr = px.bar(phase_stats, x='Phase', y='Run Rate', title="Run Rate by Phase", text_auto='.2f')
    fig_rr.update_layout(height=400, template="plotly_white")
    
    fig_wkts = px.bar(phase_stats, x='Phase', y='Wickets', title="Wickets Lost by Phase", text_auto=True)
    fig_wkts.update_layout(height=400, template="plotly_white")
    
    c1.plotly_chart(fig_rr, use_container_width=True, theme=None)
    c2.plotly_chart(fig_wkts, use_container_width=True, theme=None)


elif page == "Batting Stats":
    st.markdown(f"<div class='main-header'>Batting Analysis</div>", unsafe_allow_html=True)
    
    # Top Scorers
    batter_stats = innings_df.groupby('Batsman').agg(
        Runs=('Runs', 'sum'),
        Balls=('Ball', 'count'),
        Boundaries=('Runs', lambda x: x.isin([4, 6]).sum())
    ).reset_index().sort_values('Runs', ascending=False).head(10)
    
    batter_stats['Strike Rate'] = (batter_stats['Runs'] / batter_stats['Balls']) * 100
    
    st.subheader("Top Run Scorers")
    st.dataframe(batter_stats.style.format({'Strike Rate': '{:.2f}'}), use_container_width=True)
    
    st.markdown("---")
    st.subheader("Scoring Zones (Combined)")
    # Overall Sector Chart
    if 'Sector' in innings_df.columns:
        sector_runs = innings_df.groupby('Sector')['Runs'].sum().reset_index()
        fig_sec = px.bar_polar(
            sector_runs,
            r="Runs",
            theta="Sector",
            color="Runs",
            template="plotly_white",
            color_continuous_scale=px.colors.sequential.Plasma,
            title=f"Overall Scoring Areas - Innings {selected_innings}"
        )
        fig_sec.update_layout(height=600)
        st.plotly_chart(fig_sec, use_container_width=True, theme=None)

elif page == "Bowling Stats":
    st.markdown(f"<div class='main-header'>Bowling Analysis</div>", unsafe_allow_html=True)
    
    # Top Wicket Takers
    bowler_stats = innings_df.groupby('Bowler').agg(
        Wickets=('Wicket', lambda x: x[x != 'Unknown'].count()),
        Runs_Conceded=('Runs', 'sum'),
        Balls=('Ball', 'count')
    ).reset_index()
    bowler_stats['Overs'] = bowler_stats['Balls'] // 6 + (bowler_stats['Balls'] % 6) / 10
    bowler_stats['Economy'] = bowler_stats['Runs_Conceded'] / (bowler_stats['Balls'] / 6)
    bowler_stats = bowler_stats.sort_values(['Wickets', 'Economy'], ascending=[False, True])
    
    st.subheader("Bowling Card")
    st.dataframe(bowler_stats[['Bowler', 'Overs', 'Runs_Conceded', 'Wickets', 'Economy']].style.format({'Economy': '{:.2f}'}), use_container_width=True)
    
    st.markdown("---")
    st.subheader("Pitch Hotspots (Realistic Match View)")
    
    # Realistic Pitch Map
    fig_hotspot = create_pitch_hotspot(filtered_df, title="Team Bowling Length Distribution")
    st.plotly_chart(fig_hotspot, use_container_width=True, theme=None)
    
    st.info("Red intensity indicates frequency. Labels show Runs Conceded and Wickets taken in that zone.")


elif page == "Player Deep Dive":
    st.markdown(f"<div class='main-header'>Player Head-to-Head Analysis</div>", unsafe_allow_html=True)
    
    batsmen_options = sorted(innings_df['Batsman'].unique())
    selected_player = st.sidebar.selectbox("Select Batsman", batsmen_options)
    
    if selected_player:
        player_df = innings_df[innings_df['Batsman'] == selected_player]
        
        # 1. Key Metrics
        p_runs = player_df['Runs'].sum()
        p_balls = len(player_df)
        p_sr = (p_runs / p_balls * 100) if p_balls else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Runs", p_runs)
        m2.metric("Balls", p_balls)
        m3.metric("Strike Rate", f"{p_sr:.1f}")
        
        st.markdown("---")
        
        # 2. Head-to-Head Table
        st.subheader(f"{selected_player} vs Bowlers")
        
        h2h_df = player_df.groupby('Bowler').agg(
            Runs=('Runs', 'sum'),
            Balls=('Ball', 'count'),
            Dismissals=('Wicket', lambda x: x[x != 'Unknown'].count())
        ).reset_index()
        
        h2h_df['Strike Rate'] = (h2h_df['Runs'] / h2h_df['Balls'] * 100).round(1)
        
        # Sort by Balls Faced
        h2h_df = h2h_df.sort_values('Balls', ascending=False)
        
        st.dataframe(
            h2h_df[['Bowler', 'Runs', 'Balls', 'Dismissals', 'Strike Rate']],
            use_container_width=True,
            hide_index=True
        )
        
        # 3. Granular Matchup Breakdown (New)
        st.markdown("---")
        st.subheader("Granular Matchup Breakdown")
        
        target_bowler = st.selectbox("Drill down vs Bowler:", sorted(player_df['Bowler'].unique()))
        
        if target_bowler:
            matchup_data = player_df[player_df['Bowler'] == target_bowler]
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("##### Hotspot Analysis")
                fig_mu_hotspot = create_pitch_hotspot(matchup_data, title=f"{selected_player} vs {target_bowler} (Pitch Map)")
                st.plotly_chart(fig_mu_hotspot, use_container_width=True, theme=None)
            
            with c2:
                # Group by Length Category
                length_breakdown = matchup_data.groupby('Length Category').agg(
                    Runs=('Runs', 'sum'),
                    Balls=('Ball', 'count'),
                    Dots=('Runs', lambda x: (x==0).sum()),
                    Wickets=('Wicket', lambda x: x[x != 'Unknown'].count())
                ).reset_index()
                
                st.markdown("##### Stats by Length")
                st.dataframe(length_breakdown, use_container_width=True, hide_index=True)

        
        # 4. Shaded Wagon Wheel
        st.subheader("Strong Zones")
        if 'Sector' in player_df.columns:
            region_runs = player_df.groupby('Sector')['Runs'].sum().reset_index()
            fig_p_sec = px.bar_polar(
                region_runs,
                r="Runs",
                theta="Sector",
                color="Runs",
                template="plotly_white",
                color_continuous_scale=px.colors.sequential.Plasma,
                title=f"{selected_player}'s Scoring Areas"
            )
            fig_p_sec.update_layout(height=600)
            st.plotly_chart(fig_p_sec, use_container_width=True, theme=None)

