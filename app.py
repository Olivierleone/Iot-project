#imports
import RPi.GPIO as GPIO
import time
import imaplib
import email
from datetime import datetime
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from Freenove_DHT import DHT
import threading
import smtplib
import paho.mqtt.client as mqtt
import sqlite3
import json

rfid_scanned_from_mqtt = None
# GPIO setup

#GPIO pin for the DHT11 temperature and humidity sensor
DHTPin = 17  

#GPIO pin for the LED
LED_PIN = 18

#variable to see if email is sent or not (used for light intensity)
email_sent = False

# MQTT setup
MQTT_BROKER = "172.20.10.4"  # Set to your Raspberry Pi IP 
MQTT_PORT = 1883  # Default MQTT port
MQTT_LIGHT_TOPIC = "home/light"
MQTT_RFID_TOPIC = "home/rfid"

#variable for light intensity
light_intensity_value = 0

#GPIO pins for motor control
 # Enable pin for the motor (MOTOR1)
MOTOR1_PIN = 13  

# Input pin for controlling the direction of MOTOR2
MOTOR2_PIN = 6   

 # Input pin for controlling the direction of MOTOR3
MOTOR3_PIN = 5  

# Set the GPIO mode to BCM 
# Disable warnings to avoid cluttering the output
# Set up the LED pin as an output
# Set up the enable pin for MOTOR1 as an output
# Set up the input pin for MOTOR2 as an output
# Set up the input pin for MOTOR3 as an output
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(MOTOR1_PIN, GPIO.OUT)
GPIO.setup(MOTOR2_PIN, GPIO.OUT)
GPIO.setup(MOTOR3_PIN, GPIO.OUT)

# Initialize a Flask application instance
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) for the application
CORS(app)

# Flag to track whether the motor is currently active
motor_active = False

# Flag to indicate if a reply to the email has been processed
reply_processed = False

# Dictionary to store user IDs that have already processed replies(prevents multiple replys from activiating motor)
reply_processed_uids = {}

# Store the timestamp of the last email sent, initialized to 1 minute ago
last_email_time = datetime.now() - timedelta(minutes=1)

# Variable to track the status of the LED, initialized to 'off'
led_status = "off"


# Email credentials and server
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
EMAIL_ACCOUNT = "iot2024vaniercollege@gmail.com"
EMAIL_PASSWORD = "rncz xybc adhk ljbq"  # App-specific password for email access


#method to connect to the mqtt broker
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker")
    client.subscribe(MQTT_LIGHT_TOPIC)
    client.subscribe(MQTT_RFID_TOPIC)

def on_message(client, userdata, msg):
    global led_status, email_sent, light_intensity_value  # Declare the global variables

    topic = msg.topic
    payload = msg.payload.decode()  # Decode the raw payload
    print(f"Received message on topic {topic}: {payload}")

    global rfid_scanned_from_mqtt
    try:
        if topic == MQTT_LIGHT_TOPIC:
            # Handle light intensity
            light_intensity_value = int(payload)  # Update the global light intensity variable
            print(f"Light intensity: {light_intensity_value}")

            if light_intensity_value < 400:
                GPIO.output(LED_PIN, GPIO.HIGH)  # Turn on LED
                led_status = "on"  # Update global led_status
                print("LED turned ON (low light)")

                # Send email if not already sent
                if not email_sent:
                    send_light_status_email()
            else:
                GPIO.output(LED_PIN, GPIO.LOW)  # Turn off LED
                led_status = "off"  # Update global led_status
                print("LED turned OFF (sufficient light)")

                # Reset email_sent when light intensity goes above 400
                email_sent = False
                print("Email status reset to 'not sent' due to high light intensity")

        elif topic == MQTT_RFID_TOPIC:
            # Handle RFID data
            rfid_tag = payload  # Read as a string
            print(f"RFID Tag: {rfid_tag}")
            rfid_scanned_from_mqtt = rfid_tag  # Set the scanned RFID value

        else:
            print(f"Unhandled topic: {topic}")

    except ValueError as ve:
        print(f"ValueError: {ve}")
    except Exception as e:
        print(f"Unexpected error: {e}")
