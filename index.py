from playwright.sync_api import sync_playwright
import time

def get_availability_url():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 创建一个变量来存储找到的 URL
        found_url = None

        # 定义一个处理网络请求的回调函数
        def handle_request(request):
            nonlocal found_url
            url = request.url
            if 'Availability' in url:
                found_url = url

        # 监听网络请求
        page.on("request", handle_request)

        # 打开指定网页
        page.goto("https://puffingbilly.com.au/buy-tickets/excursion/")

        # 等待几秒钟确保页面加载完成
        time.sleep(10)

        # 关闭浏览器
        browser.close()

        return found_url

# 获取 URL 并打印
availability_url = get_availability_url()
if availability_url:
    print(f"Found URL: {availability_url}")
else:
    print("No Availability URL found.")
