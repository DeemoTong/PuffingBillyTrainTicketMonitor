import requests
import time
import re
from twilio.rest import Client
from datetime import datetime
from playwright.sync_api import sync_playwright
import tkinter as tk
from tkinter import messagebox

# Twilio Configuration
account_sid = ''
auth_token = ''
twilio_phone_number = ''
your_phone_number = ''
refresh_interval = 60
check_date = datetime.now().strftime('%d/%m/%Y')
min_tickets = 1
browser_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"

def get_availability_urls(browser_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=browser_path, headless=True)

        context = browser.new_context()

        page = context.new_page()

        found_urls = []

        def handle_request(request):
            #print(f"Captured request: {request.url}")  
            if request.method == 'POST' and 'Availability' in request.url and 'AT=' in request.url:
                #print(f"Found URL: {request.url}")
                post_data = request.post_data
                if post_data and 'category=LAKE' in post_data:
                    #print(f"Found URL With LAKE: {request.url}")
                    found_urls.append(request.url)

        page.on("request", handle_request)

        page.goto("https://puffingbilly.com.au/buy-tickets/excursion/")
        
        page.wait_for_timeout(20000)

        cookies = context.cookies()

        browser.close()

        return found_urls, cookies


def modify_url(url):
    at_param = re.search(r'AT=([^&]+)', url).group(1)
    localtime_param = re.search(r'localtime=([^&]+)', url).group(1)
    new_url = f"https://apps.customlinc.com.au/puffingbillyrailways/BookingCat/Availability/?AT={at_param}&changeDate&localtime={localtime_param}"
    return new_url

def send_sms(message):
    try:
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=your_phone_number
        )
        print("SMS sent successfully.")  
    except Exception as e:
        print(f"Warning: Failed to send SMS.")


def check_availability(url, cookies):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-GB,en;q=0.9",
        "Origin": "https://apps.customlinc.com.au",
        "Referer": url,
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # 将 Playwright 获取到的 cookies 转换为字典
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}

    data = {
        "newDate": check_date,
        "direction": "1"
    }

    # 发送请求并使用动态 cookies
    response = requests.post(url, headers=headers, cookies=cookies_dict, data=data)
    html_content = response.text

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #print(f"{current_time} - HTML 内容: \n{html_content}\n")
    if 'logout' in html_content:
        send_sms("Token 过期，需要重新登录。")
        print(f"{current_time} - Token 过期")
        return False
    
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
                if available_tickets >= min_tickets:
                    send_sms(message)
    else:
        print(f"{current_time} - 无票")

    return True  # 返回 True 表示 token 有效

def start_checking(entry_account_sid, entry_auth_token, entry_twilio_phone_number, entry_your_phone_number, entry_refresh_interval, entry_check_date, entry_min_tickets, entry_browser_path):
    global account_sid, auth_token, twilio_phone_number, your_phone_number, refresh_interval, check_date, min_tickets, browser_path
    account_sid = entry_account_sid.get()
    auth_token = entry_auth_token.get()
    twilio_phone_number = entry_twilio_phone_number.get()
    your_phone_number = entry_your_phone_number.get()
    refresh_interval = int(entry_refresh_interval.get())
    check_date = entry_check_date.get()
    min_tickets = int(entry_min_tickets.get())
    browser_path = entry_browser_path.get()

    while True:
        # 获取 URL 和 cookies
        availability_urls, cookies = get_availability_urls(browser_path)
        
        if availability_urls:
            for availability_url in availability_urls:
                if isinstance(availability_url, str):  # 检查是否为字符串
                    modified_url = modify_url(availability_url)
                    print(f"Modified URL: {modified_url}")
                    if check_availability(modified_url, cookies):
                        break
                else:
                    print(f"Invalid URL detected: {availability_url}")
            else:
                print("No valid URL found.")
        else:
            print("No Availability URL found.")
        time.sleep(refresh_interval)  # 使用用户定义的刷新间隔


def on_start():
    try:
        start_checking()
    except Exception as e:
        messagebox.showerror("Error", str(e))

# 创建 GUI
def create_gui():
    root = tk.Tk()
    root.title("Availability Checker")

    # 如果全局变量有值，使用该值初始化输入框；如果没有值，输入框保持空白
    tk.Label(root, text="Account SID").grid(row=0, column=0)
    entry_account_sid = tk.Entry(root)
    entry_account_sid.insert(0, account_sid if account_sid else "")
    entry_account_sid.grid(row=0, column=1)

    tk.Label(root, text="Auth Token").grid(row=1, column=0)
    entry_auth_token = tk.Entry(root)
    entry_auth_token.insert(0, auth_token if auth_token else "")
    entry_auth_token.grid(row=1, column=1)

    tk.Label(root, text="Twilio Phone Number").grid(row=2, column=0)
    entry_twilio_phone_number = tk.Entry(root)
    entry_twilio_phone_number.insert(0, twilio_phone_number if twilio_phone_number else "")
    entry_twilio_phone_number.grid(row=2, column=1)

    tk.Label(root, text="Your Phone Number").grid(row=3, column=0)
    entry_your_phone_number = tk.Entry(root)
    entry_your_phone_number.insert(0, your_phone_number if your_phone_number else "")
    entry_your_phone_number.grid(row=3, column=1)

    tk.Label(root, text="Refresh Interval (seconds)").grid(row=4, column=0)
    entry_refresh_interval = tk.Entry(root)
    entry_refresh_interval.insert(0, str(refresh_interval) if refresh_interval else "")
    entry_refresh_interval.grid(row=4, column=1)

    tk.Label(root, text="Check Date (dd/mm/yyyy)").grid(row=5, column=0)
    entry_check_date = tk.Entry(root)
    entry_check_date.insert(0, check_date if check_date else "")
    entry_check_date.grid(row=5, column=1)

    tk.Label(root, text="Minimum Tickets").grid(row=6, column=0)
    entry_min_tickets = tk.Entry(root)
    entry_min_tickets.insert(0, str(min_tickets) if min_tickets else "")
    entry_min_tickets.grid(row=6, column=1)

    tk.Label(root, text="Browser Path").grid(row=7, column=0)
    entry_browser_path = tk.Entry(root)
    entry_browser_path.insert(0, browser_path if browser_path else "")
    entry_browser_path.grid(row=7, column=1)

    tk.Button(root, text="Start", command=lambda: start_checking(entry_account_sid, entry_auth_token, entry_twilio_phone_number, entry_your_phone_number, entry_refresh_interval, entry_check_date, entry_min_tickets, entry_browser_path)).grid(row=8, columnspan=2)

    root.mainloop()
create_gui()
