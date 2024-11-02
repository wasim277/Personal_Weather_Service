import boto3
import json
import requests
import smtplib
from datetime import datetime, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit as st
import pytz

# Credentials and API keys defined directly in the script
OPENWEATHER_API_KEY = 'a960b5a01fa7e717a1b753937cdb5857'

# AWS Credentials
AWS_ACCESS_KEY = 'AKIASVQKH7PPWD6DWN7T'
AWS_SECRET_ACCESS_KEY = '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'

# Email Credentials
GMAIL_EMAIL = 'awsproject277@gmail.com'
GMAIL_APP_PASSWORD = 'zoxv epbg ojpm zliq'  # Use app password

# Base URL for the OpenWeatherMap API
BASE_URL = 'http://api.openweathermap.org/data/2.5/forecast'

# Function to fetch 3-day weather forecast
def fetch_three_day_weather(city):
    url = f"{BASE_URL}?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        forecast_list = data['list']

        weather_report = f"3-Day Weather Forecast for {city} (Including Today):\n\n"
        current_date = datetime.now().date()
        day_count = 0
        added_dates = set()
        today_included = False

        for forecast in forecast_list:
            dt_txt = forecast['dt_txt']
            date_time = datetime.strptime(dt_txt, '%Y-%m-%d %H:%M:%S')
            forecast_date = date_time.date()

            if not today_included and forecast_date == current_date:
                today_included = True
                temperature = forecast['main']['temp']
                weather_description = forecast['weather'][0]['description']

                weather_report += f"Date: {date_time.strftime('%Y-%m-%d')} (Today)\n"
                weather_report += f"Temperature: {temperature}°C\n"
                weather_report += f"Weather: {weather_description}\n"
                weather_report += "-" * 30 + "\n"

                added_dates.add(forecast_date)
                day_count += 1
                continue

            if forecast_date not in added_dates and forecast_date > current_date and date_time.hour == 12:
                temperature = forecast['main']['temp']
                weather_description = forecast['weather'][0]['description']

                weather_report += f"Date: {date_time.strftime('%Y-%m-%d')}\n"
                weather_report += f"Temperature: {temperature}°C\n"
                weather_report += f"Weather: {weather_description}\n"
                weather_report += "-" * 30 + "\n"

                added_dates.add(forecast_date)
                day_count += 1

            if day_count >= 3:
                break

        return weather_report
    else:
        return f"Error fetching data for {city}: {response.status_code}"

# Function to send email
def send_email_with_gmail(subject, body, recipient_email):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_EMAIL, recipient_email, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {recipient_email}.")
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")