# connecting to the mqtt brocker
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

#path for the light intensity 
@app.route('/light_intensity', methods=['GET'])
def light_intensity():
    # Ensure the data from MQTT is available
    if light_intensity_value is None:
        return jsonify({"error": "Data not yet received from MQTT"}), 500

    # Logging to verify status
    print(f"LED status: {led_status}")

    # variable to detect if the email is actually sent or no 
    global email_sent
    email_sent = email_sent if email_sent is not None else False

    return jsonify({
        "light_intensity": light_intensity_value,
        "led_status": led_status,
        "email_sent": email_sent
    })

    #m method to send email if light intensity is below 400
def send_light_status_email():
    global last_email_time, email_sent, led_status

    # Only send an email if the LED is on and at least 1 minute has passed since the last email
    if led_status == "on" and datetime.now() - last_email_time >= timedelta(minutes=1) and not email_sent:
        sender_email = EMAIL_ACCOUNT
        receiver_email = "olivier.leone90@gmail.com"  # Change to the recipient's email address
        subject = "Light Status Update"
        body = f"The light is on at {datetime.now().strftime('%H:%M')}."

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email

        try:
            with smtplib.SMTP(SMTP_SERVER, 587) as server:
                server.starttls()
                server.login(sender_email, EMAIL_PASSWORD)
                server.sendmail(sender_email, receiver_email, msg.as_string())
                print("Light status email sent successfully.")
                last_email_time = datetime.now()  # Update the timestamp for the last email
                email_sent = True  # Mark the email as sent
        except Exception as e:
            print(f"Failed to send email: {e}")
       

# method to send emails each minute 
def send_light_status_email_periodically():
    while True:
        send_light_status_email()
        time.sleep(5)  # Wait for 1 minute before sending the next email

# Activate the motor for a specified duration (default 10 seconds) and then disable it
def activate_motor_for_duration(duration=10):
    global motor_active
    motor_active = True
    GPIO.output(MOTOR1_PIN, GPIO.HIGH) 
    GPIO.output(MOTOR2_PIN, GPIO.HIGH)  
    GPIO.output(MOTOR3_PIN, GPIO.LOW)  
    time.sleep(duration)
    GPIO.output(MOTOR1_PIN, GPIO.LOW)   
    GPIO.output(MOTOR2_PIN, GPIO.LOW)
    GPIO.output(MOTOR3_PIN, GPIO.LOW)
    motor_active = False 


 # Endpoint to retrieve the current status of the motor
@app.route('/motor_status', methods=['GET'])
def get_motor_status():
    return jsonify({"motor_active": motor_active})


# Function to check and clean up expired UIDs
def cleanup_processed_replies():
    global reply_processed_uids
    while True:
        current_time = datetime.now()
        for uid in list(reply_processed_uids.keys()):
            # Check if the UID was processed more than 60 seconds ago
            if current_time - reply_processed_uids[uid] > timedelta(seconds=60):
                del reply_processed_uids[uid]  # Remove expired UID
        time.sleep(10)  # Check every 10 seconds


# Function to send temperature alert email
def send_email(temperature):
    global last_email_time,email_sent

    #preventing email flooding by limiting to 1 email sent per 2 minutes
    if datetime.now() - last_email_time < timedelta(minutes=2):
        print("Skipping email - sent less than two minutes ago")
        return

 # email info fpr sending email
    sender_email = EMAIL_ACCOUNT
    receiver_email = "olivierleone.90@gmail.com" #can be whatever email
    subject = "Temperature Alert"
    body = f"The current temperature is {temperature:.2f}°C. Would you like to turn on the fan?"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:

        #sending the actual email with exception to see if operation failed
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
# if temp is more than 24 from the dht11 sensor then send email that has the specified temp
@app.route('/sensors', methods=['GET'])
def get_sensor_data():
    print("Received request for /sensors")
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

