import cv2
import time
import pyautogui

def main():
    # Load the cascade
    # switching to alt2 for better detection stability
    cascade_path = 'haarcascade_frontalface_alt2.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    # Fallback to default if alt2 is missing (though we just copied it)
    if face_cascade.empty():
        print(f"Warning: Could not load {cascade_path}, trying default...")
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            print("Error: Could not load any cascade classifier.")
            return

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    # Low resolution to save memory & CPU
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    # Limit buffer size to minimize lag and memory
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Press 'q' to quit.")

    # Optimization: Scan every 1 second
    last_scan_time = 0
    scan_interval = 1.0  # seconds
    
    # State tracking
    is_user_present = False
    last_faces = []
    
    # Media Control State
    last_seen_time = time.time()
    ABSENT_THRESHOLD = 1.5  # seconds wait before pausing
    media_state = 'playing' # assume media is playing initially or we want it to play

    print("Media Control Active: Open YouTube and focus the window.")
    print(f"Pausing after {ABSENT_THRESHOLD}s of absence.")

    while True:
        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        current_time = time.time()
        
        # Only run detection if interval has passed
        if current_time - last_scan_time > scan_interval:
            last_scan_time = current_time
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces
            # optimized parameters: scaleFactor=1.05 (more thorough), minNeighbors=3 (more sensitive)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
            
            last_faces = faces
            
            if len(faces) > 0:
                last_seen_time = current_time
                if not is_user_present:
                    print("User Present")
                    is_user_present = True
                
                # RESUME if paused
                if media_state == 'paused':
                    print("User returned -> RESUMING")
                    pyautogui.press('k')
                    media_state = 'playing'
            else:
                if is_user_present:
                    print("User Absent (Scanning...)")
                    is_user_present = False

        # Independent check for absence threshold (regardless of scan interval, though linked)
        # It will check every frame or loop iteration to ensure responsiveness once scan updates
        if media_state == 'playing' and (time.time() - last_seen_time > ABSENT_THRESHOLD):
             print(f"User absent for > {ABSENT_THRESHOLD}s -> PAUSING")
             pyautogui.press('k')
             media_state = 'paused'

        # Visual feedback (draw last detected faces)
        # It draw the rectangle from the last scan so it doesn't flicker
        if len(last_faces) > 0:
             for (x, y, w, h) in last_faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Display output
        cv2.imshow('Attention Aware Media', frame)

        # Exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
