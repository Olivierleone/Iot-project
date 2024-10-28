import RPi.GPIO as GPIO
import time
import imaplib
import email
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask import Flask, jsonify
from flask_cors import CORS
from Freenove_DHT import DHT
import threading
import smtplib

# GPIO setup
DHTPin = 17  # GPIO 17 for DHT11
LED_PIN = 18
MOTOR1_PIN = 13  # Enable Pin
MOTOR2_PIN = 6   # Input Pin
MOTOR3_PIN = 5   # Input Pin

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(MOTOR1_PIN, GPIO.OUT)
GPIO.setup(MOTOR2_PIN, GPIO.OUT)
GPIO.setup(MOTOR3_PIN, GPIO.OUT)

app = Flask(__name__)
CORS(app)
motor_active = False
led_status = "off"
last_email_time = datetime.now() - timedelta(minutes=1)

# Email credentials and server
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
EMAIL_ACCOUNT = "iot2024vaniercollege@gmail.com"
EMAIL_PASSWORD = "rncz xybc adhk ljbq"  # App-specific password for email access

def activate_motor_for_duration(duration=10):
    global motor_active
    motor_active = True
    GPIO.output(MOTOR1_PIN, GPIO.HIGH)  # Enable motor
    GPIO.output(MOTOR2_PIN, GPIO.HIGH)  # Start motor
    GPIO.output(MOTOR3_PIN, GPIO.LOW)   # Set direction
    time.sleep(duration)
    GPIO.output(MOTOR1_PIN, GPIO.LOW)   # Disable motor
    GPIO.output(MOTOR2_PIN, GPIO.LOW)
    GPIO.output(MOTOR3_PIN, GPIO.LOW)
    motor_active = False 

@app.route('/motor_status', methods=['GET'])
def get_motor_status():
    return jsonify({"motor_active": motor_active})

# Function to send temperature alert email
def send_email(temperature):
    global last_email_time
    if datetime.now() - last_email_time < timedelta(minutes=2):
        print("Skipping email - sent less than two minutes ago")
        return

    sender_email = EMAIL_ACCOUNT
    receiver_email = "olivierleone.90@gmail.com"
    subject = "Temperature Alert"
    body = f"The current temperature is {temperature:.2f}°C. Would you like to turn on the fan?"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP(SMTP_SERVER, 587) as server:
            server.starttls()
            server.login(sender_email, EMAIL_PASSWORD)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully")
            last_email_time = datetime.now()
    except Exception as e:
        print(f"Failed to send email: {e}")

# Route to toggle LED
@app.route('/toggle', methods=['GET'])
def toggle_led():
    global led_status
    GPIO.output(LED_PIN, GPIO.HIGH if led_status == "off" else GPIO.LOW)
    led_status = "on" if led_status == "off" else "off"
    return jsonify({"status": led_status})

# Route to retrieve sensor data and send email if necessary
@app.route('/sensors', methods=['GET'])
def get_sensor_data():
    dht = DHT(DHTPin)
    for _ in range(15):
        if dht.readDHT11() == 0:
            humidity = dht.getHumidity()
            temperature = dht.getTemperature()
            if temperature > 24:
                send_email(temperature)
            return jsonify({"humidity": round(humidity, 2), "temperature": round(temperature, 2)})
        time.sleep(0.1)
    return jsonify({"error": "Failed to retrieve data from the sensor"}), 500

# Function to check email replies
def check_email_reply():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Re: Temperature Alert")')

        for num in messages[0].split():
            status, msg_data = mail.fetch(num, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                reply = part.get_payload(decode=True).decode()
                                if "yes" in reply.lower():
                                    print("Activating fan based on email reply")
                                    activate_motor_for_duration()  # Motor activation
                    mail.store(num, "+FLAGS", "\\Seen")
        mail.logout()
    except Exception as e:
        print(f"Error checking email: {e}")

# Function to run email checking in the background
def start_email_checker():
    while True:
        check_email_reply()
        time.sleep(5)  # Check every 5 seconds

# Start background thread for email checking
threading.Thread(target=start_email_checker, daemon=True).start()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
