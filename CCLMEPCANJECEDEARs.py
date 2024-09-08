import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load the CSV file
csv_file_path = "CEDEARsratios.csv"
data = pd.read_csv(csv_file_path)

# Fetch the latest data from yfinance
def fetch_latest_data(tickers):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            data[ticker] = {
                "price": hist['Close'].iloc[-1],
                "volume": hist['Volume'].iloc[-1],
            }
    return data

# Get unique tickers based on the selected option
def get_required_tickers(option):
    if option == "CCL":
        return set(data["CEDEAR ARS"].unique()) | set(data["Subyacente"].unique())
    elif option == "MEP":
        return set(data["CEDEAR ARS"].unique()) | set(data["CEDEAR D"].unique())
    elif option == "Canje":
        return set(data["CEDEAR D"].unique()) | set(data["Subyacente"].unique())

# User selection: CCL, MEP, or Canje
option = st.selectbox("Select the type of operation:", ["CCL", "MEP", "Canje"])

# Add an "Enter" button
if st.button("Enter"):
    # Fetch only the necessary data after "Enter" is pressed
    tickers = get_required_tickers(option)
    latest_data = fetch_latest_data(tickers)
    
    # Define a function to create scatter plots based on the selected option
    def create_scatter_plot(option):
        x_values = []
        y_values = []
        sizes = []
        labels = []
    
        for _, row in data.iterrows():
            if option == "CCL":
                x_value = latest_data.get(row["CEDEAR ARS"], {}).get("price", np.nan) * row["Ratio de conversión"] / latest_data.get(row["Subyacente"], {}).get("price", np.nan)
                y_value = latest_data.get(row["CEDEAR ARS"], {}).get("volume", 0) * latest_data.get(row["CEDEAR ARS"], {}).get("price", 0)
                size = y_value
            elif option == "MEP":
                x_value = latest_data.get(row["CEDEAR ARS"], {}).get("price", np.nan) / latest_data.get(row["CEDEAR D"], {}).get("price", np.nan)
                y_value = latest_data.get(row["CEDEAR D"], {}).get("volume", 0) * latest_data.get(row["CEDEAR D"], {}).get("price", 0)
                size = y_value
            elif option == "Canje":
                x_value = latest_data.get(row["CEDEAR D"], {}).get("price", np.nan) * row["Ratio de conversión"] / latest_data.get(row["Subyacente"], {}).get("price", np.nan)
                y_value = latest_data.get(row["CEDEAR ARS"], {}).get("price", np.nan) / latest_data.get(row["CEDEAR D"], {}).get("price", np.nan)
                size = latest_data.get(row["CEDEAR D"], {}).get("volume", 0) * latest_data.get(row["CEDEAR D"], {}).get("price", 0)
            
            if not np.isnan(x_value) and not np.isnan(y_value):
                x_values.append(x_value)
                y_values.append(y_value)
                sizes.append(size)
                # Label using "CEDEAR ARS" without ".BA" suffix
                labels.append(row["CEDEAR ARS"].replace(".BA", ""))
    
        # Use arithmetic scale for bubble sizes
        sizes = np.array(sizes)
        
        # Adjust sizes for plotting (since sizes in plt.scatter are in points^2)
        # Let's normalize sizes to have a reasonable size on the plot
        # For example, we can normalize sizes between 50 and 2000 points^2
        min_size = 50
        max_size = 2000
        size_min = sizes.min()
        size_max = sizes.max()
        if size_max - size_min > 0:
            sizes_scaled = min_size + (sizes - size_min) * (max_size - min_size) / (size_max - size_min)
        else:
            sizes_scaled = np.full_like(sizes, min_size)
        
        # Calculate averages for X and Y axes
        x_avg = np.mean(x_values)
        y_avg = np.mean(y_values)
        
        # Create the scatter plot using matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
    
        scatter = ax.scatter(x_values, y_values, s=sizes_scaled, c=np.arange(len(x_values)), cmap='viridis', alpha=0.6)
    
        # Add labels inside the bubbles
        for i, label in enumerate(labels):
            ax.text(x_values[i], y_values[i], label, ha='center', va='center', fontsize=8)
    
        # Add average lines for X and Y axes
        ax.axvline(x=x_avg, color='red', linestyle='--', linewidth=1)
        ax.axhline(y=y_avg, color='blue', linestyle='--', linewidth=1)
    
        # Set logarithmic scale for Y axis if required
        ax.set_yscale('log')
    
        # Add grid lines for both axes
        ax.grid(True, which='both', linestyle='-', linewidth=0.5, color='lightgray')
    
        # Set labels and title
        ax.set_xlabel('USD CCL' if option == 'CCL' else 'X Axis')
        ax.set_ylabel('Y Axis')
        ax.set_title(f'Scatter plot for {option} option')
    
        # Adjust layout
        plt.tight_layout()
    
        # Display the plot in Streamlit
        st.pyplot(fig)
    
    # Display the scatter plot based on the selected option
    create_scatter_plot(option)
