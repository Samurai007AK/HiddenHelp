import customtkinter as ctk
import cv2
from PIL import Image
import threading
import time
import pyautogui

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AttentionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Attention Aware Media Control")
        self.geometry("800x600")
import customtkinter as ctk
import cv2
from PIL import Image
import threading
import time
import pyautogui

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AttentionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Attention Aware Media Control")
        self.geometry("800x600")

        # Layout
        self.grid_columnconfigure(0, weight=3) # Video area
        self.grid_columnconfigure(1, weight=1) # Controls area
        self.grid_rowconfigure(0, weight=1)

        # Threading & State
        self.stop_event = threading.Event()
        self.thread = None
        self.lock = threading.Lock()
        
        # Shared Data
        self.current_image = None
        self.status_data = {
            "text": "STOPPED",
            "color": "gray",
            "progress": 0.0,
            "media": "IDLE",
            "media_color": "gray"
        }

        # UI Components
        self.setup_ui()
        
        # Auto-start
        self.after(500, self.start_camera_thread)
        self.after(100, self.update_ui_loop)

    def setup_ui(self):
        # Left Side - Video Feed
        self.video_frame = ctk.CTkFrame(self, corner_radius=0)
        self.video_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="Initializing...")
        self.video_label.pack(expand=True, fill="both")

        # Right Side - Controls
        self.control_frame = ctk.CTkFrame(self, corner_radius=0)
        self.control_frame.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=10)

        # Status Label
        self.status_label = ctk.CTkLabel(self.control_frame, text="Status: STOPPED", font=("Arial", 20, "bold"))
        self.status_label.pack(pady=20)

        # Media State Label
        self.media_label = ctk.CTkLabel(self.control_frame, text="Media: IDLE", text_color="gray")
        self.media_label.pack(pady=10)

        # Detection Indicator
        self.detection_indicator = ctk.CTkProgressBar(self.control_frame, width=150)
        self.detection_indicator.set(0)
        self.detection_indicator.pack(pady=10)

        # Controls
        self.btn_toggle = ctk.CTkButton(self.control_frame, text="Start Camera", command=self.toggle_camera)
        self.btn_toggle.pack(pady=50)

        self.btn_quit = ctk.CTkButton(self.control_frame, text="Quit App", fg_color="red", hover_color="darkred", command=self.on_close)
        self.btn_quit.pack(side="bottom", pady=20)
        
        # Instructions
        self.info_text = ctk.CTkTextbox(self.control_frame, height=150)
        self.info_text.insert("0.0", "Instructions:\n\n1. Open YouTube/Media.\n2. Ensure this app is running.\n3. Detection runs in background.\n4. If absent > 2.5s, media pauses (Spacebar).\n\nPress 'Quit App' to exit safely.")
        self.info_text.configure(state="disabled")
        self.info_text.pack(side="bottom", pady=10, padx=10)

    def start_camera_thread(self):
        if self.thread and self.thread.is_alive():
            return
            
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.camera_task, daemon=True)
        self.thread.start()
        self.btn_toggle.configure(text="Stop Camera")

    def stop_camera_thread(self):
        self.stop_event.set()
        self.btn_toggle.configure(text="Stopping...")
        # We don't join() here to avoid freezing UI waiting for thread. 
        # UI loop will detect stop.

    def toggle_camera(self):
        if self.thread and self.thread.is_alive():
            self.stop_camera_thread()
        else:
            self.start_camera_thread()

    def camera_task(self):
        """
        Runs completely in background. 
        Mimics main.py logic.
        """
        print("[Thread] Starting Camera...")
        # Use DirectShow (CAP_DSHOW) to avoid hanging on Windows
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        # Optimizations
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            print("[Thread] Failed to open camera")
            with self.lock:
                self.status_data["text"] = "Camera Error"
                self.status_data["color"] = "red"
            return

        # Load Cascade
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
        if face_cascade.empty():
            face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

        # Logic Variables
        last_scan_time = 0
        scan_interval = 1.0
        is_user_present = False
        last_faces = []
        
        last_seen_time = time.time()
        ABSENT_THRESHOLD = 2.5
        media_state = 'playing'

        # Main Loop inside Thread
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # Mirror
            frame = cv2.flip(frame, 1)

            # --- Detection Logic ---
            current_time = time.time()
            if current_time - last_scan_time > scan_interval:
                last_scan_time = current_time
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                last_faces = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30)
                )
                
                if len(last_faces) > 0:
                    last_seen_time = current_time
                    if not is_user_present:
                        is_user_present = True
                        with self.lock:
                            self.status_data.update({"text": "User Present", "color": "green", "progress": 1.0})
                    
                    if media_state == 'paused':
                        try:
                            pyautogui.press('space')
                            media_state = 'playing'
                            with self.lock:
                                self.status_data.update({"media": "PLAYING", "media_color": "green"})
                        except: pass
                else:
                    if is_user_present:
                        is_user_present = False
                        with self.lock:
                            self.status_data.update({"text": "Checking...", "color": "orange", "progress": 0.5})

            # Media Check
            if media_state == 'playing' and (time.time() - last_seen_time > ABSENT_THRESHOLD):
                try:
                    pyautogui.press('space')
                    media_state = 'paused'
                    with self.lock:
                        self.status_data.update({
                            "media": "PAUSED", "media_color": "red",
                            "text": "User Absent", "color": "red", "progress": 0.0
                        })
                except: pass

            # --- Visualization ---
            for (x, y, w, h) in last_faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Convert to CTkImage HERE (in thread) to save UI time?
            # Actually, creating CTkImage requires a tk master, safer to send PIL image.
            resized = cv2.resize(frame, (640, 480))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb)
            
            with self.lock:
                self.current_image = pil_image

            # Throttle slightly
            time.sleep(0.01)

        # Cleanup
        print("[Thread] Releasing Camera...")
        cap.release()
        with self.lock:
            self.status_data["text"] = "STOPPED"
            self.status_data["color"] = "gray"

    def update_ui_loop(self):
        # 1. Update Image
        with self.lock:
            if self.current_image:
                # CTkImage creation must stay on main thread usually
                ctk_img = ctk.CTkImage(light_image=self.current_image, dark_image=self.current_image, size=(640, 480))
                self.video_label.configure(image=ctk_img, text="")
                self.video_label.image = ctk_img # Keep ref
                self.current_image = None # Consumed

            # 2. Update Text
            d = self.status_data
            self.status_label.configure(text=f"Status: {d['text']}", text_color=d['color'])
            self.detection_indicator.set(d['progress'])
            self.media_label.configure(text=f"Media: {d['media']}", text_color=d['media_color'])

        # 3. Check Thread State
        if self.thread and not self.thread.is_alive():
            self.btn_toggle.configure(text="Start Camera")
        
        self.after(30, self.update_ui_loop)

    def on_close(self):
        self.stop_camera_thread()
        self.destroy()

if __name__ == "__main__":
    app = AttentionApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
