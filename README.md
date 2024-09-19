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
 
