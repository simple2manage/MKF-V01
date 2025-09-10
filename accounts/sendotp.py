import random
import requests
from django.conf import settings


def send_otp_to_phone(phone_number):
    try:
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]

        otp = str(random.randint(1000, 9999))
        print(f"DEBUG: Sending OTP {otp} to {phone_number}")
        url = f'https://2factor.in/API/V1/{settings.OTP_API_KEY}/SMS/{phone_number}/{otp}'
        response = requests.get(url)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")

        return otp if response.status_code == 200 else None
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return None
