#!/usr/bin/env python3
"""
Hyperliquid Whale Analytics
This script analyzes whale positions to identify patterns and generate insights.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# Configure visualization settings
plt.style.use('ggplot')
sns.set_palette("viridis")
plt.rcParams['figure.figsize'] = (12, 8)

class WhaleAnalytics:
    def __init__(self, data_dir="bots/hyperliquid/data/ppls_positions"):
        """Initialize the whale analytics tool with the data directory."""
        self.data_dir = data_dir
        self.positions_file = os.path.join(data_dir, "all_positions.csv")
        self.agg_file = os.path.join(data_dir, "aggregated_positions.csv")
        self.output_dir = os.path.join(data_dir, "analytics")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load data
        self.load_data()
        
    def load_data(self):
        """Load position data from CSV files."""
        try:
            self.positions_df = pd.read_csv(self.positions_file)
            self.agg_df = pd.read_csv(self.agg_file)
            print(f"✅ Loaded data: {len(self.positions_df)} positions from {self.positions_df['address'].nunique()} unique addresses")
        except FileNotFoundError:
            print(f"❌ Error: Position data files not found at {self.data_dir}")
            print("Please run positions.py first to generate the data files.")
            raise
            
    def identify_whale_clusters(self, min_positions=3):
        """
        Identify clusters of whales with similar trading patterns.
        Returns a dictionary mapping cluster IDs to lists of addresses.
        """
        # Focus on whales with multiple positions
        whale_counts = self.positions_df['address'].value_counts()
        active_whales = whale_counts[whale_counts >= min_positions].index.tolist()
        
        # Create a features matrix: which coins they're trading and direction
        coins = self.positions_df['coin'].unique()
        
        # For each whale, create a profile of their positions
        whale_profiles = []
        
        for whale in active_whales:
            whale_data = self.positions_df[self.positions_df['address'] == whale]
            profile = {'address': whale}
            
            # Total value of positions
            profile['total_value'] = whale_data['position_value'].sum()
            
            # Percentage long vs short
            long_value = whale_data[whale_data['is_long']]['position_value'].sum()
            profile['pct_long'] = long_value / profile['total_value'] if profile['total_value'] > 0 else 0
            
            # For each coin, what percentage of their portfolio
            for coin in coins:
                coin_value = whale_data[whale_data['coin'] == coin]['position_value'].sum()
                profile[f'pct_{coin}'] = coin_value / profile['total_value'] if profile['total_value'] > 0 else 0
            
            whale_profiles.append(profile)
        
        # Convert to DataFrame
        profiles_df = pd.DataFrame(whale_profiles)
        
        # Use a simple clustering approach based on portfolio composition
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        # Prepare features for clustering (excluding address and total_value)
        feature_cols = [col for col in profiles_df.columns if col not in ['address', 'total_value']]
        X = profiles_df[feature_cols].values
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Determine optimal number of clusters
        from sklearn.metrics import silhouette_score
        
        silhouette_scores = []
        K = range(2, min(10, len(active_whales) // 5 + 1))  # Try up to 10 clusters or 1/5 of active whales
        
        for k in K:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            silhouette_avg = silhouette_score(X_scaled, cluster_labels)
            silhouette_scores.append(silhouette_avg)
        
        # Choose number of clusters with highest silhouette score
        optimal_k = K[np.argmax(silhouette_scores)] if silhouette_scores else 3
        
        # Final clustering
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        profiles_df['cluster'] = kmeans.fit_predict(X_scaled)
        
        # Create a dictionary mapping cluster IDs to lists of addresses
        clusters = {}
        for cluster_id in profiles_df['cluster'].unique():
            clusters[cluster_id] = profiles_df[profiles_df['cluster'] == cluster_id]['address'].tolist()
        
        print(f"✅ Identified {optimal_k} whale clusters")
        
        # Save cluster data
        clusters_file = os.path.join(self.output_dir, "whale_clusters.csv")
        profiles_df.to_csv(clusters_file, index=False)
        
        # Generate cluster visualization
        plt.figure(figsize=(10, 6))
        plt.bar(silhouette_scores.index, silhouette_scores)
        plt.xlabel('Number of Clusters')
        plt.ylabel('Silhouette Score')
        plt.title('Optimal Number of Whale Clusters')
        plt.savefig(os.path.join(self.output_dir, "cluster_analysis.png"), dpi=300, bbox_inches='tight')
        
        return clusters, profiles_df
    
    def analyze_whale_behavior(self):
        """
        Analyze whale behavior patterns and generate insights.
        """
        # Group whales by their main trading coin
        whale_main_coins = {}
        
        for address in self.positions_df['address'].unique():
            whale_data = self.positions_df[self.positions_df['address'] == address]
            if whale_data.empty:
                continue
            
            # Find the coin with the highest position value
            coin_values = whale_data.groupby('coin')['position_value'].sum()
            if coin_values.empty:
                continue
                
            main_coin = coin_values.idxmax()
            main_value = coin_values.max()
            
            whale_main_coins[address] = {
                'main_coin': main_coin,
                'main_value': main_value,
                'total_value': whale_data['position_value'].sum(),
                'concentration': main_value / whale_data['position_value'].sum(),
                'position_count': len(whale_data),
                'is_mostly_long': whale_data[whale_data['is_long']]['position_value'].sum() > whale_data[~whale_data['is_long']]['position_value'].sum()
            }
        
        # Convert to DataFrame
        whale_profile_df = pd.DataFrame.from_dict(whale_main_coins, orient='index')
        whale_profile_df.reset_index(inplace=True)
        whale_profile_df.rename(columns={'index': 'address'}, inplace=True)
        
        # Save whale profile data
        profile_file = os.path.join(self.output_dir, "whale_profiles.csv")
        whale_profile_df.to_csv(profile_file, index=False)
        
        # Generate insights about whale concentration
        plt.figure(figsize=(12, 6))
        sns.histplot(whale_profile_df['concentration'], bins=20, kde=True)
        plt.axvline(0.5, color='red', linestyle='--', label='50% Concentration')
        plt.title('Distribution of Whale Portfolio Concentration')
        plt.xlabel('Concentration (% in main coin)')
        plt.ylabel('Number of Whales')
        plt.legend()
        plt.savefig(os.path.join(self.output_dir, "whale_concentration.png"), dpi=300, bbox_inches='tight')
        
        # Generate insights about main coins
        plt.figure(figsize=(12, 6))
        coin_counts = whale_profile_df['main_coin'].value_counts()
        sns.barplot(x=coin_counts.index, y=coin_counts.values)
        plt.title('Most Popular Main Trading Coins Among Whales')
        plt.xlabel('Coin')
        plt.ylabel('Number of Whales')
        plt.xticks(rotation=45)
        plt.savefig(os.path.join(self.output_dir, "main_coins.png"), dpi=300, bbox_inches='tight')
        
        # Calculate market sentiment by coin
        sentiment_by_coin = {}
        
        for coin in self.positions_df['coin'].unique():
            coin_data = self.positions_df[self.positions_df['coin'] == coin]
            if coin_data.empty:
                continue
                
            long_value = coin_data[coin_data['is_long']]['position_value'].sum()
            short_value = coin_data[~coin_data['is_long']]['position_value'].sum()
            total_value = long_value + short_value
            
            if total_value == 0:
                continue
                
            sentiment = (long_value - short_value) / total_value  # -1 to 1 scale
            
            sentiment_by_coin[coin] = {
                'long_value': long_value,
                'short_value': short_value,
                'total_value': total_value,
                'sentiment': sentiment,
                'whale_count': coin_data['address'].nunique()
            }
        
        # Convert to DataFrame
        sentiment_df = pd.DataFrame.from_dict(sentiment_by_coin, orient='index')
        sentiment_df.reset_index(inplace=True)
        sentiment_df.rename(columns={'index': 'coin'}, inplace=True)
        
        # Save sentiment data
        sentiment_file = os.path.join(self.output_dir, "market_sentiment.csv")
        sentiment_df.to_csv(sentiment_file, index=False)
        
        # Generate sentiment visualization
        plt.figure(figsize=(12, 6))
        sns.barplot(x='coin', y='sentiment', data=sentiment_df.sort_values('total_value', ascending=False).head(10))
        plt.axhline(0, color='black', linestyle='-')
        plt.title('Market Sentiment by Coin (Top 10 by Volume)')
        plt.xlabel('Coin')
        plt.ylabel('Sentiment (-1 = Bearish, 1 = Bullish)')
        plt.xticks(rotation=45)
        plt.savefig(os.path.join(self.output_dir, "market_sentiment.png"), dpi=300, bbox_inches='tight')
        
        return whale_profile_df, sentiment_df
    
    def generate_report(self):
        """
        Generate a comprehensive whale analytics report.
        """
        # Get clusters and whale profiles
        clusters, profiles_df = self.identify_whale_clusters()
        whale_profiles, sentiment_df = self.analyze_whale_behavior()
        
        # Generate summary statistics
        total_value = self.positions_df['position_value'].sum()
        total_whales = self.positions_df['address'].nunique()
        total_positions = len(self.positions_df)
        avg_positions_per_whale = total_positions / total_whales if total_whales > 0 else 0
        
        # Generate HTML report
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
        <html>
        <head>
            <title>Hyperliquid Whale Analytics Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; min-width: 200px; }}
                .metric h3 {{ margin: 0; font-size: 16px; }}
                .metric p {{ margin: 5px 0 0; font-size: 24px; font-weight: bold; }}
                img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>🐳 Hyperliquid Whale Analytics Report</h1>
            <p>Generated on {now}</p>
            
            <h2>Overview</h2>
            <div style="display: flex; flex-wrap: wrap;">
                <div class="metric">
                    <h3>Total Value Tracked</h3>
                    <p>${total_value:,.0f}</p>
                </div>
                <div class="metric">
                    <h3>Total Whales</h3>
                    <p>{total_whales:,}</p>
                </div>
                <div class="metric">
                    <h3>Total Positions</h3>
                    <p>{total_positions:,}</p>
                </div>
                <div class="metric">
                    <h3>Avg Positions/Whale</h3>
                    <p>{avg_positions_per_whale:.1f}</p>
                </div>
            </div>
            
            <h2>Whale Clusters</h2>
            <p>We identified {len(clusters)} distinct whale trading patterns:</p>
            <table>
                <tr>
                    <th>Cluster</th>
                    <th>Whale Count</th>
                    <th>Avg Portfolio Value</th>
                    <th>Most Common Coin</th>
                    <th>Long/Short Bias</th>
                </tr>
        """
        
        # Add cluster data to HTML
        for cluster_id, addresses in clusters.items():
            cluster_df = profiles_df[profiles_df['cluster'] == cluster_id]
            cluster_positions = self.positions_df[self.positions_df['address'].isin(addresses)]
            
            # Most common coin
            coin_values = cluster_positions.groupby('coin')['position_value'].sum()
            most_common_coin = coin_values.idxmax() if not coin_values.empty else "N/A"
            
            # Long/short bias
            long_value = cluster_positions[cluster_positions['is_long']]['position_value'].sum()
            short_value = cluster_positions[~cluster_positions['is_long']]['position_value'].sum()
            bias = "Long" if long_value > short_value else "Short"
            bias_pct = (max(long_value, short_value) / (long_value + short_value) * 100) if (long_value + short_value) > 0 else 0
            
            html += f"""
                <tr>
                    <td>Cluster {cluster_id}</td>
                    <td>{len(addresses)}</td>
                    <td>${cluster_df['total_value'].mean():,.0f}</td>
                    <td>{most_common_coin}</td>
                    <td>{bias} ({bias_pct:.1f}%)</td>
                </tr>
            """
        
        html += """
            </table>
            
            <div>
                <img src="cluster_analysis.png" alt="Cluster Analysis">
            </div>
            
            <h2>Market Sentiment</h2>
            <p>Current whale sentiment by top coins:</p>
            <div>
                <img src="market_sentiment.png" alt="Market Sentiment">
            </div>
            
            <table>
                <tr>
                    <th>Coin</th>
                    <th>Total Value</th>
                    <th>Long Value</th>
                    <th>Short Value</th>
                    <th>Sentiment</th>
                    <th>Whale Count</th>
                </tr>
        """
        
        # Add sentiment data to HTML
        for _, row in sentiment_df.sort_values('total_value', ascending=False).head(10).iterrows():
            sentiment_class = "positive" if row['sentiment'] > 0 else "negative"
            html += f"""
                <tr>
                    <td>{row['coin']}</td>
                    <td>${row['total_value']:,.0f}</td>
                    <td>${row['long_value']:,.0f}</td>
                    <td>${row['short_value']:,.0f}</td>
                    <td style="color: {'green' if row['sentiment'] > 0 else 'red'};">{row['sentiment']:.2f}</td>
                    <td>{row['whale_count']}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Whale Concentration</h2>
            <p>How concentrated are whale portfolios in their main coins:</p>
            <div>
                <img src="whale_concentration.png" alt="Whale Concentration">
            </div>
            
            <h2>Top Whales by Portfolio Value</h2>
            <table>
                <tr>
                    <th>Whale Address</th>
                    <th>Total Value</th>
                    <th>Main Coin</th>
                    <th>Main Coin Value</th>
                    <th>Concentration</th>
                    <th>Position Count</th>
                    <th>Bias</th>
                </tr>
        """
        
        # Add top whale data to HTML
        for _, row in whale_profiles.sort_values('total_value', ascending=False).head(20).iterrows():
            html += f"""
                <tr>
                    <td>{row['address'][:6]}...{row['address'][-4:]}</td>
                    <td>${row['total_value']:,.0f}</td>
                    <td>{row['main_coin']}</td>
                    <td>${row['main_value']:,.0f}</td>
                    <td>{row['concentration']:.2f}</td>
                    <td>{row['position_count']}</td>
                    <td>{"Long" if row['is_mostly_long'] else "Short"}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Most Popular Coins</h2>
            <div>
                <img src="main_coins.png" alt="Popular Coins">
            </div>
            
            <h2>Conclusion</h2>
            <p>
                This analysis provides insights into the trading patterns of Hyperliquid whales.
                Understanding these patterns can help identify market trends and potential trading opportunities.
            </p>
            
            <footer>
                <p>Report generated with Hyperliquid Whale Analytics Tool</p>
            </footer>
        </body>
        </html>
        """
        
        # Save HTML report
        report_file = os.path.join(self.output_dir, "whale_analytics_report.html")
        with open(report_file, 'w') as f:
            f.write(html)
        
        print(f"✅ Analytics report generated at {report_file}")
        
        return report_file

if __name__ == "__main__":
    try:
        analyzer = WhaleAnalytics()
        report_file = analyzer.generate_report()
        print(f"\n🎉 Analysis complete! View your report at: {report_file}")
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}") 