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

# Add options for font sizes
axis_font_size = st.slider("Select font size for axis labels:", 10, 30, 14)
hover_font_size = st.slider("Select font size for hover text:", 10, 30, 12)

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

        # Create the scatter plot using Plotly
        fig = px.scatter(x=x_values, y=y_values, size=sizes, text=labels,
                         labels={'x': 'USD CCL' if option == "CCL" else 'X Axis',
                                 'y': 'Volumen en pesos' if option == "CCL" else 'Y Axis'},
                         title=f'Scatter plot for {option} option',
                         size_max=50, log_y=True,
                         color=np.arange(len(x_values)),  # Use index for color to distinguish bubbles
                         color_continuous_scale='Viridis')

        # Add average lines for X and Y axes
        fig.add_shape(type="line", x0=x_avg, x1=x_avg, y0=min(y_values), y1=max(y_values),
                      line=dict(color="Red", width=2, dash="dash"))
        fig.add_shape(type="line", x0=min(x_values), x1=max(x_values), y0=y_avg, y1=y_avg,
                      line=dict(color="Blue", width=2, dash="dash"))

        # Ensure the ticker labels are inside the bubbles
        fig.update_traces(textposition='middle center', marker=dict(sizemode='diameter', opacity=0.8))

        # Add grid lines for both axes
        fig.update_xaxes(showgrid=True, gridcolor='LightGray', gridwidth=1, tickfont=dict(size=axis_font_size))
        fig.update_yaxes(showgrid=True, gridcolor='LightGray', gridwidth=1, tickfont=dict(size=axis_font_size))

        # Adjust hover text font size
        fig.update_traces(marker=dict(sizemode='diameter', opacity=0.8),
                          selector=dict(mode='markers+text'))
        fig.update_traces(hovertemplate="<b>%{text}</b><br>Price: %{x}<br>Volume: %{y}<br>Size: %{marker.size}",
                          hoverlabel=dict(font_size=hover_font_size))

        # Add sliders for adjusting percentiles and axes
        st.plotly_chart(fig, use_container_width=True)

    # Display the scatter plot based on the selected option
    create_scatter_plot(option)
