import cv2
import os

cam = cv2.VideoCapture(0)
# Force the camera buffer to only hold 1 frame max
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

def snapshot():
    # Flush any leftover frames in the hardware buffer
    for _ in range(4):
        cam.grab()
        
    ret, frame = cam.read()

    if ret:
        os.makedirs("sebbyFrontV2", exist_ok=True)
        file_path = os.path.join("sebbyFrontV2", "snapshot.jpg")
        cv2.imwrite(file_path, frame)
        print(f"SNAPSHOT TAKEN -> {file_path}")
    else:
        print("SCREENSHOT ERROR")