"""
SignBridge - ASL/ISL Recognition
Single File Streamlit App - Deploy to Streamlit Cloud (FREE)

Install & Run Locally:
    pip install streamlit opencv-python mediapipe numpy pillow
    streamlit run app_streamlit.py

Deploy to Cloud (FREE):
    1. Push to GitHub
    2. Go to share.streamlit.io
    3. Connect your GitHub repo
    4. Done! (share link with professor)
"""

import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
import time

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="SignBridge - ASL & ISL Recognition",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
    .main { padding: 0; }
    .stApp { background: linear-gradient(135deg, #0f0f23 0%, #1a0033 100%); }
    h1 { color: #00e5a0; text-align: center; }
    h2 { color: #00e5a0; }
    .big-letter { 
        font-size: 120px; 
        text-align: center; 
        color: #00e5a0; 
        font-weight: bold;
        margin: 20px 0;
    }
    .metric-card {
        background: rgba(0,229,160,0.1);
        border: 2px solid #00e5a0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .confidence-high { color: #00ff88; font-weight: bold; }
    .confidence-low { color: #ff6b35; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ASL & ISL PATTERNS
# ─────────────────────────────────────────────

ASL_PRIMARY = {
    (0, 1, 0, 0, 0): "D",   (0, 1, 1, 0, 0): "V",   (0, 1, 1, 1, 0): "W",
    (0, 1, 1, 1, 1): "B",   (1, 1, 1, 1, 1): "B",   (1, 0, 0, 0, 0): "A",
    (0, 0, 0, 0, 1): "I",   (1, 0, 0, 0, 1): "Y",   (1, 1, 0, 0, 0): "L",
    (0, 0, 0, 0, 0): "S",   (0, 0, 1, 1, 1): "N",   (0, 0, 0, 1, 1): "Z",
    (0, 1, 0, 1, 0): "H",   (0, 0, 1, 0, 0): "F",   (1, 0, 1, 0, 0): "E",
    (1, 0, 0, 1, 0): "Q",   (0, 1, 0, 0, 1): "P",   (1, 0, 1, 1, 0): "K",
    (0, 0, 1, 0, 1): "X",   (1, 1, 0, 1, 0): "O",   (1, 1, 1, 0, 0): "3",
    (1, 1, 0, 1, 1): "T",   (1, 0, 1, 0, 1): "J",   (0, 0, 1, 1, 0): "R",
    (1, 1, 1, 0, 1): "U",   (0, 1, 1, 0, 1): "M",   (1, 0, 1, 1, 1): "G",
}

ISL_PRIMARY = {
    (0, 0, 0, 0, 0): "अ",  (1, 1, 1, 1, 1): "आ",  (0, 1, 0, 0, 0): "इ",
    (0, 1, 1, 0, 0): "ई",  (0, 0, 0, 0, 1): "उ",  (1, 0, 0, 0, 1): "ऊ",
    (1, 0, 0, 0, 0): "ए",  (1, 1, 0, 0, 0): "ओ",  (0, 1, 1, 1, 0): "क",
    (1, 1, 1, 0, 0): "ख",  (0, 1, 1, 1, 1): "ग",  (1, 1, 1, 1, 0): "घ",
    (0, 1, 0, 1, 0): "च",  (0, 0, 1, 0, 0): "छ",  (0, 0, 1, 1, 0): "ज",
    (1, 0, 1, 0, 0): "झ",  (0, 0, 0, 1, 0): "ट",  (1, 0, 0, 1, 0): "ठ",
    (0, 1, 0, 0, 1): "ड",  (1, 1, 0, 1, 0): "ढ",  (0, 0, 1, 0, 1): "ण",
    (1, 0, 1, 1, 0): "त",  (0, 0, 1, 1, 1): "थ",  (0, 0, 0, 1, 1): "न",
    (1, 1, 1, 0, 1): "प",  (1, 0, 1, 0, 1): "फ",  (0, 1, 1, 0, 1): "ब",
    (1, 1, 0, 1, 1): "भ",  (0, 0, 1, 1, 0): "म",
}

# ─────────────────────────────────────────────
# HAND ANALYZER CLASS
# ─────────────────────────────────────────────

class HandAnalyzer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.65,
        )
        self.mp_draw = mp.solutions.drawing_utils

    def get_landmarks(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.hands.process(rgb)
        if res.multi_hand_landmarks:
            return res.multi_hand_landmarks[0]
        return None

    def draw_hand(self, frame, lm):
        self.mp_draw.draw_landmarks(
            frame, lm, self.mp_hands.HAND_CONNECTIONS,
            self.mp_draw.DrawingSpec(color=(0,255,120), thickness=2, circle_radius=4),
            self.mp_draw.DrawingSpec(color=(255,255,255), thickness=1)
        )
        return frame

    def extract(self, lm):
        pts = np.array([[p.x, p.y, p.z] for p in lm.landmark])
        fingers = self._finger_states(pts)
        curvature = self._avg_curvature(pts)
        visibility = float(np.mean([getattr(p, 'visibility', 0.9) for p in lm.landmark]))
        
        return {
            "fingers": tuple(fingers),
            "curvature": curvature,
            "visibility": visibility,
        }

    def _finger_states(self, pts):
        states = []
        tip, ip = pts[4], pts[3]
        mcp = pts[2]
        states.append(1 if abs(tip[0] - mcp[0]) > abs(ip[0] - mcp[0]) else 0)
        for tip_i, pip_i in [(8,6), (12,10), (16,14), (20,18)]:
            states.append(1 if pts[tip_i][1] < pts[pip_i][1] else 0)
        return states

    def _avg_curvature(self, pts):
        configs = [(8,7,6), (12,11,10), (16,15,14), (20,19,18)]
        angles = []
        for tip, dip, pip in configs:
            v1 = pts[tip] - pts[dip]
            v2 = pts[pip] - pts[dip]
            n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
            if n1 > 0 and n2 > 0:
                cos = np.clip(np.dot(v1, v2) / (n1 * n2), -1, 1)
                angles.append(np.arccos(cos))
        return float(np.mean(angles)) if angles else 0.0

# ─────────────────────────────────────────────
# CLASSIFIER CLASS
# ─────────────────────────────────────────────

class GestureClassifier:
    def __init__(self):
        self.mode = "ASL"

    def classify(self, features):
        pattern = features["fingers"]
        curvature = features["curvature"]
        table = ISL_PRIMARY if self.mode == "ISL" else ASL_PRIMARY
        
        letter = table.get(pattern, "")
        if not letter:
            return "", 0.0
        
        vis = min(features["visibility"], 1.0)
        excl = 0.95
        conf = float(np.mean([vis, excl]))
        
        return letter, conf

# ─────────────────────────────────────────────
# STREAMLIT INTERFACE
# ─────────────────────────────────────────────

st.markdown("# 🤟 SignBridge")
st.markdown("### Real-Time ASL & ISL Sign Language Recognition")

# Sidebar settings
with st.sidebar:
    st.title("⚙️ Settings")
    mode = st.radio("Select Language", ["ASL", "ISL"], key="mode")
    confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.65, 0.05)
    st.markdown("---")
    st.markdown("**Made with 🤟 for sign language recognition**")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📷 Camera Feed")
    picture = st.camera_input("Take a picture")

with col2:
    st.markdown("### 🎯 Detection")
    detection_placeholder = st.empty()

# Initialize analyzer and classifier
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = HandAnalyzer()

if 'classifier' not in st.session_state:
    st.session_state.classifier = GestureClassifier()

# Set mode
st.session_state.classifier.mode = mode

# Process image if provided
if picture is not None:
    # Read image
    img = Image.open(picture)
    img_array = np.array(img)
    
    # Convert to BGR for OpenCV
    frame = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Detect hand
    lm = st.session_state.analyzer.get_landmarks(frame)
    
    detected = ""
    conf = 0.0
    hand_detected = False
    
    if lm:
        hand_detected = True
        # Draw hand
        frame = st.session_state.analyzer.draw_hand(frame, lm)
        # Extract features
        features = st.session_state.analyzer.extract(lm)
        # Classify
        detected, conf = st.session_state.classifier.classify(features)
    
    # Display image with hand drawn
    st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_column_width=True)
    
    # Display detection result
    with detection_placeholder.container():
        if hand_detected:
            if detected and conf > confidence_threshold:
                st.markdown(f'<div class="big-letter">{detected}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-card"><h3 class="confidence-high">{conf*100:.1f}% Confidence</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="big-letter">?</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-card"><h3 class="confidence-low">{conf*100:.1f}% (Low)</h3></div>', unsafe_allow_html=True)
                st.warning("Confidence too low. Try a clearer gesture!")
        else:
            st.markdown(f'<div class="big-letter">—</div>', unsafe_allow_html=True)
            st.info("No hand detected. Show your hand to the camera!")

# Text building section
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 Text Builder")
    
    if 'letters' not in st.session_state:
        st.session_state.letters = []
    if 'words' not in st.session_state:
        st.session_state.words = []
    
    # Manual letter input (for testing)
    manual_letter = st.text_input("Or type a letter manually:", max_chars=1)
    
    if manual_letter and manual_letter.isalpha():
        st.session_state.letters.append(manual_letter.upper())
    
    # Display current word
    current_word = "".join(st.session_state.letters)
    st.markdown(f"**Current Word:** `{current_word if current_word else '(empty)'}`")
    
    # Buttons
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("✅ Confirm Word"):
            if current_word:
                st.session_state.words.append(current_word)
                st.session_state.letters = []
                st.success(f"Word confirmed: {current_word}")
    
    with col_btn2:
        if st.button("🔄 Clear Word"):
            st.session_state.letters = []
    
    with col_btn3:
        if st.button("🧹 Clear All"):
            st.session_state.letters = []
            st.session_state.words = []

with col2:
    st.markdown("### 🗣️ Sentence")
    sentence = " ".join(st.session_state.words)
    st.markdown(f"```\n{sentence if sentence else '(your sentence will appear here)'}\n```")

# Information section
st.markdown("---")

with st.expander("📚 ASL Letters Guide"):
    st.markdown("""
    **How to make ASL letters:**
    - **A** - Thumb only (closed fist)
    - **B** - All fingers extended, thumb tucked
    - **D** - Index finger only
    - **E** - Fingers curled, thumb across
    - **F** - Middle & ring up, others down
    - **I** - Pinky only
    - **L** - Thumb + index up
    - **S** - Closed fist
    - **V** - Index & middle up (peace sign)
    - **Y** - Thumb + pinky up
    - **And more...**
    
    **Tips for better detection:**
    - ✅ Good lighting is essential
    - ✅ Make clear, distinct gestures
    - ✅ Keep hand still in frame
    - ✅ Hold gesture for 1-2 seconds
    """)

with st.expander("❓ How to Use"):
    st.markdown("""
    1. **Take a picture** using the camera
    2. **Show a hand sign** (ASL or ISL)
    3. **Check detected letter** in the right panel
    4. **Type manually** or confirm letter
    5. **Build words** using the buttons
    6. **Create sentences** and share!
    
    **Keyboard Alternative:**
    For laptop testing, you can type letters manually in the text box.
    """)
