import streamlit as st
import pandas as pd
import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

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
        else:
            st.warning(f"No data found for ticker: {ticker}")
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

        # Calculate averages for X and Y axes
        x_avg = np.mean(x_values)
        y_avg = np.mean(y_values)

        # Create the scatter plot using seaborn
        plt.figure(figsize=(10, 6))
        scatter = plt.scatter(x=x_values, y=y_values, s=sizes / 1e6, alpha=0.5)

        # Add average lines for X and Y axes
        plt.axvline(x_avg, color="red", linestyle="--", linewidth=2)
        plt.axhline(y_avg, color="blue", linestyle="--", linewidth=2)

        # Add labels
        for i, label in enumerate(labels):
            plt.text(x_values[i], y_values[i], label, ha='center', va='center')

        # Set labels and title
        plt.xlabel('USD CCL' if option == 'CCL' else 'X Axis')
        plt.ylabel('Y Axis')
        plt.title(f'Scatter plot for {option} option')

        # Add grid
        plt.grid(True, which='both', color='lightgray', linestyle='-', linewidth=0.5)

        # Display the plot
        st.pyplot(plt)

    # Display the scatter plot based on the selected option
    create_scatter_plot(option)
