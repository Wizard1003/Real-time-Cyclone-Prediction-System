import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import json

# Page configuration
st.set_page_config(
    page_title="Cyclone Prediction System",
    page_icon="🌀",
    layout="wide"
)

# API Configuration - Tomorrow.io
WEATHER_API_KEY = "Odlt6jwCcqQEv14dRuqJOQEGROygzaXp"
WEATHER_API_BASE = "https://api.tomorrow.io/v4"

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 2rem;
    }
    .warning-box {
        background-color: #ff6b6b;
        padding: 15px;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        margin: 10px 0;
    }
    .safe-box {
        background-color: #51cf66;
        padding: 15px;
        border-radius: 10px;
        color: black;
        font-weight: bold;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Function to fetch weather data from Tomorrow.io
@st.cache_data(ttl=600)
def fetch_weather_data(location):
    try:
        # Tomorrow.io Realtime API
        realtime_url = f"{WEATHER_API_BASE}/weather/realtime"
        
        # Tomorrow.io Forecast API
        forecast_url = f"{WEATHER_API_BASE}/weather/forecast"
        
        params = {
            "location": location,
            "apikey": WEATHER_API_KEY,
            "units": "metric"
        }
        
        # Fetch realtime data
        realtime_response = requests.get(realtime_url, params=params)
        realtime_data = realtime_response.json()
        
        # Fetch forecast data
        forecast_params = params.copy()
        forecast_params["timesteps"] = "1d"
        forecast_response = requests.get(forecast_url, params=forecast_params)
        forecast_data = forecast_response.json()
        
        return realtime_data, forecast_data
    except Exception as e:
        st.error(f"Error fetching weather data: {str(e)}")
        return None, None

# Function to calculate cyclone risk score
def calculate_cyclone_risk(weather_data):
    if not weather_data or 'data' not in weather_data:
        return 0, "Unknown"
    
    try:
        values = weather_data['data']['values']
        
        # Risk factors from Tomorrow.io data
        wind_speed = values.get('windSpeed', 0) * 3.6  # Convert m/s to km/h
        pressure = values.get('pressureSurfaceLevel', 1013)
        humidity = values.get('humidity', 0)
        temp = values.get('temperature', 25)
        cloud_cover = values.get('cloudCover', 0)
        
        # Cyclone risk calculation
        risk_score = 0
        
        # Wind speed factor (tropical cyclone: >63 km/h)
        if wind_speed > 118:
            risk_score += 40
        elif wind_speed > 88:
            risk_score += 30
        elif wind_speed > 63:
            risk_score += 20
        elif wind_speed > 40:
            risk_score += 10
        
        # Pressure factor (low pressure indicates cyclone)
        if pressure < 980:
            risk_score += 30
        elif pressure < 1000:
            risk_score += 20
        elif pressure < 1010:
            risk_score += 10
        
        # Humidity factor
        if humidity > 85:
            risk_score += 15
        elif humidity > 75:
            risk_score += 10
        
        # Temperature factor (tropical cyclones form in warm waters)
        if 26 <= temp <= 32:
            risk_score += 10
        
        # Cloud cover
        if cloud_cover > 80:
            risk_score += 5
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "EXTREME"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MODERATE"
        elif risk_score >= 15:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        return risk_score, risk_level
    except Exception as e:
        st.error(f"Error calculating risk: {str(e)}")
        return 0, "Unknown"

# Main app
def main():
    st.markdown('<h1 class="main-header">🌀 Real-Time Cyclone Prediction System</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("🌍 Location Settings")
    st.sidebar.info("💡 Enter coordinates (lat,lon) or city name")
    
    location_input = st.sidebar.text_input(
        "Enter Location", 
        value="19.0760,72.8777",
        help="Format: latitude,longitude (e.g., 19.0760,72.8777 for Mumbai) or city name"
    )
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Risk Levels:**
    - 🟢 MINIMAL: 0-14
    - 🟡 LOW: 15-29
    - 🟠 MODERATE: 30-49
    - 🔴 HIGH: 50-69
    - ⚫ EXTREME: 70+
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.caption("""
    **Popular Indian Coastal Cities:**
    - Mumbai: 19.0760,72.8777
    - Chennai: 13.0827,80.2707
    - Kolkata: 22.5726,88.3639
    - Visakhapatnam: 17.6868,83.2185
    - Bhubaneswar: 20.2961,85.8245
    """)
    
    # Fetch data
    with st.spinner("Fetching weather data from Tomorrow.io..."):
        current_data, forecast_data = fetch_weather_data(location_input)
    
    if not current_data or 'data' not in current_data:
        error_msg = "❌ Unable to fetch weather data."
        if current_data and 'message' in current_data:
            error_msg += f"\n\nAPI Error: {current_data.get('message', 'Unknown error')}"
        st.error(error_msg)
        st.info("💡 **Tip:** Use coordinates format like '19.0760,72.8777' or try a different location.")
        return
    
    # Calculate risk
    risk_score, risk_level = calculate_cyclone_risk(current_data)
    
    # Display risk alert
    if risk_level in ["EXTREME", "HIGH"]:
        st.markdown(f'<div class="warning-box">⚠️ CYCLONE RISK: {risk_level} (Score: {risk_score}/100)</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="safe-box">✅ CYCLONE RISK: {risk_level} (Score: {risk_score}/100)</div>', unsafe_allow_html=True)
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        values = current_data['data']['values']
        
        temp = values.get('temperature', 0)
        wind_speed = values.get('windSpeed', 0) * 3.6  # m/s to km/h
        wind_gust = values.get('windGust', 0) * 3.6
        pressure = values.get('pressureSurfaceLevel', 0)
        humidity = values.get('humidity', 0)
        cloud_cover = values.get('cloudCover', 0)
        visibility = values.get('visibility', 0)
        precip = values.get('precipitationIntensity', 0)
        
        with col1:
            st.metric("🌡️ Temperature", f"{temp:.1f}°C", 
                     f"Feels like {values.get('temperatureApparent', temp):.1f}°C")
        with col2:
            st.metric("💨 Wind Speed", f"{wind_speed:.1f} km/h", 
                     f"Gusts: {wind_gust:.1f} km/h")
        with col3:
            st.metric("🌊 Pressure", f"{pressure:.0f} mb", 
                     f"{'⬇️ Low' if pressure < 1000 else '➡️ Normal' if pressure < 1013 else '⬆️ High'}")
        with col4:
            st.metric("💧 Humidity", f"{humidity:.0f}%", 
                     f"Cloud: {cloud_cover:.0f}%")
        
        # Two column layout
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📊 Risk Factor Analysis")
            
            # Risk gauge chart
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=risk_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Cyclone Risk Score"},
                delta={'reference': 30},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 15], 'color': "lightgreen"},
                        {'range': [15, 30], 'color': "yellow"},
                        {'range': [30, 50], 'color': "orange"},
                        {'range': [50, 70], 'color': "red"},
                        {'range': [70, 100], 'color': "darkred"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': 70
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            # Risk factors breakdown
            risk_factors = {
                "Wind Speed": min((wind_speed / 118) * 100, 100) if wind_speed > 0 else 0,
                "Low Pressure": max(100 - ((pressure - 900) / 1.13), 0) if pressure > 0 else 0,
                "High Humidity": humidity,
                "Cloud Cover": cloud_cover,
                "Temperature": 100 if 26 <= temp <= 32 else 50
            }
            
            fig_factors = go.Figure(data=[
                go.Bar(x=list(risk_factors.values()), y=list(risk_factors.keys()), orientation='h',
                      marker=dict(color=list(risk_factors.values()), colorscale='Reds'))
            ])
            fig_factors.update_layout(
                title="Risk Contributing Factors (%)",
                xaxis_title="Contribution",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_factors, use_container_width=True)
        
        with col_right:
            st.subheader("🎯 Current Conditions")
            st.write(f"**Location:** {location_input}")
            st.write(f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Weather Code:** {values.get('weatherCode', 'N/A')}")
            st.write(f"**Wind Direction:** {values.get('windDirection', 0):.0f}°")
            st.write(f"**Precipitation:** {precip:.2f} mm/h")
            st.write(f"**Visibility:** {visibility:.1f} km")
            st.write(f"**UV Index:** {values.get('uvIndex', 0)}")
            st.write(f"**Dew Point:** {values.get('dewPoint', 0):.1f}°C")
            
            st.markdown("---")
            st.subheader("⚠️ Safety Recommendations")
            
            if risk_level in ["EXTREME", "HIGH"]:
                st.warning("""
                - 🏠 Stay indoors and secure all outdoor items
                - 📻 Monitor weather updates continuously
                - 🚫 Avoid coastal areas and low-lying regions
                - 🎒 Keep emergency supplies ready
                - 🚗 Avoid unnecessary travel
                """)
            elif risk_level == "MODERATE":
                st.info("""
                - 👀 Monitor weather conditions
                - 📦 Prepare emergency supplies
                - 📱 Stay informed via weather alerts
                - 🏠 Secure loose outdoor items
                """)
            else:
                st.success("""
                - ✅ Conditions are currently favorable
                - 📊 Continue monitoring updates
                - 🌤️ Normal activities can continue
                """)
        
        # Forecast section
        st.markdown("---")
        st.subheader("📅 Weather Forecast & Risk Trend")
        
        if forecast_data and 'timelines' in forecast_data:
            try:
                daily_data = forecast_data['timelines']['daily']
                
                dates = []
                temps_max = []
                temps_min = []
                wind_speeds = []
                humidity_vals = []
                daily_risks = []
                
                for day in daily_data[:7]:  # Get 7 days
                    day_values = day['values']
                    dates.append(day['time'][:10])
                    
                    temp_max = day_values.get('temperatureMax', 0)
                    temp_min = day_values.get('temperatureMin', 0)
                    wind = day_values.get('windSpeedAvg', 0) * 3.6
                    humid = day_values.get('humidityAvg', 0)
                    
                    temps_max.append(temp_max)
                    temps_min.append(temp_min)
                    wind_speeds.append(wind)
                    humidity_vals.append(humid)
                    
                    # Calculate daily risk
                    daily_risk = 0
                    if wind > 63:
                        daily_risk += 30
                    if humid > 80:
                        daily_risk += 20
                    if day_values.get('precipitationIntensityAvg', 0) > 5:
                        daily_risk += 15
                    daily_risks.append(daily_risk)
                
                # Create forecast charts
                fig_forecast = go.Figure()
                
                fig_forecast.add_trace(go.Scatter(
                    x=dates, y=temps_max, name='Max Temp (°C)',
                    mode='lines+markers', line=dict(color='red')
                ))
                fig_forecast.add_trace(go.Scatter(
                    x=dates, y=temps_min, name='Min Temp (°C)',
                    mode='lines+markers', line=dict(color='blue')
                ))
                fig_forecast.add_trace(go.Scatter(
                    x=dates, y=wind_speeds, name='Wind Speed (km/h)',
                    mode='lines+markers', line=dict(color='green'), yaxis='y2'
                ))
                fig_forecast.add_trace(go.Scatter(
                    x=dates, y=daily_risks, name='Risk Score',
                    mode='lines+markers', line=dict(color='purple', width=3), yaxis='y2'
                ))
                
                fig_forecast.update_layout(
                    title='Weather Forecast & Risk Trend',
                    xaxis_title='Date',
                    yaxis_title='Temperature (°C)',
                    yaxis2=dict(title='Wind Speed (km/h) / Risk Score', overlaying='y', side='right'),
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_forecast, use_container_width=True)
                
                # Forecast table
                forecast_df = pd.DataFrame({
                    'Date': dates,
                    'Max Temp (°C)': [f"{t:.1f}" for t in temps_max],
                    'Min Temp (°C)': [f"{t:.1f}" for t in temps_min],
                    'Wind (km/h)': [f"{w:.1f}" for w in wind_speeds],
                    'Humidity (%)': [f"{h:.0f}" for h in humidity_vals],
                    'Risk Score': daily_risks
                })
                st.dataframe(forecast_df, use_container_width=True)
            except Exception as e:
                st.warning(f"Forecast data unavailable: {str(e)}")
        
    except Exception as e:
        st.error(f"Error displaying weather data: {str(e)}")
        st.json(current_data)
    
    # Footer
    st.markdown("---")
    st.caption(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data Source: Tomorrow.io")

if __name__ == "__main__":
    main()