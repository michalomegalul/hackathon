import cv2
import numpy as np
import mysql.connector
import time
from collections import deque
import datetime

def create_heatmap(gray_image, coords, radius=10, intensity=8, blur_size=30, normalize=True):
    heatmap = np.zeros_like(gray_image, np.float32)
    for x, y, _ in coords:
        cv2.circle(heatmap, (x, y), radius, intensity, -1)
    heatmap = cv2.GaussianBlur(heatmap, (0, 0), blur_size)
    if normalize:
        heatmap /= np.max(heatmap)
    return heatmap

def get_coordinates_from_db(db_connection):
    cursor = db_connection.cursor()
    #cursor2 = db_connection.cursor2()
    #cursor2.execute(query2)
    #result2 = cursor.fetchone()
    #query2 = "SELECT timestamp FROM Customers"
    query = f'''
    SELECT x_pos, y_pos, timestamp
    FROM Customers
    WHERE timestamp= (SELECT MAX(timestamp) FROM Customers)
    '''
    #print(result2)

    print((datetime.datetime.now()).strftime("%Y-%m-%d-%H:%M:%S"))
    cursor.execute(query)
    result = cursor.fetchall()
    print(result)
    # if result:
    #     new_coords = [(result[0], result[1], result[2])]
    #     max_timestamp = result[2]
    # else:
    #     new_coords = []
    #     max_timestamp = last_max_timestamp

    cursor.close()
    return result

def main():
    # Load an image
    image = cv2.imread('PXL_20230626_115014611.jpg')
    image_resize = cv2.resize(image, (1080, 720))
    num_dots_to_show = 30
    existing_coords = deque(maxlen=num_dots_to_show)

    gray_image = cv2.cvtColor(image_resize, cv2.COLOR_BGR2GRAY)


    while True:
        # Reconnect to the database
        db_connection = mysql.connector.connect(
            host="192.168.1.176",
            user="uzivatel",
            password="ABCabc123",
            database="Customers"
        )

        new_coords = get_coordinates_from_db(db_connection)

        if len(new_coords) == 0:
            print("No new data")
            if cv2.waitKey(1000) & 0xFF == ord('q'):
                break
        else:
            print(new_coords)

            existing_coords.extend(new_coords)

            coords = list(existing_coords)

            heatmap = create_heatmap(gray_image, coords, radius=20, intensity=16, blur_size=30)
            colored_heatmap = cv2.applyColorMap((heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET)

            weighted_image = cv2.addWeighted(image_resize, 0.7, colored_heatmap, 0.3, 0)

            cv2.imshow('Image with Heatmap Overlay', weighted_image)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Close the database connection and add a delay before the next iteration
        db_connection.close()
        time.sleep(1)

    cv2.destroyAllWindows()
    db_connection.close()

if __name__ == '__main__':
    main()