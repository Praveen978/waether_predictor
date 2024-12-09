import streamlit as st
import requests
from datetime import datetime

st.image("76818-forecasting-material-rain-shower-weather-icon.png",width=400)

# API Keys
WEATHER_API_KEY = "c636a75a96c74aeced3f5b2e0f056787"
GEOCODE_API_KEY = "2a8c929f9c434f978fda64e8027ea1c2"

# Helper Functions
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

# Display Functions
def display_weather(weather_data):
    """Display current weather data."""
    st.subheader("Current Weather")
    st.write(f"**Temperature:** {weather_data['main']['temp']}°C")
    st.write(f"**Feels Like:** {weather_data['main']['feels_like']}°C")
    st.write(f"**Description:** {weather_data['weather'][0]['description'].capitalize()}")
    st.write(f"**Humidity:** {weather_data['main']['humidity']}%")
    st.write(f"**Pressure:** {weather_data['main']['pressure']} hPa")
    st.write(f"**Wind Speed:** {weather_data['wind']['speed'] * 3.6:.2f} km/h")
    st.write(f"**Sunrise:** {datetime.fromtimestamp(weather_data['sys']['sunrise']).strftime('%H:%M:%S')}")
    st.write(f"**Sunset:** {datetime.fromtimestamp(weather_data['sys']['sunset']).strftime('%H:%M:%S')}")

def display_forecast(forecast_data):
    """Display 5-day weather forecast."""
    st.subheader("5-Day Weather Forecast")
    forecast_list = forecast_data['list']
    for entry in forecast_list[::8]:  # Data every 3 hours; pick one for each day
        date = datetime.fromtimestamp(entry['dt']).strftime('%Y-%m-%d')
        temp = entry['main']['temp']
        description = entry['weather'][0]['description']
        st.write(f"**{date}:** {temp}°C, {description.capitalize()}")

# Main App
def main():
    st.title("Weather Predictor")
    st.caption("Get real-time weather updates and 5-day forecasts for any location in India.")
    
    location = st.text_input("Enter a location in India:")
    
    if location:
        lat, lng = get_coordinates(GEOCODE_API_KEY, location)
        if lat and lng:
            with st.spinner("Fetching weather data..."):
                weather_data = get_weather(lat, lng)
                if weather_data:
                    display_weather(weather_data)
            
            with st.spinner("Fetching forecast data..."):
                forecast_data = get_forecast(lat, lng)
                if forecast_data:
                    display_forecast(forecast_data)

if __name__ == "__main__":
    main()
