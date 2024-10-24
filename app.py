from flask import Flask, jsonify
from flask_cors import CORS
import time
import RPi.GPIO as GPIO
from Freenove_DHT import DHT
import smtplib
from email.mime.text import MIMEText

# Setup the DHT11 pin
DHTPin = 17  # GPIO 17 for DHT11

# Setup the LED pin
LED_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)  # Suppress GPIO warnings
GPIO.setup(LED_PIN, GPIO.OUT)

app = Flask(__name__)
CORS(app)

led_status = "off"

def send_email(temperature):
    sender_email = "iot2024vaniercollege@gmail.com"  # your Gmail address(the fake one we are using)
    receiver_email = "olivierleone.90@gmail.com"  # recipient's email
    subject = "Temperature Alert"
    body = f"The current temperature is {temperature:.2f}°C. Would you like to turn on the fan?"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, "rncz xybc adhk ljbq") #App Password here
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/toggle', methods=['GET'])
def toggle_led():
    global led_status
    if led_status == "off":
        GPIO.output(LED_PIN, GPIO.HIGH)
        led_status = "on"
    else:
        GPIO.output(LED_PIN, GPIO.LOW)
        led_status = "off"
    return jsonify({"status": led_status})

@app.route('/sensors', methods=['GET'])
def get_sensor_data():
    dht = DHT(DHTPin)
    
    # Attempt to read the sensor up to 15 times
    for i in range(15):
        chk = dht.readDHT11()
        if chk == 0:
            # Successfully read the sensor
            humidity = dht.getHumidity()
            temperature = dht.getTemperature()
            # Check if temperature exceeds 24°C and send an email
            if temperature > 24:
                send_email(temperature)
            return jsonify({"humidity": round(humidity, 2), "temperature": round(temperature, 2)})
        time.sleep(0.1)
    
    # If the reading fails, return an error
    return jsonify({"error": "Failed to retrieve data from the sensor"}), 500

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()  # Clean up GPIO pins on exit
