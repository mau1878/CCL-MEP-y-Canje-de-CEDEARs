import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
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
    return data

# Get unique tickers
tickers = set(data["CEDEAR ARS"].unique()) | set(data["CEDEAR D"].unique()) | set(data["Subyacente"].unique())
tickers = [ticker + ".BA" for ticker in tickers]

# Fetch the latest price and volume data
latest_data = fetch_latest_data(tickers)

# User selection: CCL, MEP, or Canje
option = st.selectbox("Select the type of operation:", ["CCL", "MEP", "Canje"])

# Add an "Enter" button
if st.button("Enter"):
    # Define a function to create scatter plots based on the selected option
    def create_scatter_plot(option):
        x_values = []
        y_values = []
        sizes = []
        labels = []

        for _, row in data.iterrows():
            if option == "CCL":
                x_value = latest_data.get(row["CEDEAR ARS"] + ".BA", {}).get("price", np.nan) * row["Ratio de conversión"] / latest_data.get(row["Subyacente"] + ".BA", {}).get("price", np.nan)
                y_value = latest_data.get(row["CEDEAR ARS"] + ".BA", {}).get("volume", 0) * latest_data.get(row["CEDEAR ARS"] + ".BA", {}).get("price", 0)
                size = y_value
            elif option == "MEP":
                x_value = latest_data.get(row["CEDEAR ARS"] + ".BA", {}).get("price", np.nan) / latest_data.get(row["CEDEAR D"] + ".BA", {}).get("price", np.nan)
                y_value = latest_data.get(row["CEDEAR D"] + ".BA", {}).get("volume", 0) * latest_data.get(row["CEDEAR D"] + ".BA", {}).get("price", 0)
                size = y_value
            elif option == "Canje":
                x_value = latest_data.get(row["CEDEAR D"] + ".BA", {}).get("price", np.nan) * row["Ratio de conversión"] / latest_data.get(row["Subyacente"] + ".BA", {}).get("price", np.nan)
                y_value = latest_data.get(row["CEDEAR ARS"] + ".BA", {}).get("price", np.nan) / latest_data.get(row["CEDEAR D"] + ".BA", {}).get("price", np.nan)
                size = latest_data.get(row["CEDEAR D"] + ".BA", {}).get("volume", 0) * latest_data.get(row["CEDEAR D"] + ".BA", {}).get("price", 0)
            
            if not np.isnan(x_value) and not np.isnan(y_value):
                x_values.append(x_value)
                y_values.append(y_value)
                sizes.append(size)
                labels.append(f'{row["CEDEAR ARS"]} - {row["CEDEAR D"]} - {row["Subyacente"]}')
        
        # Convert sizes to logarithmic scale
        sizes = np.log(sizes)

        # Create the scatter plot using Plotly
        fig = px.scatter(x=x_values, y=y_values, size=sizes, hover_name=labels,
                         labels={'x': 'X Axis', 'y': 'Y Axis'},
                         title=f'Scatter plot for {option} option',
                         size_max=50, log_y=True)

        # Add sliders for adjusting percentiles and axes
        st.plotly_chart(fig, use_container_width=True)

    # Display the scatter plot based on the selected option
    create_scatter_plot(option)
