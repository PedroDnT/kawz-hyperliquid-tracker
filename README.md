# Kawz's Hyperliquid Whale Position Tracker

A tool for tracking and analyzing whale positions on Hyperliquid, providing insights into trading patterns of large market participants.

## Features

- **Position Tracking**: Monitor positions from a list of whale addresses on Hyperliquid
- **Data Visualization**: Analyze whale positions through multiple visualizations
- **Sentiment Analysis**: Track market sentiment by coin based on long/short ratios
- **Whale Clustering**: Identify groups of whales with similar trading strategies
- **Custom Filtering**: Query and export data based on specific criteria

## Project Structure

```
.
├── positions.py            # Main script for fetching position data
├── nice_funcs.py           # Helper functions
├── whale_dashboard.py      # Streamlit dashboard for interactive analysis
├── whale_analytics.py      # Advanced analytics with machine learning
├── whale_analysis.ipynb    # Jupyter notebook for interactive analysis
└── bots/
    └── hyperliquid/
        └── data/
            └── ppls_positions/
                ├── whale_addresses.txt     # List of addresses to track
                ├── all_positions.csv       # Raw position data
                └── aggregated_positions.csv # Aggregated position data
```

## Getting Started

### Prerequisites

- Python 3.8+
- Required packages:
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - plotly
  - scikit-learn
  - streamlit (for dashboard)
  - jupyter (for notebook)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/kawz-hyperliquid-tracker.git
cd kawz-hyperliquid-tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the position tracker:
```bash
python positions.py
```

### Running the Dashboard

```bash
streamlit run whale_dashboard.py
```

### Using the Jupyter Notebook

```bash
jupyter notebook whale_analysis.ipynb
```

## Data Sources

The tool uses the Hyperliquid API to fetch position data for monitored addresses.

## License

MIT License

## Acknowledgments

- Hyperliquid for their API
- Various Dune Analytics dashboards for whale address identification 