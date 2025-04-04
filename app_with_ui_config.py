from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO
import requests
import os
import sys

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

ENV_PATH = ".env"
WEBEX_TOKEN = os.getenv('WEBEX_TOKEN')
ROOM_ID = os.getenv('WEBEX_ROOM_ID')
WEBEX_API_URL = 'https://webexapis.com/v1/messages'

headers = {
    'Authorization': f'Bearer {WEBEX_TOKEN}',
    'Content-Type': 'application/json'
}

HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Webex Alert Bot</title>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 0;
      background: linear-gradient(to right, #1c92d2, #f2fcfe);
    }
    .container {
      max-width: 700px;
      margin: 40px auto;
      background: #fff;
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 0 20px rgba(0,0,0,0.1);
    }
    h2 {
      text-align: center;
      color: #1c92d2;
    }
    textarea, input[type="text"] {
      width: 100%;
      font-size: 16px;
      padding: 10px;
      margin-bottom: 15px;
      border-radius: 5px;
      border: 1px solid #ccc;
      box-sizing: border-box;
    }
    button {
      background-color: #1c92d2;
      color: white;
      border: none;
      padding: 12px 25px;
      font-size: 16px;
      border-radius: 5px;
      cursor: pointer;
      display: block;
      margin: 10px auto;
    }
    button:hover {
      background-color: #166fa7;
    }
    .status {
      text-align: center;
      font-weight: bold;
    }
    .section {
      margin-bottom: 30px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>Send Webex Alert</h2>
    <div class="section">
      <input type="text" id="server" value="http://localhost:5650/alert" />
      <textarea id="message" placeholder="Type your alert message here..."></textarea>
      <button onclick="sendAlert()">Send Alert</button>
      <div id="status" class="status"></div>
    </div>

    <hr />

    <h2>Update Bot Configuration</h2>
    <div class="section">
      <input type="text" id="token" placeholder="New Webex Bot Token" />
      <input type="text" id="room" placeholder="New Webex Room ID" />
      <button onclick="updateConfig()">Update Config & Restart</button>
      <div id="configStatus" class="status"></div>
    </div>
  </div>

  <script>
    async function sendAlert() {
      const server = document.getElementById("server").value;
      const message = document.getElementById("message").value;
      const statusDiv = document.getElementById("status");

      if (!message.trim()) {
        statusDiv.textContent = "Please enter a message.";
        return;
      }

      try {
        const response = await fetch(server, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message })
        });

        const data = await response.json();
        statusDiv.textContent = "Alert sent! Status: " + response.status;
      } catch (err) {
        statusDiv.textContent = "Error: " + err.message;
      }
    }

    async function updateConfig() {
      const token = document.getElementById("token").value;
      const room = document.getElementById("room").value;
      const configStatus = document.getElementById("configStatus");

      if (!token.trim() || !room.trim()) {
        configStatus.textContent = "Both token and room ID are required.";
        return;
      }

      try {
        const response = await fetch("/update-config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, room })
        });

        const data = await response.json();
        configStatus.textContent = data.message || "Update complete.";
      } catch (err) {
        configStatus.textContent = "Error: " + err.message;
      }
    }
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/alert', methods=['POST'])
def alert():
    data = request.get_json()
    message = data.get('message')
    if not message:
        return jsonify({'error': 'Missing message'}), 400

    status_code, resp = send_webex_message(message)
    return jsonify(resp), status_code

@app.route('/update-config', methods=['POST'])
def update_config():
    data = request.get_json()
    token = data.get('token')
    room = data.get('room')

    if not token or not room:
        return jsonify({'error': 'Missing token or room ID'}), 400

    try:
        with open(ENV_PATH, 'w') as f:
            f.write(f"WEBEX_TOKEN={token}
")
            f.write(f"WEBEX_ROOM_ID={room}
")
        return jsonify({'message': 'Config updated. Restarting...'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.execv(sys.executable, ['python'] + sys.argv)

@socketio.on('alert')
def handle_socket_alert(data):
    message = data.get('message')
    if message:
        status_code, resp = send_webex_message(message)
        socketio.emit('alert_response', {'status': status_code, 'response': resp})
    else:
        socketio.emit('alert_response', {'error': 'Missing message'})

def send_webex_message(message, room_id=ROOM_ID):
    payload = {
        'text': message,
        'roomId': room_id
    }
    response = requests.post(WEBEX_API_URL, headers=headers, json=payload)
    return response.status_code, response.json()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5650)
