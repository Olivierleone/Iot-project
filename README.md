# Phase1
First phase of our IOT project


## Setup Instructions
### 1. Start Live Server

1. Open Visual Studio Code
2. Launch the Live Server extension to serve your HTML files. This will allow you to view and interact with your dashboard.

### 2. Start Flask Server

1. Open a terminal or command prompt.
   
2. Navigate to the directory containing your `app.py` file:
   cd /path/to/your/project
   then run it with python3 app.py

### 3. Verify Ip Address

1. Verify ip address matches the system and in the html fetch (used to get /toggle from the python server)
   ex:  fetch('http://192.168.1.1811:5000/toggle')

### 4. Make sure flask_cors is imported and installed (should already be done)

# Phase 2
Second phase of our IoT project

## Setup Instructions

### 1. Configure SMTP Server

1. Open your `app.py` file.
2. Ensure you have the following SMTP settings configured:
   - **Sender Email**: Your email address that will send notifications.
   - **Receiver Email**: The email address where notifications will be sent.
   - **App Password**: The password for the sender email account (this should be generated if you have 2-step verification enabled).

### 2. Generate App Password (if unsure where to find it)

1. **For Gmail Users**:
   - Go to your Google Account settings.
   - Navigate to **Security**.
   - Under the "Signing in to Google" section, ensure 2-Step Verification is turned on.
   - Once 2-Step Verification is enabled, find the **App passwords** option and click on it.
   - Select the app and device you want to generate the password for and click **Generate**.
   - Copy the generated password and use it in your `app.py` file.

2. **For Other Email Providers**: 
   - Refer to your email provider's documentation on generating app passwords or enabling SMTP access.

### 3. Start Live Server

1. Open Visual Studio Code.
2. Launch the Live Server extension to serve your HTML files. This will allow you to view and interact with your dashboard.

### 4. Start Flask Server

1. Open a terminal or command prompt.
2. Navigate to the directory containing your `app.py` file:
   ```bash
   cd /path/to/your/project
 