# Check for unread email replies with the subject "Re: Temperature Alert" 
# and activate the fan if a reply contains "yes"; track processed replies to prevent reactivation with messageID
def check_email_reply():
    global reply_processed_uids
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")
        _, messages = mail.search(None, '(UNSEEN SUBJECT "Re: Temperature Alert")')

        for num in messages[0].split():
            _, msg_data = mail.fetch(num, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    uid = msg["Message-ID"]
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                reply = part.get_payload(decode=True).decode()
                                # Check if reply is "yes" and if this UID has not been processed
                                if "yes" in reply.lower() and uid not in reply_processed_uids:
                                    print("Activating fan based on email reply")
                                    activate_motor_for_duration()  # Activate motor
                                    reply_processed_uids[uid] = datetime.now()  # Mark this UID as processed to prevent replying to the same email
                    mail.store(num, "+FLAGS", "\\Seen")
        mail.logout()
    except Exception as e:
        print(f"Error checking email: {e}")


# Function to run email checking in the background
def start_email_checker():
    while True:
        check_email_reply()
        time.sleep(5)  # Check every 5 seconds


# Function to check if the RFID exists in the database
def check_rfid_in_db(rfid):
    conn = sqlite3.connect('iot_dashboard.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE rfid_tag=?", (rfid,))
    user = cursor.fetchone()
    conn.close()
    return user

@app.route('/home/rfid', methods=['POST'])
def scan_rfid():
    global rfid_scanned_from_mqtt

    # Get RFID from request or fallback to last scanned from MQTT
    rfid = request.json.get('rfid') or rfid_scanned_from_mqtt

    if not rfid:
        return jsonify({'success': False, 'message': 'No RFID provided or scanned'})

    user = check_rfid_in_db(rfid)
    if user:
        return jsonify({'success': True, 'message': f'Welcome, {user[1]}!'})
    else:
        return jsonify({'success': False, 'message': 'Invalid RFID tag'})


@app.route('/home/rfid-status', methods=['GET'])
def rfid_status():
    global rfid_scanned_from_mqtt
    print(f"rfid_scanned_from_mqtt: {rfid_scanned_from_mqtt}")  # Log the value of rfid_scanned_from_mqtt
    if rfid_scanned_from_mqtt:
        user = check_rfid_in_db(rfid_scanned_from_mqtt)
        if user:
            message = f"Welcome, {user[1]}!"  # Assuming user[1] is the user's name
            rfid_tag = rfid_scanned_from_mqtt  # Get the scanned RFID tag
            rfid_scanned_from_mqtt = None  # Reset after successful login
            return jsonify({'success': True, 'rfid_tag': rfid_tag, 'message': message})
        else:
            rfid_scanned_from_mqtt = None  # Reset even for invalid RFID
            return jsonify({'success': False, 'message': 'Invalid RFID tag'})
    return jsonify({'success': False, 'message': 'No valid RFID scanned'})



def get_user_profile(rfid_tag):
    conn = sqlite3.connect('iot_dashboard.db')
    cursor = conn.cursor()
    cursor.execute("SELECT rfid_tag, light_threshold, temp_threshold FROM users WHERE rfid_tag = ?", (rfid_tag,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return {"rfid_tag": result[0], "light_preference": result[1], "temp_preference": result[2]}
    else:
        return None

@app.route('/get_user_profile', methods=['GET'])
def get_user_profile():
    rfid_tag = request.args.get('rfid_tag')  # Get the RFID tag from query parameters
    
    if not rfid_tag:
        return jsonify({'success': False, 'message': 'RFID tag is required'})
    
    user = check_rfid_in_db(rfid_tag)  # Assuming check_rfid_in_db function works as expected
    
    if user:
        # Assuming the user record has these fields: rfid_tag, light_preference, temp_preference
        return jsonify({
            'success': True,
            'rfid_tag': user[1],  # Assuming user[1] is the RFID tag
            'light_preference': user[3],  # Assuming user[3] is the light preference
            'temp_preference': user[2]  # Assuming user[2] is the temperature preference
        })
    else:
        return jsonify({'success': False, 'message': 'User not found'})


# Start background threads for continuous email checking and cleanup of processed replies
threading.Thread(target=start_email_checker, daemon=True).start()
threading.Thread(target=cleanup_processed_replies, daemon=True).start()
threading.Thread(target=send_light_status_email_periodically, daemon=True).start()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
