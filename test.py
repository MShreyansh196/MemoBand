import gpsd
import time

# Connect to the local gpsd
gpsd.connect()

while True:
    packet = gpsd.get_current()
    
    if packet.mode >= 2:  # 2D or 3D fix
        latitude = packet.lat
        longitude = packet.lon
        altitude = packet.alt
        print(f"Latitude: {latitude}, Longitude: {longitude}, Altitude: {altitude}")
    else:
        print("Waiting for GPS fix...")

    time.sleep(1)
