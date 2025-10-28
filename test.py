import gpsd
import time

gpsd.connect()

while True:
    packet = gpsd.get_current()
    
    if packet.mode >= 2: 
        latitude = packet.lat
        longitude = packet.lon
        altitude = packet.alt
        print(f"Latitude: {latitude}, Longitude: {longitude}, Altitude: {altitude}")
    else:
        print("Waiting for GPS fix...")

    time.sleep(1)
