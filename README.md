# IND vs NZ ODI Analytics Dashboard 🏏

An interactive cricket analytics dashboard visualizing the 2023 India vs New Zealand ODI series.

## Features
- **Match Overview**: Worm graphs, Run Rate analysis, and Phase breakdowns.
- **Detailed Stats**: Top run scorers, bowling economy rates, and wicket tickers.
- **Realistic Pitch Maps**: Visualizing bowling lengths on a graphical cricket pitch.
- **Granular Matchups**: Analyze specific batsman vs bowler contests with hotspot maps.
- **Clean UI**: Custom Light Theme with India/NZ brand colors.

## Tech Stack
- Python
- Streamlit
- Plotly Express & Graph Objects
- Pandas

## How to Run Locally
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run dashboard.py
   ```

## Data
Ball-by-ball data for the three ODIs (January 2023) was web-scraped from public online match commentary and saved as CSVs in `data/`. Rights to the underlying match data stay with the original publishers.
