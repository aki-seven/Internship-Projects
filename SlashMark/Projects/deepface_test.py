import cv2
import time
from deepface import DeepFace
import mediapipe as mp

reference_img_path = 'my_face.jpg'

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Press 'q' to quit.")

# ---------------- CONFIG ----------------
max_attempts = 100
attempts = 0
verify_count = 0
verify_threshold = 3
distance_threshold = 0.4

# rate limiting
cooldown = 2
last_attempt_time = 0
lockout_time = None
lockout_duration = 30

# anti-spoof
prev_gray = None
motion_threshold = 2000  # FIXED (less aggressive)

# ----------------------------------------

def perform_login():
    print("Face recognized. Logging in...")
    cap.release()
    cv2.destroyAllWindows()

def prompt_password_login():
    print("Switching to password login...")

# ---------------- LIVENESS ----------------
def is_blinking(landmarks, w, h):
    left_eye = [33, 160, 158, 133, 153, 144]

    pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in left_eye]

    vertical = abs(pts[1][1] - pts[5][1])
    horizontal = abs(pts[0][0] - pts[3][0])

    if horizontal == 0:
        return False

    ratio = vertical / horizontal
    return ratio < 0.2

def check_liveness(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            if is_blinking(face_landmarks.landmark, frame.shape[1], frame.shape[0]):
                return True
    return False

# ---------------- ANTI-SPOOF ----------------
def check_motion(gray):
    global prev_gray

    if prev_gray is None:
        prev_gray = gray
        return True

    diff = cv2.absdiff(prev_gray, gray)
    motion = diff.sum()
    prev_gray = gray

    return motion > motion_threshold

# ---------------- RATE LIMIT ----------------
def rate_limit():
    global last_attempt_time, lockout_time

    current_time = time.time()

    if lockout_time:
        if current_time - lockout_time < lockout_duration:
            print("Locked out...")
            return False
        else:
            lockout_time = None

    if current_time - last_attempt_time < cooldown:
        print("Rate limited...")
        return False

    last_attempt_time = current_time
    return True

# ---------------- MAIN LOOP ----------------
while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to capture image")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # rate limiting
    if not rate_limit():
        cv2.imshow('Video', frame)
        continue

    # anti-spoof (motion)
    if not check_motion(gray):
        print("Low motion detected (possible spoof)")
        cv2.imshow('Video', frame)
        continue

    # detect faces FIRST (FIXED ORDER)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )

    face_recognized = False

    for (x, y, w, h) in faces:
        face_region = frame[y:y+h, x:x+w]

        # liveness INSIDE face loop (FIXED)
        if not check_liveness(frame):
            print("Blink required...")
            continue

        try:
            result = DeepFace.verify(face_region, reference_img_path)

            if result["verified"] and result["distance"] < distance_threshold:
                verify_count += 1
                attempts = 0  # FIXED: reset attempts on success

                print(f"Verified {verify_count}/{verify_threshold}")

                if verify_count >= verify_threshold:
                    face_recognized = True
                    break
            else:
                verify_count = 0

        except Exception as e:
            print(f"Error: {e}")

        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

    cv2.imshow('Video', frame)

    # FIXED: only increment if face was detected but failed
    if len(faces) > 0 and not face_recognized:
        attempts += 1

        if attempts >= max_attempts:
            lockout_time = time.time()
            print("Too many attempts. Locked out.")
            prompt_password_login()
            break

    if face_recognized:
        perform_login()
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()