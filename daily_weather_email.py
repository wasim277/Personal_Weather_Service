import boto3
import json
import requests
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# OpenWeather API Key
OPENWEATHER_API_KEY = 'a960b5a01fa7e717a1b753937cdb5857'

# Email Credentials
GMAIL_EMAIL = 'awsproject277@gmail.com'
GMAIL_APP_PASSWORD = 'zoxv epbg ojpm zliq'  # Use app password

# Function to fetch 3-day weather forecast
def fetch_three_day_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        forecast_list = data['list']

        weather_report = f"3-Day Weather Forecast for {city}:\n\n"
        current_date = datetime.now().date()
        day_count = 0
        added_dates = set()

        for forecast in forecast_list:
            dt_txt = forecast['dt_txt']
            date_time = datetime.strptime(dt_txt, '%Y-%m-%d %H:%M:%S')
            forecast_date = date_time.date()

            if forecast_date not in added_dates and date_time.hour == 12:
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

# Function to read user subscriptions from S3 and send emails
def process_subscriptions():
    s3 = boto3.client(
        's3',
        aws_access_key_id='AKIASVQKH7PPWD6DWN7T',
        aws_secret_access_key='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',
        region_name='us-east-1'
    )
    bucket_name = 'weatherreporting'
    file_key = 'subscriptions.json'

    try:
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        subscriptions = json.loads(obj['Body'].read().decode('utf-8'))

        for subscription in subscriptions:
            email = subscription['email']
            city = subscription['city']
            weather_report = fetch_three_day_weather(city)
            send_email_with_gmail(
                subject=f"Daily Weather Update for {city}",
                body=weather_report,
                recipient_email=email
            )
    except s3.exceptions.NoSuchKey:
        print("No subscriptions found.")
