import streamlit as st # pyright: ignore[reportMissingImports]
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase # pyright: ignore[reportMissingImports]
import cv2 # pyright: ignore[reportMissingImports]
import mediapipe as mp # pyright: ignore[reportMissingImports]
import numpy as np # pyright: ignore[reportMissingImports]
import pickle
import av # pyright: ignore[reportMissingImports]
import threading
from gtts import gTTS # pyright: ignore[reportMissingImports]
import io 

#page details
st.set_page_config(
    page_title="Sign Language Translator", 
    page_icon="🤘", 
    layout="wide")

#gradient background
page_bg_gradient = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, rgba(232, 245, 252, 0.7), rgba(252, 232, 248, 0.7));
    background-size: cover;
}
</style>
"""
st.markdown(page_bg_gradient, unsafe_allow_html=True)

#styling text
st.markdown("""
    <style>
    h1 { 
        font-size: 5vw !important; 
        text-align: center !important; 
    }
            
    .access { 
        font-size: 2.1vw ! important; 
        text-align: left !important;
    }

    .caption {
        font-size: 1.9vw !important; 
        text-align: left !important;
    }    
    .sentence-box { 
        background-color: white; padding: 20px; border-radius: 10px; 
        border: 2px solid #84fab0; font-size: 24px; min-height: 80px; margin-top: 10px;
    }
            
    @media (max-width: 768px) {
        h1 {
            font-size: 13vw !important;
        }
        .access {
            font-size: 6.5vw !important;
        }
        .caption {
            font-size: 5.5vw !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

if st.button("← Back to Home"):
    st.switch_page("home/app.py")

st.markdown("<h1>Sign Language Translator</h1>", unsafe_allow_html=True)
st.markdown("<p class='access' style='text-align:center;'>This feature requires camera access for real-time translating</p>", unsafe_allow_html=True)
st.markdown("<p class='caption' style='text-align:center;'>Allow camera access to translate Sign Language and communicate with everyone!</p>", unsafe_allow_html=True)

#gtts for saying things out loud
def text_to_speak(text):
    """Converts text to speech using gTTS and returns audio for the widget"""
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp # Return the memory object directly
    except Exception as e:
        st.error(f"Speech Error: {e}")
        return None


#intialize session state
if 'sentence' not in st.session_state:
    st.session_state.sentence = []

#load model pkl file
@st.cache_resource
def load_data():
    with open('asl_model_84.pkl', 'rb') as f:
        data = pickle.load(f)
    return data['model'], data['label_encoder']

model, label_encoder = load_data()

#mediapipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

#normalizing
def normalize_hand(landmarks):
    coords = np.array([[lm.x, lm.y] for lm in landmarks])
    wrist = coords[0]
    centered = coords - wrist
    max_val = np.max(np.abs(centered))
    if max_val == 0: max_val = 1
    return (centered / max_val).flatten()


class ASLProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame_count = 0
        self.last_prediction = "Waiting..."
        self.lock = threading.Lock()

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1
        
        #runs every 3rd frame (keeps things smooth)
        if self.frame_count % 3 == 0:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            res = hands.process(img_rgb)
            
            data_row = np.zeros(84)
            if res.multi_hand_landmarks:
                for i, hand_lms in enumerate(res.multi_hand_landmarks):
                    if i < 2:
                        mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
                        norm_coords = normalize_hand(hand_lms.landmark)
                        data_row[i*42 : (i+1)*42] = norm_coords
                
                try:
                    prediction = model.predict([data_row])
                    decoded = label_encoder.inverse_transform(prediction)[0]
                    with self.lock:
                        self.last_prediction = str(decoded)
                except:
                    pass 
            else:
                with self.lock:
                    self.last_prediction = "No Hand"

        cv2.rectangle(img, (0, 0), (320, 60), (0, 0, 0), -1)
        with self.lock:
            cv2.putText(img, f"Sign: {self.last_prediction}", (10, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

#webrtc camera
ctx = webrtc_streamer(
    key="asl-pro",
    video_processor_factory=ASLProcessor,
    async_processing=True,
    media_stream_constraints={
        "video": {
        "facingMode": "environment"}, 
        "audio": False},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

#sentence buttons
st.write("---")
c1, c2, c3 = st.columns(3)

with c1:
    #adding word/letter
    if st.button("➕ Add Word", use_container_width=True):
        if ctx.video_processor:
            with ctx.video_processor.lock:
                word = ctx.video_processor.last_prediction
            if word not in ["No Hand", "Waiting..."]:
                st.session_state.sentence.append(word)

with c2:
    #backspace
    if st.button("🔙 Delete Last", use_container_width=True):
        if st.session_state.sentence:
            st.session_state.sentence.pop()

with c3:
    #clear everything
    if st.button("🧹 Clear All", use_container_width=True):
        st.session_state.sentence = []

#display
st.markdown("### 📝 Current Sentence:")
sentence_text = " ".join(st.session_state.sentence)
st.markdown(f'<div class="sentence-box">{sentence_text if sentence_text else "Waiting for signs..."}</div>', unsafe_allow_html=True)

st.write("")
if st.button("🔊Read Aloud", type="primary"):
    audio_data = text_to_speak(sentence_text)
    if audio_data:
        st.audio(audio_data, format="audio/mpeg", autoplay=True)#saying text out loud