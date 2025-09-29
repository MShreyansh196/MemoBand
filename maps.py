import folium

m = folium.Map(location=[37.7749, -122.4194], zoom_start=12)
m.save("map.html")
from flask import Flask, render_template, jsonify
import random
import time
import threading

app = Flask(__name__)

# Current GPS coordinates (initialize to somewhere)
gps_data = {"lat": 37.7749, "lon": -122.4194}

# Function to simulate GPS updates (replace with real GPS reading)
def gps_updater():
    global gps_data
    while True:
        # Example: simulate small movements
        gps_data["lat"] += random.uniform(-0.0005, 0.0005)
        gps_data["lon"] += random.uniform(-0.0005, 0.0005)
        time.sleep(2)  # update every 2 seconds

# Start GPS updater in background thread
threading.Thread(target=gps_updater, daemon=True).start()

@app.route("/")
def index():
    return render_template("map.html")  # HTML map file

@app.route("/gps")
def get_gps():
    return jsonify(gps_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
