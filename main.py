
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import json
import requests
from dotenv import dotenv_values

app = FastAPI()
config = dotenv_values(".env")

app.mount("/static", StaticFiles(directory="static"), name="static")

def send_webex_message(message: str, image_url: str = None):
    headers = {
        "Authorization": f"Bearer {config['WEBEX_TOKEN']}",
        "Content-Type": "application/json"
    }
    payload = {
        "roomId": config["WEBEX_ROOM_ID"],
        "markdown": f"![Chuck Norris]({image_url})\\n\\n{message}" if image_url else message
    }
    requests.post("https://webexapis.com/v1/messages", headers=headers, json=payload)

@app.post("/alert")
async def alert(request: Request):
    data = await request.json()
    message = data.get("message", "No message provided")
    send_webex_message(message)
    return {"status": "Message sent"}

@app.post("/webex")
async def receive_webex_message(request: Request):
    data = await request.json()
    message_id = data.get("data", {}).get("id")
    if not message_id:
        return {"error": "Invalid webhook payload"}

    headers = {"Authorization": f"Bearer {config['WEBEX_TOKEN']}"}
    msg_resp = requests.get(f"https://webexapis.com/v1/messages/{message_id}", headers=headers)
    if msg_resp.status_code != 200:
        return {"error": "Failed to fetch message"}

    message_data = msg_resp.json()
    message_text = message_data.get("text", "").strip()

    if message_data.get("personEmail") == get_bot_email():
        return {"status": "ignored"}

    
    if message_text.lower() == "/help":
        help_text = "**Webex Alert Bot Help**\n\n" \
                    "• `/alert your message` — Send an alert to this space\n" \
                    "• `/help` — Show this help message\n\n" \
                    "You can also send alerts from the web UI or external systems."
        send_webex_message(help_text)
        return {"status": "help sent"}

    if message_text.lower().startswith("/alert "):
        msg_to_send = message_text[7:].strip()
        send_webex_message(msg_to_send)
        return {"status": "alert sent"}

    return {"status": "no command detected"}


INAPPROPRIATE_WORDS = ["sex", "naked", "damn", "hell", "shit", "fuck"]

def is_appropriate_joke(joke):
    return not any(word in joke.lower() for word in INAPPROPRIATE_WORDS)

@app.post("/webex")
async def receive_webex_message(request: Request):
    data = await request.json()
    message_id = data.get("data", {}).get("id")
    if not message_id:
        return {"error": "Invalid webhook payload"}

    headers = {"Authorization": f"Bearer {config['WEBEX_TOKEN']}"}
    msg_resp = requests.get(f"https://webexapis.com/v1/messages/{message_id}", headers=headers)
    if msg_resp.status_code != 200:
        return {"error": "Failed to fetch message"}

    message_data = msg_resp.json()
    message_text = message_data.get("text", "").strip()

    if message_data.get("personEmail") == get_bot_email():
        return {"status": "ignored"}

    if message_text.lower() == "/help":
        help_text = "**Webex Alert Bot Help**\n\n" \
                    "• `/alert your message` — Send an alert to this space\n" \
                    "• `/help` — Show this help message\n" \
                    "• `/chuck` — Get a PG-rated Chuck Norris joke"
        send_webex_message(help_text)
        return {"status": "help sent"}

    if message_text.lower().startswith("/alert "):
        msg_to_send = message_text[7:].strip()
        send_webex_message(msg_to_send)
        return {"status": "alert sent"}

    if message_text.lower() == "/chuck":
        joke_text, icon_url = "", ""
        for _ in range(5):
            joke_resp = requests.get("https://api.chucknorris.io/jokes/random")
            if joke_resp.status_code == 200:
                joke_data = joke_resp.json()
                joke = joke_data.get("value", "")
                if is_appropriate_joke(joke):
                    joke_text = joke
                    icon_url = joke_data.get("icon_url", "")
                    break
        if joke_text:
            send_webex_message(joke_text, icon_url)
            return {"status": "chuck joke sent"}
        else:
            send_webex_message("Couldn't find a clean Chuck Norris joke right now!")
            
    if message_text.lower() == "/dadjoke":
        joke_resp = requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"})
        if joke_resp.status_code == 200:
            joke = joke_resp.json().get("joke", "")
            send_webex_message(joke)
            return {"status": "dadjoke sent"}
        else:
            send_webex_message("Couldn't fetch a dad joke.")
            return {"status": "dadjoke error"}

    if message_text.lower().startswith("/weather "):
        zip_code = message_text[9:].strip()
        if not re.match(r"^\d{5}$", zip_code):
            send_webex_message("Please provide a valid 5-digit ZIP code.")
            return {"status": "invalid zip code"}
        key = config.get("OPENWEATHER_API_KEY", "")
        if not key:
            send_webex_message("Weather API key not configured.")
            return {"status": "missing weather api key"}
        url = f"http://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&units=imperial&appid={key}"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            weather = (f"Weather in {data.get('name', 'Unknown')}: {data['weather'][0]['description'].title()}\n"
                       f"Temp: {data['main']['temp']}°F, Humidity: {data['main']['humidity']}%\n"
                       f"Wind: {data['wind']['speed']} mph")
            send_webex_message(weather)
            return {"status": "weather sent"}
        else:
            send_webex_message("Couldn't fetch weather data.")
            return {"status": "weather error"}

    if message_text.lower().startswith("/movie "):
        zip_code = message_text[7:].strip()
        key = config.get("MOVIE_API_KEY", "")
        if not re.match(r"^\d{5}$", zip_code):
            send_webex_message("Please provide a valid 5-digit ZIP code.")
            return {"status": "invalid zip code"}
        if not key:
            send_webex_message("Movie API key not configured.")
            return {"status": "missing movie api key"}
        today = date.today().isoformat()
        url = f"http://data.tmsapi.com/v1.1/movies/showings?startDate={today}&zip={zip_code}&api_key={key}"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            if not data:
                send_webex_message("No movies found.")
                return {"status": "no movies"}
            msg = "Movies today:\n" + "\n".join([f"{m['title']}" for m in data[:5]])
            send_webex_message(msg)
            return {"status": "movies sent"}
        else:
            send_webex_message("Error getting movie times.")
            return {"status": "movie error"}

    if message_text.lower() == "/tv":
        key = config.get("TV_API_KEY", "")
        if not key:
            send_webex_message("TV API key not configured.")
            return {"status": "missing tv api key"}
        now = datetime.now()
        start = now.replace(hour=18, minute=0).isoformat()
        end = now.replace(hour=22, minute=0).isoformat()
        networks = ["ABC", "NBC", "CBS", "Paramount", "Max"]
        url = f"https://api.tvmedia.ca/tvlistings?start={start}&end={end}&networks={','.join(networks)}&api_key={key}"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            msg = "TV Tonight:\n" + "\n".join([f"{s['network']}: {s['program']}" for s in data[:5]])
            send_webex_message(msg)
            return {"status": "tv sent"}
        else:
            send_webex_message("Error getting TV listings.")
            return {"status": "tv error"}
return {"status": "no clean joke found"}


    headers = {"Authorization": f"Bearer {config['WEBEX_TOKEN']}"}
    profile = requests.get("https://webexapis.com/v1/people/me", headers=headers)
    if profile.status_code == 200:
        return profile.json().get("emails", [""])[0]
    return ""

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html") as f:
        return f.read()

@app.websocket("/alert")
async def websocket_alert(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        send_webex_message(data)
        await websocket.send_text(f"Sent: {data}")
