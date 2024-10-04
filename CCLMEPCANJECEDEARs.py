import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px

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
def create_scatter_plot(option, data, latest_data, log_scale, exclude_outliers):
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

  # Convert to numpy arrays for processing
  x_values = np.array(x_values)
  y_values = np.array(y_values)
  sizes = np.array(sizes)

  # Exclude outliers if selected
  if exclude_outliers:
      q1 = np.percentile(y_values, 25)
      q3 = np.percentile(y_values, 75)
      iqr = q3 - q1
      lower_bound = q1 - 1.5 * iqr
      upper_bound = q3 + 1.5 * iqr
      mask = (y_values >= lower_bound) & (y_values <= upper_bound)
      x_values = x_values[mask]
      y_values = y_values[mask]
      sizes = sizes[mask]
      labels = [labels[i] for i in range(len(labels)) if mask[i]]

  # Create the scatter plot using Plotly
  fig = px.scatter(
      x=x_values,
      y=y_values,
      size=sizes / 1e6,  # Scale sizes for better visibility
      hover_name=labels,
      labels={'x': 'X Axis', 'y': 'Y Axis'},
      title=f'Scatter Plot for {option} Option'
  )

  # Set logarithmic scale if selected
  if log_scale:
      fig.update_xaxes(type="log")
      fig.update_yaxes(type="log")

  # Show the plot in Streamlit
  st.plotly_chart(fig)

# User selection: CCL, MEP, or Canje
option = st.selectbox("Select the type of operation:", ["CCL", "MEP", "Canje"])

# Add options for logarithmic scale and outlier exclusion
log_scale = st.checkbox("Use logarithmic scale for axes")
exclude_outliers = st.checkbox("Exclude outliers")

# Add an "Enter" button
if st.button("Enter"):
  # Fetch only the necessary data after "Enter" is pressed
  tickers = get_required_tickers(option, data)
  st.write(f"Fetching data for tickers: {tickers}")
  latest_data = fetch_latest_data(tickers)
  # Display the scatter plot based on the selected option
  create_scatter_plot(option, data, latest_data, log_scale, exclude_outliers)
