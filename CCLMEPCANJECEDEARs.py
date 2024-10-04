import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt

# Load the CSV file and clean duplicate headers
csv_file_path = "CEDEARsratios.csv"
data = pd.read_csv(csv_file_path)
data = data[data['CEDEAR ARS'] != 'CEDEAR ARS']

# Convert 'Ratio de conversión' to numeric
data['Ratio de conversión'] = pd.to_numeric(data['Ratio de conversión'], errors='coerce')
data = data.dropna(subset=['Ratio de conversión'])

# Adjust tickers for yfinance
def adjust_ticker(ticker):
  return ticker.strip()

data['CEDEAR ARS yfinance'] = data['CEDEAR ARS'].apply(adjust_ticker)
data['CEDEAR D yfinance'] = data['CEDEAR D'].apply(adjust_ticker)
data['Subyacente yfinance'] = data['Subyacente'].apply(adjust_ticker)

# Fetch the latest data from yfinance
def fetch_latest_data(tickers):
  data_dict = {}
  tickers_list = list(tickers)
  if len(tickers_list) == 0:
      st.warning("No tickers to fetch.")
      return data_dict

  hist = yf.download(tickers_list, period="1d", group_by='ticker', threads=True)
  if 'Close' in hist.columns:
      # Only one ticker
      hist = {tickers_list[0]: hist}
  else:
      # Multiple tickers
      pass

  for ticker in tickers_list:
      try:
          if ticker in hist and not hist[ticker].empty:
              data_dict[ticker] = {
                  "price": hist[ticker]['Close'].iloc[-1],
                  "volume": hist[ticker]['Volume'].iloc[-1],
              }
          else:
              st.warning(f"No data found for ticker: {ticker}")
      except Exception as e:
          st.warning(f"Error fetching data for ticker: {ticker} ({e})")
  return data_dict

# Get unique tickers based on the selected option
def get_required_tickers(option, data):
  if option == "CCL":
      tickers = set(data["CEDEAR ARS yfinance"].unique()) | set(data["Subyacente yfinance"].unique())
  elif option == "MEP":
      tickers = set(data["CEDEAR ARS yfinance"].unique()) | set(data["CEDEAR D yfinance"].unique())
  elif option == "Canje":
      tickers = set(data["CEDEAR D yfinance"].unique()) | set(data["Subyacente yfinance"].unique())
  else:
      tickers = set()
  return tickers

# Define a function to create scatter plots based on the selected option
def create_scatter_plot(option, data, latest_data):
  x_values = []
  y_values = []
  sizes = []
  labels = []

  for _, row in data.iterrows():
      try:
          ceade_ar_ticker = row["CEDEAR ARS yfinance"]
          ceade_d_ticker = row["CEDEAR D yfinance"]
          subyacente_ticker = row["Subyacente yfinance"]

          if option == "CCL":
              if ceade_ar_ticker in latest_data and subyacente_ticker in latest_data:
                  ceade_ar_price = latest_data[ceade_ar_ticker]["price"]
                  subyacente_price = latest_data[subyacente_ticker]["price"]
                  x_value = (ceade_ar_price * row["Ratio de conversión"]) / subyacente_price
                  y_value = latest_data[ceade_ar_ticker]["volume"] * ceade_ar_price
                  size = y_value
              else:
                  continue
          elif option == "MEP":
              if ceade_ar_ticker in latest_data and ceade_d_ticker in latest_data:
                  ceade_ar_price = latest_data[ceade_ar_ticker]["price"]
                  ceade_d_price = latest_data[ceade_d_ticker]["price"]
                  x_value = ceade_ar_price / ceade_d_price
                  y_value = latest_data[ceade_d_ticker]["volume"] * ceade_d_price
                  size = y_value
              else:
                  continue
          elif option == "Canje":
              if ceade_d_ticker in latest_data and subyacente_ticker in latest_data:
                  ceade_d_price = latest_data[ceade_d_ticker]["price"]
                  subyacente_price = latest_data[subyacente_ticker]["price"]
                  x_value = (ceade_d_price * row["Ratio de conversión"]) / subyacente_price
                  y_value = latest_data[ceade_ar_ticker]["price"] / ceade_d_price
                  size = latest_data[ceade_d_ticker]["volume"] * ceade_d_price
              else:
                  continue
          else:
              continue

          if not np.isnan(x_value) and not np.isnan(y_value):
              x_values.append(x_value)
              y_values.append(y_value)
              sizes.append(size)
              labels.append(row["CEDEAR ARS"].replace(".BA", ""))
      except Exception as e:
          st.warning(f"Error processing row for ticker {row['CEDEAR ARS']}: {e}")
          continue

  if not x_values or not y_values:
      st.warning("No data available to plot.")
      return

  sizes = np.array(sizes)
  x_avg = np.mean(x_values)
  y_avg = np.mean(y_values)

  fig, ax = plt.subplots(figsize=(10, 6))
  scatter = ax.scatter(x=x_values, y=y_values, s=sizes / 1e6, alpha=0.5)

  # Add average lines for X and Y axes
  ax.axvline(x_avg, color="red", linestyle="--", linewidth=2)
  ax.axhline(y_avg, color="blue", linestyle="--", linewidth=2)

  # Add labels
  for i, label in enumerate(labels):
      ax.text(x_values[i], y_values[i], label, ha='center', va='center')

  # Set labels and title
  if option == 'CCL':
      ax.set_xlabel('USD CCL')
      ax.set_ylabel('Volume in ARS')
  elif option == 'MEP':
      ax.set_xlabel('Price Ratio CEDEAR ARS / CEDEAR D')
      ax.set_ylabel('Volume in USD')
  elif option == 'Canje':
      ax.set_xlabel('Converted Price Ratio')
      ax.set_ylabel('Price Ratio CEDEAR ARS / CEDEAR D')
  else:
      ax.set_xlabel('X Axis')
      ax.set_ylabel('Y Axis')

  ax.set_title(f'Scatter Plot for {option} Option')

  ax.grid(True, which='both', color='lightgray', linestyle='-', linewidth=0.5)
  st.pyplot(fig)

# User selection: CCL, MEP, or Canje
option = st.selectbox("Select the type of operation:", ["CCL", "MEP", "Canje"])

# Add an "Enter" button
if st.button("Enter"):
  # Fetch only the necessary data after "Enter" is pressed
  tickers = get_required_tickers(option, data)
  st.write(f"Fetching data for tickers: {tickers}")
  latest_data = fetch_latest_data(tickers)
  # Display the scatter plot based on the selected option
  create_scatter_plot(option, data, latest_data)
