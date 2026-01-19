#MEDIAPIPE

import streamlit as st # pyright: ignore[reportMissingImports]
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase # pyright: ignore[reportMissingImports]
import cv2 # pyright: ignore[reportMissingImports]
import mediapipe as mp # pyright: ignore[reportMissingImports]
import numpy as np # pyright: ignore[reportMissingImports]
import pickle
import av # pyright: ignore[reportMissingImports]

st.set_page_config(
    page_title="Sign Language Translator",
    page_icon="🤘",
    layout="wide"
)


page_bg_gradient = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, rgba(232, 245, 252, 0.7), rgba(252, 232, 248, 0.7));
    background-size: cover;
}
</style>
"""
st.markdown(page_bg_gradient, unsafe_allow_html=True)

if st.button("← Back to Home"):
    st.switch_page("app.py")

#styling the text
st.markdown("""
    <style>
    h1 {
        font-size: 5vw !important;
        text-align: center !important;    
    }
    
    .access {
        font-size: 2.1vw ! important;
    }
    .caption {
        font-size: 1.9vw !important;
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

    """            
, unsafe_allow_html=True)

#actual text
st.markdown("<h1>Sign Language Translator</h1>", unsafe_allow_html=True)
st.markdown("<p class='access'>This feature requires camera access for real-time translating</p>", unsafe_allow_html=True)
st.markdown("<p class='caption'>Allow camera access to translate ASL and communicate with everyone!</p>", unsafe_allow_html=True)

# 1. Load the "Brain"
with open('asl_model_84.pkl', 'rb') as f:
    model_data = pickle.load(f)
    model = model_data['model']
    label_encoder = model_data['label_encoder']

# 2. Setup MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

def normalize_hand(landmarks):
    coords = np.array([[lm.x, lm.y] for lm in landmarks])
    wrist = coords[0]
    centered = coords - wrist
    max_val = np.max(np.abs(centered))
    if max_val == 0: max_val = 1
    return (centered / max_val).flatten()

# 3. Modern Processor (using recv and VideoProcessorBase)
class ASLProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame_count = 0
        self.last_prediction = "Waiting..."

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1
        
        # Mirror for natural user interaction
        #img = cv2.flip(img, 1)
        
        # TURBO STRATEGY: Only run heavy AI every 2nd frame
        if self.frame_count % 2 == 0:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            res = hands.process(img_rgb)
            
            data_row = np.zeros(84)
            if res.multi_hand_landmarks:
                for i, hand_lms in enumerate(res.multi_hand_landmarks):
                    if i < 2:
                        mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
                        norm_coords = normalize_hand(hand_lms.landmark)
                        data_row[i*42 : (i+1)*42] = norm_coords
                
                prediction = model.predict([data_row])
                self.last_prediction = label_encoder.inverse_transform(prediction)[0]
            else:
                self.last_prediction = "No Hand"

        # UI Overlay: Black box and Green text for high visibility
        cv2.rectangle(img, (0, 0), (280, 60), (0, 0, 0), -1)
        cv2.putText(img, f"Sign: {self.last_prediction}", (10, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")




# Use the processor_factory instead of video_transformer_factory
webrtc_streamer(
    key="asl-pro",
    video_processor_factory=ASLProcessor,
    # This forces the back camera and mutes the mic
    media_stream_constraints={
        "video": {
            "facingMode": "environment",  # "user" for front, "environment" for back
        },
        "audio": False
    },
    rtc_configuration={ 
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
)
