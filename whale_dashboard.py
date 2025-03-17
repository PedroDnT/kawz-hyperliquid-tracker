import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(layout="wide", page_title="Whale Position Tracker")

# Dashboard title
st.title("🐳 Hyperliquid Whale Position Tracker")
st.write("Track and analyze whale positions on Hyperliquid")

# Load data
@st.cache_data
def load_data():
    data_path = "bots/hyperliquid/data/ppls_positions"
    positions_file = os.path.join(data_path, "all_positions.csv")
    agg_file = os.path.join(data_path, "aggregated_positions.csv")
    
    # Check if files exist
    if not os.path.exists(positions_file) or not os.path.exists(agg_file):
        st.error("Position data files not found. Run positions.py first!")
        return None, None
    
    # Load the data
    positions_df = pd.read_csv(positions_file)
    agg_df = pd.read_csv(agg_file)
    
    return positions_df, agg_df

positions_df, agg_df = load_data()

if positions_df is None:
    st.stop()

# Add sidebar filters
st.sidebar.header("Filters")

# Coin filter
all_coins = sorted(positions_df['coin'].unique())
selected_coins = st.sidebar.multiselect("Select Coins", all_coins, default=all_coins[:5])

# Direction filter
direction = st.sidebar.radio("Position Direction", ["All", "Long Only", "Short Only"])

# Min position value filter
min_value = st.sidebar.slider("Min Position Value ($)", 
                             min_value=int(positions_df['position_value'].min()),
                             max_value=int(positions_df['position_value'].max()),
                             value=50000,
                             step=10000)

# Apply filters
filtered_df = positions_df[positions_df['coin'].isin(selected_coins) & 
                         (positions_df['position_value'] >= min_value)]

if direction == "Long Only":
    filtered_df = filtered_df[filtered_df['is_long'] == True]
elif direction == "Short Only":
    filtered_df = filtered_df[filtered_df['is_long'] == False]

# Display KPIs in columns
st.header("Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Value Tracked", f"${filtered_df['position_value'].sum():,.0f}")
with col2:
    st.metric("Unique Addresses", f"{filtered_df['address'].nunique():,}")
with col3:
    st.metric("Total Positions", f"{len(filtered_df):,}")
with col4:
    pnl = filtered_df['unrealized_pnl'].sum()
    st.metric("Unrealized PnL", f"${pnl:,.0f}", delta=f"{(pnl/filtered_df['position_value'].sum()*100):.1f}%")

# Tabs for different visualizations
tab1, tab2, tab3, tab4 = st.tabs(["Coin Distribution", "Whale Analysis", "Position Breakdown", "Raw Data"])

with tab1:
    # Coin distribution charts
    st.subheader("Position Distribution by Coin")
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart for distribution
        coin_values = filtered_df.groupby('coin')['position_value'].sum().reset_index()
        fig = px.pie(coin_values, values='position_value', names='coin', 
                     title="Value Distribution by Coin",
                     hole=0.4)
        st.plotly_chart(fig)
    
    with col2:
        # Bar chart for long vs short
        direction_data = filtered_df.groupby(['coin', 'is_long'])['position_value'].sum().reset_index()
        direction_data['direction'] = direction_data['is_long'].map({True: 'Long', False: 'Short'})
        fig = px.bar(direction_data, x='coin', y='position_value', color='direction',
                    title="Long vs Short by Coin",
                    barmode='group')
        st.plotly_chart(fig)

with tab2:
    # Whale analysis
    st.subheader("Top Whales Analysis")
    
    # Top whales by total value
    whale_values = filtered_df.groupby('address')['position_value'].sum().reset_index().sort_values('position_value', ascending=False)
    whale_values = whale_values.head(10)  # Top 10 whales
    
    # Shortened addresses for better display
    whale_values['short_address'] = whale_values['address'].apply(lambda x: f"{x[:6]}...{x[-4:]}")
    
    fig = px.bar(whale_values, x='short_address', y='position_value',
                title="Top 10 Whales by Position Value",
                labels={'short_address': 'Wallet Address', 'position_value': 'Total Position Value ($)'})
    st.plotly_chart(fig)
    
    # Whale positions by coin
    st.subheader("Whale Portfolio Composition")
    
    # Let user select a whale to analyze
    selected_whale = st.selectbox("Select Whale Address to Analyze", 
                                 options=whale_values['address'].tolist(),
                                 format_func=lambda x: f"{x[:6]}...{x[-4:]} (${filtered_df[filtered_df['address']==x]['position_value'].sum():,.0f})")
    
    # Show portfolio composition for selected whale
    whale_portfolio = filtered_df[filtered_df['address'] == selected_whale]
    
    if not whale_portfolio.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart of coins
            fig = px.pie(whale_portfolio, values='position_value', names='coin',
                        title=f"Portfolio Composition for {selected_whale[:6]}...{selected_whale[-4:]}")
            st.plotly_chart(fig)
        
        with col2:
            # Table of positions
            st.dataframe(whale_portfolio[['coin', 'position_value', 'is_long', 'entry_price', 'unrealized_pnl']]
                        .sort_values('position_value', ascending=False)
                        .reset_index(drop=True)
                        .style.format({
                            'position_value': '${:,.0f}',
                            'entry_price': '${:.2f}',
                            'unrealized_pnl': '${:,.0f}'
                        }))

with tab3:
    # Position breakdown
    st.subheader("Position Size Analysis")
    
    # Histogram of position sizes
    fig = px.histogram(filtered_df, x='position_value', nbins=50,
                      title="Distribution of Position Sizes",
                      labels={'position_value': 'Position Value ($)'})
    st.plotly_chart(fig)
    
    # Scatter plot of entry price vs liquidation price
    st.subheader("Entry vs Liquidation Analysis")
    
    # Let user select a coin to analyze
    coin_for_analysis = st.selectbox("Select Coin for Entry/Liquidation Analysis", 
                                    options=selected_coins)
    
    coin_data = filtered_df[filtered_df['coin'] == coin_for_analysis]
    if not coin_data.empty:
        fig = px.scatter(coin_data, x='entry_price', y='liquidation_price', 
                        color='is_long', size='position_value',
                        color_discrete_map={True: 'green', False: 'red'},
                        hover_data=['address', 'position_value', 'unrealized_pnl'],
                        title=f"Entry vs Liquidation Prices for {coin_for_analysis}")
        
        # Add current price line if available
        # You would need to fetch current price data
        # fig.add_hline(y=current_price, line_dash="dash", line_color="gray", annotation_text="Current Price")
        
        st.plotly_chart(fig)

with tab4:
    # Raw data
    st.subheader("Raw Position Data")
    
    # Display the filtered dataframe
    st.dataframe(filtered_df.sort_values(['coin', 'position_value'], ascending=[True, False])
                .reset_index(drop=True)
                .style.format({
                    'position_value': '${:,.0f}',
                    'entry_price': '${:.2f}',
                    'unrealized_pnl': '${:,.0f}',
                    'liquidation_price': '${:.2f}'
                }))
    
    # Download link for the filtered data
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_whale_positions.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("*Data refreshes when positions.py is run*") 