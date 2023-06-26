#!/usr/bin/env python3

import time
import pymysql.cursors
from jetson_inference import detectNet
from jetson_utils import videoSource, videoOutput, cudaDrawRect

net = detectNet("ssd-inception-v2", threshold=0.5)
net.SetTrackingEnabled(True)

camera = videoSource("/dev/video0", ["--input-width=1280", "--input-height=720", "--input-flip=rotate+180"]) 
display = videoOutput("display://0") 

zones = {
    'zone1': ((0,0), (426,720), (255, 0, 0, 50)),
    'zone2': ((427,0), (853,720), (0, 255, 0, 50)),
    'zone3': ((854,0), (1280,720), (0, 0, 255, 50))
}


# Connect to the database
connection = pymysql.connect(host="localhost",
                            user="uzivatel",
                            password="ABCabc123",
                            database="Customers",
                             cursorclass=pymysql.cursors.DictCursor)

# Initialize timestamp
last_written = time.time()

while display.IsStreaming():
    img = camera.Capture()

    if img is None: # capture timeout
        continue

    detections = net.Detect(img)
    people_counts = {zone: 0 for zone in zones}
    detections_list = []
    for detection in detections:
        if detection.ClassID == 1: 
            for zone, ((start_x, start_y), (end_x, end_y), color) in zones.items():
                if start_x < detection.Center[0] < end_x and start_y < detection.Center[1] < end_y:
                    people_counts[zone] += 1
            detections_list.append((detection.TrackID, time.strftime('%Y-%m-%d %H:%M:%S'), detection.Center[0], detection.Center[1]))

    # Check if one second has passed since last write
    if time.time() - last_written >= 1 and detections_list:
        sql = "INSERT INTO Customers (id, timestamp, x_pos, y_pos) VALUES (%s, %s, %s, %s)"
        with connection.cursor() as cursor:  # Create a new cursor
            # Execute the SQL command for each detection in the list
            cursor.executemany(sql, detections_list)
        connection.commit()  # Commit the transaction
        # Update last_written timestamp
        last_written = time.time()

    for zone, ((start_x, start_y), (end_x, end_y), color) in zones.items():
        cudaDrawRect(img, (start_x, start_y, end_x, end_y), color)

    print(people_counts)
    display.Render(img)
    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))
