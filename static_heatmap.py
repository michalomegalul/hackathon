import cv2
import numpy as np
import mysql.connector
import time
from collections import deque 
import multiprocessing

def create_heatmap(gray_image, coords, radius=3, intensity=8, blur_size=30, normalize=True):
    heatmap = np.zeros_like(gray_image, np.float32)
    for x, y, _ in coords:
        cv2.circle(heatmap, (x, y), radius, intensity, -1)
    heatmap = cv2.GaussianBlur(heatmap, (0, 0), blur_size)
    if normalize:
        heatmap /= np.max(heatmap)
    return heatmap

def get_coordinates_from_db(db_connection):
    cursor = db_connection.cursor()
    query = f'''
    SELECT x_pos, y_pos, timestamp
    FROM Customers
    '''
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

def process_image(image, coords):
    image_resize = cv2.resize(image, (1270, 960))
    gray_image = cv2.cvtColor(image_resize, cv2.COLOR_BGR2GRAY)
    heatmap = create_heatmap(gray_image, coords, radius=20, intensity=16, blur_size=30)
    colored_heatmap = cv2.applyColorMap((heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET)
    weighted_image = cv2.addWeighted(image_resize, 0.7, colored_heatmap, 0.3, 0)
    cv2.imshow('Image with Heatmap Overlay', weighted_image)
    cv2.waitKey(1)

def image_processing_worker(image_queue, coords_queue):
    while True:
        image = image_queue.get()
        if image is None:
            break
        coords = coords_queue.get()
        process_image(image, coords)

def main():
    # Load an image
    image = cv2.imread('Screenshot 2023-01-26 103620.png')
    image_resize = cv2.resize(image, (1080, 720))
    existing_coords = []

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
            if cv2.waitKey(1000) & 0xFF == ord('q'):
                break
        else:
            existing_coords += new_coords

            coords = list(existing_coords)

            heatmap = create_heatmap(gray_image, coords, radius=3, intensity=16, blur_size=30)
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
