import boto3
import json
from datetime import datetime, time
import streamlit as st
import pytz

# AWS Credentials
AWS_ACCESS_KEY = 'AKIASVQKH7PPWD6DWN7T'
AWS_SECRET_ACCESS_KEY = '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'

# Function to save user data to S3
def save_to_s3(city, unit, email, end_date, time_zone, update_time):
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name='us-east-1'
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

# Streamlit app logic for user input
st.title("Subscribe to Daily Weather Updates")

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
update_time = st.time_input("Select Time for Updates", value=time(9, 0))
time_zones = pytz.all_timezones
time_zone = st.selectbox("Select Time Zone", time_zones)

if st.button("Subscribe"):
    subscription_saved = save_to_s3(city, unit, email, end_date, time_zone, update_time)
    if subscription_saved:
        st.success("Subscription successful! You'll receive daily updates.")
    else:
        st.warning("You are already registered for weather updates in this city.")
