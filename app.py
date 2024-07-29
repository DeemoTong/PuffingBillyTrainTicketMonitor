import requests
import time
import re
from twilio.rest import Client
from datetime import datetime

# Twilio Configuration
account_sid = 'AC41af73fd7d56737982db8e345a4bad0c'
auth_token = '51badeb69076c7fcd5eb227f504d7899'
twilio_phone_number = '+12089031693'
your_phone_number = '+61419328769'

# **Required**:
# Request URL (Request headers Path)
# Normally you will only need to change this url in order to get the availability of tickets
url = "https://apps.customlinc.com.au/puffingbillyrailways/BookingCat/Availability/?AT=5F1BXvWrApR6LSFLpf6Rtj&changeDate&localtime=2024-07-29,%2010:30:30:535"

# Request Headers
headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-GB,en;q=0.9",
    "Origin": "https://apps.customlinc.com.au",
    "Referer": "https://apps.customlinc.com.au/puffingbillyrailways/BookingCat/Availability/?changeDate&localtime=2024-07-29,%2010:30:30:535",
    "X-Requested-With": "XMLHttpRequest",
}

# Request cookie
cookies = {
    "currentBrandWAFApplicationBookingCat": "PUFFING%20BILLY",
    "oidToken": "12594595.467180---EKKRegvApR6n5FLpf6Rj"
}

# Request data, newDate is the date you want to check, DD/MM/YYYY format
# The API will only return the next 5 days of availability
# If you want more days, you need to run multiple tasks with different dates
data = {
    "newDate": "06/08/2024",
    "direction": "1"
}

def send_sms(message):
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=message,
        from_=twilio_phone_number,
        to=your_phone_number
    )

def check_availability():
    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    html_content = response.text

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if 'logout' in html_content:
        send_sms("Token 过期，需要重新登录。")
        print(f"{current_time} - Token 过期")
        return
    
    matches = list(re.finditer("Limited Seats", html_content))
    
    if matches:
        for match in matches:
            start_index = max(0, match.start() - 300)
            end_index = min(len(html_content), match.end() + 19)
            context = html_content[start_index:end_index]
            message = f"有票了！上下文：\n{context}"
            print(f"{current_time} - {message}")

            ticket_match = re.search(r'<br>\s*(\d+)\s*Available', message)
            if ticket_match:
                available_tickets = int(ticket_match.group(1))
                # Send SMS if available tickets are >= 3
                if available_tickets >= 3:
                    send_sms(message)
    else:
        print(f"{current_time} - 无票")
        
        
        

# Optional: Loop requests to refresh tickets
while True:
    check_availability()
    time.sleep(60)  # check every 60 seconds

