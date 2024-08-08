import requests
import time
import re
from twilio.rest import Client
from datetime import datetime
from playwright.sync_api import sync_playwright

# Twilio Configuration
account_sid = 'XXXXXXXXXXXXXXXXXX'
auth_token = 'XXXXXXXXXXXXXXXXXXX'
twilio_phone_number = '+12089031693'
your_phone_number = '+61419328769'

# Get new token URLs
def get_availability_urls():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        found_urls = []

        def handle_request(request):
            if request.method == 'POST' and 'Availability' in request.url and 'AT=' in request.url:
                print(f"Found URL: {request.url}")
                post_data = request.post_data
                if post_data and 'category=LAKE' in post_data:
                    print(f"Found URL With LAKE: {request.url}")  
                    found_urls.append(request.url)

        page.on("request", handle_request)

        page.goto("https://puffingbilly.com.au/buy-tickets/excursion/")

        page.wait_for_timeout(10000)

        browser.close()

        return found_urls

def modify_url(url):
    # export AT and localtime parameters
    at_param = re.search(r'AT=([^&]+)', url).group(1)
    localtime_param = re.search(r'localtime=([^&]+)', url).group(1)
    # construct new URL
    new_url = f"https://apps.customlinc.com.au/puffingbillyrailways/BookingCat/Availability/?AT={at_param}&changeDate&localtime={localtime_param}"
    return new_url
def send_sms(message):
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=message,
        from_=twilio_phone_number,
        to=your_phone_number
    )


def check_availability(url):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-GB,en;q=0.9",
        "Origin": "https://apps.customlinc.com.au",
        "Referer": "https://apps.customlinc.com.au/puffingbillyrailways/BookingCat/Availability/?changeDate&localtime=2024-07-29,%2010:30:30:535",
        "X-Requested-With": "XMLHttpRequest",
    }

    cookies = {
        "currentBrandWAFApplicationBookingCat": "PUFFING%20BILLY",
        "oidToken": "12594595.467180---EKKRegvApR6n5FLpf6Rj"
    }

    data = {
        "newDate": "06/09/2024",
        "direction": "1"
    }

    response = requests.post(url, headers=headers, cookies=cookies, data=data)
    html_content = response.text

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if 'logout' in html_content:
        send_sms("Token 过期，需要重新登录。")
        print(f"{current_time} - Token 过期")
        return False  # 返回 False 表示 token 过期
    
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

    return True  


while True:
    # get availability URLs
    availability_urls = get_availability_urls()
    if availability_urls:
        for availability_url in availability_urls:
            modified_url = modify_url(availability_url)
            print(f"Modified URL: {modified_url}")
            if check_availability(modified_url):
                break
        else:
            print("No valid URL found.")
    else:
        print("No Availability URL found.")
    time.sleep(60)  # retry every 60 seconds
