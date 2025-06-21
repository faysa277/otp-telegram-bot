import requests
from bs4 import BeautifulSoup
from datetime import datetime
import telegram
import time
import re

# Telegram bot info
BOT_TOKEN = '7829438504:AAG1OwgxUkBjB9CooaV5-Yvgpu6jJVS0H_A'
CHAT_ID = '-1002577343003'
bot = telegram.Bot(token=BOT_TOKEN)
# URLs
BASE_URL = 'http://94.23.120.156/ints'
LOGIN_URL = f'{BASE_URL}/login'
# Credentials
USERNAME = 'Faruk25'
PASSWORD = 'Faruk25'
SMS_REPORT_URL = f'{BASE_URL}/smsreport'

last_otp = None

def login_and_get_session():
    session = requests.Session()

    # Step 1: GET login page
    login_page = session.get(LOGIN_URL)
    soup = BeautifulSoup(login_page.text, 'html.parser')

    # Step 2: Extract math question from page
    math_question_text = soup.find(text=re.compile("What is"))
    match = re.search(r'(\d+)\s*\+\s*(\d+)', math_question_text)

    if not match:
        print("❌ Could not extract math question.")
        return None

    num1, num2 = int(match.group(1)), int(match.group(2))
    math_ans = num1 + num2

    # Step 3: Prepare POST data
    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'answer': math_ans
    }

    # Step 4: Submit login form
    response = session.post(LOGIN_URL, data=payload)

    # Step 5: Check if login worked
    if "logout" in response.text.lower():
        print("✅ Login success.")
        return session
    else:
        print("❌ Login failed.")
        return None

def get_otp_from_sms(session):
    global last_otp

    res = session.get(SMS_REPORT_URL)
    soup = BeautifulSoup(res.text, 'html.parser')

    rows = soup.select('table tbody tr')
    if not rows:
        return None

    first_row = rows[0].find_all('td')
    if len(first_row) < 2:
        return None

    number = first_row[0].text.strip()
    otp_msg = first_row[1].text.strip()

    if "-" not in otp_msg or otp_msg == last_otp:
        return None

    last_otp = otp_msg

    # Format number
    clean_number = number.replace(" ", "").replace("-", "")
    if len(clean_number) >= 7:
        masked_number = f"{clean_number[:6]}***{clean_number[-2:]}"
    else:
        masked_number = number

    current_time = datetime.now().strftime('%I:%M %p')

    message = (
        f"🔐 New OTP Received\n"
        f"📱 Number: {masked_number}\n"
        f"🕒 Time: {current_time}\n"
        f"🔑 Code: {otp_msg}"
    )
    return message

def start_bot():
    bot.send_message(chat_id=CHAT_ID, text="🟢 Bot Started and Monitoring OTPs...")
    session = login_and_get_session()
    if not session:
        bot.send_message(chat_id=CHAT_ID, text="❌ Login failed. Bot stopped.")
        return

    while True:
        try:
            otp_msg = get_otp_from_sms(session)
            if otp_msg:
                bot.send_message(chat_id=CHAT_ID, text=otp_msg)
            time.sleep(30)
        except Exception as e:
            print("❌ Error:", e)
            time.sleep(60)

if __name__ == "__main__":
    start_bot()