import streamlit as st
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import folium
from folium.plugins import MarkerCluster
from io import BytesIO
from PIL import Image
from streamlit_folium import folium_static  # Import folium_static

# API Keys
WEATHER_API_KEY = "c636a75a96c74aeced3f5b2e0f056787"
GEOCODE_API_KEY = "2a8c929f9c434f978fda64e8027ea1c2"

# Helper Functions
@st.cache_data
def get_coordinates(api_key, location):
    """Get latitude and longitude for a given location."""
    base_url = "https://api.opencagedata.com/geocode/v1/json"
    complete_url = f"{base_url}?q={location},India&key={api_key}"
    
    response = requests.get(complete_url)
    data = response.json()
    
    if response.status_code == 200 and 'results' in data and len(data['results']) > 0:
        lat = data['results'][0]['geometry']['lat']
        lng = data['results'][0]['geometry']['lng']
        return lat, lng
    else:
        st.error("Error retrieving coordinates. Please check the location.")
        return None, None

@st.cache_data
def get_weather(lat, lng):
    """Get current weather data."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    complete_url = f"{base_url}?lat={lat}&lon={lng}&appid={WEATHER_API_KEY}&units=metric"
    
    response = requests.get(complete_url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error retrieving current weather data.")
        return None

@st.cache_data
def get_forecast(lat, lng):
    """Get 5-day weather forecast."""
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    complete_url = f"{base_url}?lat={lat}&lon={lng}&appid={WEATHER_API_KEY}&units=metric"
    
    response = requests.get(complete_url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error retrieving forecast data.")
        return None

def display_weather(weather_data):
    """Display current weather data."""
    st.subheader("Current Weather")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Temperature:** {weather_data['main']['temp']}°C")
        st.write(f"**Feels Like:** {weather_data['main']['feels_like']}°C")
        st.write(f"**Description:** {weather_data['weather'][0]['description'].capitalize()}")
    with col2:
        st.write(f"**Humidity:** {weather_data['main']['humidity']}%")
        st.write(f"**Pressure:** {weather_data['main']['pressure']} hPa")
        st.write(f"**Wind Speed:** {weather_data['wind']['speed'] * 3.6:.2f} km/h")
        st.write(f"**Sunrise:** {datetime.fromtimestamp(weather_data['sys']['sunrise']).strftime('%H:%M:%S')}")
        st.write(f"**Sunset:** {datetime.fromtimestamp(weather_data['sys']['sunset']).strftime('%H:%M:%S')}")

def display_forecast(forecast_data):
    """Display 5-day weather forecast."""
    st.subheader("5-Day Weather Forecast")
    forecast_list = forecast_data['list']
    daily_data = forecast_list[::8]  # Data every 3 hours; pick one for each day

    for entry in daily_data:
        date = datetime.fromtimestamp(entry['dt']).strftime('%Y-%m-%d')
        temp = entry['main']['temp']
        description = entry['weather'][0]['description']
        st.write(f"**{date}:** {temp}°C, {description.capitalize()}")

def display_weather_trends(forecast_data):
    """Generate a line plot for multiple weather trends (temp, humidity, wind speed)."""
    dates = [datetime.fromtimestamp(entry['dt']).strftime('%Y-%m-%d %H:%M:%S') for entry in forecast_data['list']]
    temps = [entry['main']['temp'] for entry in forecast_data['list']]
    humidities = [entry['main']['humidity'] for entry in forecast_data['list']]
    wind_speeds = [entry['wind']['speed'] for entry in forecast_data['list']]

    fig, axs = plt.subplots(3, figsize=(10, 12))

    # Temperature plot
    axs[0].plot(dates, temps, marker='o', linestyle='-', color='b')
    axs[0].set_title("Temperature Trend (5-Day Forecast)")
    axs[0].set_xlabel("Date and Time")
    axs[0].set_ylabel("Temperature (°C)")
    axs[0].tick_params(axis='x', rotation=45)

    # Humidity plot
    axs[1].plot(dates, humidities, marker='o', linestyle='-', color='g')
    axs[1].set_title("Humidity Trend (5-Day Forecast)")
    axs[1].set_xlabel("Date and Time")
    axs[1].set_ylabel("Humidity (%)")
    axs[1].tick_params(axis='x', rotation=45)

    # Wind Speed plot
    axs[2].plot(dates, wind_speeds, marker='o', linestyle='-', color='r')
    axs[2].set_title("Wind Speed Trend (5-Day Forecast)")
    axs[2].set_xlabel("Date and Time")
    axs[2].set_ylabel("Wind Speed (m/s)")
    axs[2].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    st.pyplot(fig)

def display_map(lat, lng, weather_data):
    """Display a map with a weather icon at the location."""
    map_center = [lat, lng]
    m = folium.Map(location=map_center, zoom_start=10, tiles='cartodb dark_matter')  # Changed map style to 'cartodb dark_matter'
    
    weather_icon_url = f"http://openweathermap.org/img/wn/{weather_data['weather'][0]['icon']}@2x.png"
    weather_icon = folium.CustomIcon(weather_icon_url, icon_size=(40, 40))
    
    # Custom popup HTML to display location name above icon
    popup_html = f"""
    <h4>{weather_data['name']}</h4>
    <img src="{weather_icon_url}" width="40" height="40"/>
    """
    
    folium.Marker(location=map_center, popup=folium.Popup(popup_html, max_width=200), icon=weather_icon).add_to(m)
    
    # Display map in Streamlit
    st.subheader("Location on Map")
    folium_static(m)

# Main App
def main():
    st.title("Weather Dashboard")
    st.caption("Get real-time weather updates and forecasts for any location in India.")

    location = st.text_input("Enter a location in India:")
    
    if location:
        lat, lng = get_coordinates(GEOCODE_API_KEY, location)
        if lat and lng:
            with st.spinner("Fetching weather data..."):
                weather_data = get_weather(lat, lng)
                if weather_data:
                    display_weather(weather_data)
                    display_map(lat, lng, weather_data)
            
            with st.spinner("Fetching forecast data..."):
                forecast_data = get_forecast(lat, lng)
                if forecast_data:
                    display_forecast(forecast_data)
                    display_weather_trends(forecast_data)

if __name__ == "__main__":
    main()
