import streamlit as st
import sqlite3
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
SENDER_EMAIL = os.getenv("EMAIL")  # Sender email from .env
SENDER_PASSWORD = os.getenv("PASSWORD")  # App password from .env
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # OpenWeatherMap API Key
GEOCODE_API_KEY = os.getenv("GEOCODE_API_KEY")  # OpenCage Geocoding API Key

# Database setup
def create_database():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS userdetails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            location TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_user(name, email, location):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO userdetails (name, email, location) VALUES (?, ?, ?)", (name, email, location))
        conn.commit()
        conn.close()
        st.success("User registered successfully!")
    except sqlite3.IntegrityError:
        st.error("This email is already registered.")

def retrieve_user(email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userdetails WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

# Function to get coordinates for a location
def get_coordinates(api_key, location):
    base_url = "https://api.opencagedata.com/geocode/v1/json"
    complete_url = f"{base_url}?q={location},India&key={api_key}"
    response = requests.get(complete_url)
    data = response.json()
    if response.status_code == 200 and data['results']:
        lat = data['results'][0]['geometry']['lat']
        lng = data['results'][0]['geometry']['lng']
        return lat, lng
    else:
        st.error("Error retrieving coordinates. Please try again.")
        return None

# Function to fetch current weather data
def get_weather(api_key, lat, lng):
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}lat={lat}&lon={lng}&appid={api_key}&units=metric"
    response = requests.get(complete_url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error retrieving weather data. Please try again.")
        return None

# Function to fetch 5-day weather forecast
def get_weather_forecast(api_key, lat, lng):
    base_url = "http://api.openweathermap.org/data/2.5/forecast?"
    complete_url = f"{base_url}lat={lat}&lon={lng}&appid={api_key}&units=metric"
    response = requests.get(complete_url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error retrieving 5-day forecast. Please try again.")
        return None

# Function to display 5-day weather forecast
def display_weather_forecast(forecast_data):
    st.subheader("5-Day Weather Forecast")
    for forecast in forecast_data['list'][:40:8]:  # Fetch one forecast per day
        dt = datetime.fromtimestamp(forecast['dt']).strftime("%Y-%m-%d %H:%M:%S")
        temp = forecast['main']['temp']
        description = forecast['weather'][0]['description']
        icon_url = f"http://openweathermap.org/img/wn/{forecast['weather'][0]['icon']}.png"
        
        st.write(f"### {dt}")
        st.image(icon_url, width=50)
        st.write(f"Temperature: {temp}°C")
        st.write(f"Description: {description.capitalize()}")

# Function to provide weather-related health tips
def should_send_email_based_on_conditions(weather_data):
    """Check if the weather conditions meet the criteria to send an email."""
    weather_condition = weather_data['weather'][0]['description'].lower()
    temperature = weather_data['main']['temp']

    if 'rain' in weather_condition:
        return "It's raining! Wear waterproof clothing, carry an umbrella, and avoid slippery areas.", True
    elif 'cloud' in weather_condition:
        return "It's cloudy! It might rain later, so carry an umbrella just in case.", True
    elif temperature > 35:
        return "It's very hot! Stay indoors, drink plenty of water, and avoid strenuous activities during peak hours.", True
    else:
        return "The weather is fine. No alerts to send via email.", False


# Function to send an email with weather tips
def send_weather_tip(email, tips, location):
    try:
        subject = f"Weather Tips for {location}"

        message = MIMEMultipart()
        message['From'] = SENDER_EMAIL
        message['To'] = email
        message['Subject'] = subject
        message_body = f"Hello,\n\nHere are your instant weather tips for {location}:\n\n{tips}\n\nStay safe!\nSkySnap Team"
        message.attach(MIMEText(message_body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)

        st.success("Weather tip sent to your email!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

# Improved UI and navigation
def show_sidebar():
    st.sidebar.title("Navigation")
    menu = ["Home", "Weather", "User Profile"]
    choice = st.sidebar.selectbox("Select Option", menu)
    return choice

def show_home():
    st.title("Welcome to SkySnap!")
    st.write("SkySnap is your personal weather assistant.")
    st.image("76818-forecasting-material-rain-shower-weather-icon.png", use_column_width=True)
    st.subheader("Features")
    st.write("1. Get instant weather updates and tips.")
    st.write("2. Save weather data for future reference.")
    st.write("3. Personalized notifications and advice based on your location.")
    st.write("4. 5-day weather forecasts for better planning.")

def show_weather(user=None):
    st.title("Weather Information")
    
    weather_location = st.text_input("Enter a location in India to check weather:")

    if weather_location:
        coords = get_coordinates(GEOCODE_API_KEY, weather_location)
        if coords:
            lat, lng = coords
            weather_data = get_weather(WEATHER_API_KEY, lat, lng)
            if weather_data:
                st.write(f"### Current Weather in {weather_location}")
                st.write(f"Temperature: {weather_data['main']['temp']}°C")
                st.write(f"Feels Like: {weather_data['main']['feels_like']}°C")
                st.write(f"Description: {weather_data['weather'][0]['description']}")
                st.image(f"http://openweathermap.org/img/wn/{weather_data['weather'][0]['icon']}.png", width=100)

                tips, send_email = should_send_email_based_on_conditions(weather_data)
                st.write(f"### Instant Tip: {tips}")
                
                if user and send_email:
                    if st.button("Send Weather Alert to Your Email"):
                        send_weather_tip(user[2], tips, weather_location)
                elif not send_email:
                    st.write("No significant weather alert to send via email.")
                else:
                    st.write("Please log in to receive weather updates via email.")

                # Fetch and display 5-day forecast
                forecast_data = get_weather_forecast(WEATHER_API_KEY, lat, lng)
                if forecast_data:
                    display_weather_forecast(forecast_data)

def show_user_profile(user):
    st.title("User Profile")
    st.write(f"Name: {user[1]}")
    st.write(f"Email: {user[2]}")
    st.write(f"Location: {user[3]}")
    if st.button("Update Location"):
        new_location = st.text_input("Enter new location:")
        if new_location:
            update_user_location(user[0], new_location)
            st.success(f"Location updated to {new_location}.")
            send_weather_tip(user[2], f"Your location has been updated to {new_location}.", new_location)

# Register New User
def register_new_user():
    st.subheader("New User Registration")
    name = st.text_input("Enter your name")
    email = st.text_input("Enter your email")
    location = st.text_input("Enter your location")

    if st.button("Create Profile"):
        if name and email and location:
            insert_user(name, email, location)
        else:
            st.error("All fields are required to create a profile.")

# Main Application Flow
def main():
    create_database()

    choice = show_sidebar()

    user = None

    user_status = st.sidebar.radio("Are you an existing user?", ["Yes", "No"])

    if user_status == "Yes":
        login_email = st.sidebar.text_input("Enter your email to login:")
        if login_email:
            user = retrieve_user(login_email)
            if user:
                st.subheader(f"Welcome, {user[1]}!")
                st.write(f"Email: {user[2]}")
                st.write(f"Location: {user[3]}")
            else:
                st.error("No user found with this email. Please register.")
    elif user_status == "No":
        register_new_user()

    if choice == "Home":
        show_home()
    elif choice == "Weather":
        show_weather(user)
    elif choice == "User Profile":
        if user:
            show_user_profile(user)
        else:
            st.error("Please log in to view your profile.")

if __name__ == "__main__":
    main()

import schedule
import time

# Function to automate email sending
def automated_weather_email():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userdetails")
    users = cursor.fetchall()
    conn.close()

    for user in users:
        user_id, name, email, location = user
        coords = get_coordinates(GEOCODE_API_KEY, location)
        if coords:
            lat, lng = coords
            weather_data = get_weather(WEATHER_API_KEY, lat, lng)
            if weather_data:
                tips, should_send = should_send_email_based_on_conditions(weather_data)
                if should_send:
                    send_weather_tip(email, tips, location)

# Schedule the task to run every day at a specific time
schedule.every().day.at("01:25").do(automated_weather_email)

# Run the scheduler
if __name__ == "__main__":
    create_database()
    while True:
        schedule.run_pending()
        time.sleep(1)
