import cv2
import os

cam = cv2.VideoCapture(0)

def snapshot():
    ret, frame = cam.read()

    if ret:
        # is it a thing
        os.makedirs("sebby", exist_ok=True)

        # make path
        file_path = os.path.join("sebby", "snapshot.jpg")

        cv2.imwrite(file_path, frame)
        print(f"SNAPSHOT TAKEN -> {file_path}")

    else:
        print("SCREENSHOT ERROR")