# Function to save user data to S3
def save_to_s3(city, unit, email, end_date, time_zone, update_time):
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name='us-east-1'  # Example: 'us-west-1'
    )
    
    bucket_name = 'weatherreporting'
    file_key = 'subscriptions.json'

    # Load existing data from S3, if it exists
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        existing_data = json.loads(obj['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        existing_data = []

    # Check for existing subscription
    for subscription in existing_data:
        if subscription['email'] == email and subscription['city'] == city:
            return False  # Indicates already registered

    # Append new subscription data
    subscription_data = {
        'email': email,
        'city': city,
        'unit': unit,
        'end_date': str(end_date),
        'time_zone': time_zone,
        'update_time': str(update_time),
        'subscription_date': str(datetime.now())
    }
    existing_data.append(subscription_data)

    # Save updated data back to S3
    s3.put_object(
        Bucket=bucket_name,
        Key=file_key,
        Body=json.dumps(existing_data)
    )
    return True  # Indicates subscription saved successfully

# Function to unsubscribe user from S3
def unsubscribe_from_s3(city, email):
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name='us-east-1'
    )
    
    bucket_name = 'weatherreporting'
    file_key = 'subscriptions.json'

    # Load existing data from S3
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        existing_data = json.loads(obj['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        return False  # No subscriptions found

    # Filter out the subscription to unsubscribe
    updated_data = [sub for sub in existing_data if not (sub['city'] == city and sub['email'] == email)]

    if len(updated_data) == len(existing_data):
        return False  # No subscription found to unsubscribe

    # Save updated data back to S3
    s3.put_object(
        Bucket=bucket_name,
        Key=file_key,
        Body=json.dumps(updated_data)
    )
    return True  # Indicates unsubscription successful

# Streamlit app logic
st.title("Daily Weather Updates Subscription")

# Create tabs for subscription and unsubscription
tab1, tab2 = st.tabs(["Subscribe", "Unsubscribe"])

# Subscription tab
with tab1:
    city = st.selectbox("Select Your City", [
        "New York", "London", "Tokyo", "Delhi", "Sydney", "Paris", "Los Angeles",
        "Beijing", "Singapore", "Dubai", "Berlin", "Rome", "Toronto", "Shanghai",
        "Moscow", "Mumbai", "Istanbul", "Chicago", "Hong Kong", "Bangkok",
        "San Francisco", "Madrid", "Sao Paulo", "Seoul", "Mexico City",
        "Buenos Aires", "Cape Town", "Kuala Lumpur", "Jakarta", "Cairo",
        "Lisbon", "Melbourne", "Vienna", "Zurich", "Stockholm", "Barcelona",
        "Amsterdam", "Vancouver", "Rio de Janeiro", "Montreal", "Warsaw",
        "Prague", "Budapest", "Athens", "Brussels", "Copenhagen", "Dublin"
    ])
    unit = st.radio("Choose Temperature Unit", ('Celsius', 'Fahrenheit'))
    email = st.text_input("Enter Your Email")
    end_date = st.date_input("Subscription End Date")
    
    # Time selection for updates
    update_time = st.time_input("Select Time for Updates", value=time(9, 0))
    
    # Time zone selection
    time_zones = pytz.all_timezones
    time_zone = st.selectbox("Select Time Zone", time_zones)

    if st.button("Subscribe"):
        subscription_saved = save_to_s3(city, unit, email, end_date, time_zone, update_time)
        
        if subscription_saved:
            st.success("Subscription successful! You'll receive daily updates.")
            
            # Send initial confirmation email
            send_email_with_gmail(
                subject="Weather Update Subscription Confirmation",
                body=f"Hello,\n\nYou have successfully subscribed to weather updates for {city}.\n\nYou will receive updates at {update_time.strftime('%H:%M')} {time_zone}.\n\nThank you!",
                recipient_email=email
            )
        else:
            st.warning("You are already registered for weather updates in this city.")

# Unsubscription tab
with tab2:
    unsubscribe_city = st.selectbox("Select Your City to Unsubscribe", [
        "New York", "London", "Tokyo", "Delhi", "Sydney", "Paris", "Los Angeles",
        "Beijing", "Singapore", "Dubai", "Berlin", "Rome", "Toronto", "Shanghai",
        "Moscow", "Mumbai", "Istanbul", "Chicago", "Hong Kong", "Bangkok",
        "San Francisco", "Madrid", "Sao Paulo", "Seoul", "Mexico City", "Buenos Aires", "Cape Town", "Kuala Lumpur",
        "Jakarta", "Cairo", "Lisbon", "Melbourne", "Vienna", "Zurich", 
        "Stockholm", "Barcelona", "Amsterdam", "Vancouver", "Rio de Janeiro", 
        "Montreal", "Warsaw", "Prague", "Budapest", "Athens", "Brussels", 
        "Copenhagen", "Dublin"
    ])
    
    unsubscribe_email = st.text_input("Enter Your Email to Unsubscribe")

    if st.button("Unsubscribe"):
        unsubscription_successful = unsubscribe_from_s3(unsubscribe_city, unsubscribe_email)

        if unsubscription_successful:
            st.success("You have been unsubscribed successfully.")
            # Send unsubscription confirmation email
            send_email_with_gmail(
                subject="Weather Update Unsubscription Confirmation",
                body=f"Hello,\n\nYou have successfully unsubscribed from weather updates for {unsubscribe_city}.\n\nThank you!",
                recipient_email=unsubscribe_email
            )
        else:
            st.warning("No subscription found for this email in the selected city.")

# Schedule for sending weather updates (this part would typically be run as a separate job)
# Here is a placeholder for logic to send scheduled emails, which would require a task scheduler
# This is not included in the Streamlit app itself, but would be managed by a backend scheduler
def scheduled_weather_updates():
    # This function would be scheduled to run at the specified update_time
    # It would check the S3 bucket for subscriptions, fetch the weather, and send emails
    pass  # Placeholder for scheduled task logic

# Note: You need to implement a background job scheduler to handle sending emails at the desired times.

if __name__ == "__main__":
    st.write("Use the above options to subscribe or unsubscribe from daily weather updates.")

