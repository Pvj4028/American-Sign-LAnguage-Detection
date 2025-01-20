import socket
import cv2
from cvzone.HandTrackingModule import HandDetector
from cvzone.ClassificationModule import Classifier
import numpy as np
import math
import threading
cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1)
classifier = Classifier(r"C:\Users\Pavan\Downloads\project\keras_model.h5", r"C:\Users\Pavan\Downloads\project\labels.txt")

offset = 20
imgSize = 256
detected_string = ""  
save_flag = False  # To prevent multiple saves for the same key press

labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

# Server setup
HOST ='192.168.1.16' 
PORT = 8080

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server listening on port {PORT}")

def accept_connection():
    try:
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")
        return conn
    except Exception as e:
        print(f"Error accepting connection: {e}")
        return None

def handle_client(conn):
    global detected_string, save_flag
    try:
        while True:
            # Non-blocking receive with a small timeout
            conn.settimeout(0.1)
            try:
                data = conn.recv(1024)  # Receive up to 1024 bytes
                if data:
                    received_message = data.decode()
                    print(f"Received from client: {received_message}")
            except socket.timeout:
                pass  # No data received; continue processing

            success, img = cap.read()
            if not success:
                break

            imgOutput = img.copy()
            hands, img = detector.findHands(img, draw=True)

            if hands:
                hand = hands[0]  # Single hand detection
                x, y, w, h = hand['bbox']

                # Adjust bounding box to avoid slicing errors
                y1, y2 = max(0, y - offset), min(img.shape[0], y + h + offset)
                x1, x2 = max(0, x - offset), min(img.shape[1], x + w + offset)
                imgCrop = img[y1:y2, x1:x2]

                if imgCrop.size != 0:
                    imgWhite = np.ones((imgSize, imgSize, 3), np.uint8) * 255
                    aspectRatio = h / w

                    if aspectRatio > 1:  # Height > Width
                        k = imgSize / h
                        wCal = math.ceil(k * w)
                        imgResize = cv2.resize(imgCrop, (wCal, imgSize))
                        wGap = math.ceil((imgSize - wCal) / 2)
                        imgWhite[:, wGap:wGap + wCal] = imgResize
                    else:  # Width >= Height
                        k = imgSize / w
                        hCal = math.ceil(k * h)
                        imgResize = cv2.resize(imgCrop, (imgSize, hCal))
                        hGap = math.ceil((imgSize - hCal) / 2)
                        imgWhite[hGap:hGap + hCal, :] = imgResize

                    prediction, index = classifier.getPrediction(imgWhite, draw=True)
                    detected_letter = labels[index]

                    # Draw on output image
                    cv2.rectangle(imgOutput, (x - offset, y - offset - 50),
                                  (x - offset + 90, y - offset - 50 + 50), (150, 200, 150), cv2.FILLED)
                    cv2.putText(imgOutput, detected_letter, (x, y - 26),
                                cv2.FONT_HERSHEY_COMPLEX, 1.7, (255, 255, 255), 2)
                    cv2.rectangle(imgOutput, (x - offset, y - offset),
                                  (x + w + offset, y + h + offset), (150, 200, 150), 4)

            cv2.imshow("Hand Gesture Recognition", imgOutput)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):  # Save on 's' key press
                if not save_flag:  # Save only if the flag is False
                    detected_string += detected_letter
                    print(f"Saved letter: {detected_letter}")
                    save_flag = True  # Set flag to prevent multiple saves
            else:
                save_flag = False  # Reset flag when 's' is not pressed

            if key == 13:  # Enter key
                if detected_string:
                    # Send the detected string to the client
                    try:
                        conn.sendall(detected_string.encode())  # Just send the data
                        print(f"Sent to client: {detected_string}")
                    except (BrokenPipeError, ConnectionResetError) as e:
                        print(f"Error while sending data to client: {e}")
                        break
                    # Clear the detected string after sending
                    detected_string = ""
            elif key == ord(' '):
                detected_string += " "
            elif key == ord('q'):  # Quit on 'q'
                break
    except Exception as e:
        print(f"Error in client handling: {e}")
    finally:
        conn.close()
        cap.release()
        cv2.destroyAllWindows()

# Accept and handle client connections
def run_server():
    while True:
        conn = accept_connection()
        if conn:
            # Start handling the client connection in a separate thread
            client_thread = threading.Thread(target=handle_client, args=(conn,))
            client_thread.start()
            client_thread.join()  # Wait for the client thread to finish

run_server()
