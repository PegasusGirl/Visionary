#MEDIAPIPE

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
import whisper
import base64
import streamlit.components.v1 as components
import time


#page details
st.set_page_config(
    page_title="Sign Language Translator", 
    page_icon="🤘", 
    layout="wide")


#all session states
if 'whisper_model' not in st.session_state:
    st.session_state.whisper_model = whisper.load_model("base")
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "camera_running" not in st.session_state:
    st.session_state.camera_running = False
if 'sentence' not in st.session_state:
    st.session_state.sentence = []
if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = None


#audios
@st.cache_data
def speak_audio(text):
    try:
        tts = gTTS(text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return base64.b64encode(fp.read()).decode()
    except Exception as e:
        return ""

def play_audio(audio_data, element_id="visionary-audio"):
    """Global audio player that attempts immediate playback."""
    components.html(f"""
        <script>
            var parentDoc = window.parent.document;
            var audio = parentDoc.getElementById('{element_id}'); 
            
            if (!audio) {{
                audio = parentDoc.createElement('audio');
                audio.id = '{element_id}';
                audio.style.display = 'none';
                parentDoc.body.appendChild(audio);
            }}
            
            audio.src = 'data:audio/mpeg;base64,{audio_data}';
            audio.currentTime = 0;
            
            audio.play().catch(e => {{
                console.log("Autoplay blocked, waiting for interaction:", e);
                parentDoc.addEventListener('click', () => audio.play(), {{once: true}});
            }});
        </script>
    """, height=0, width=0)

def queue_audio(text):
    """Adds text to the queue to be played by the Global Speaker at the end of the script."""
    if text:
        st.session_state.audio_queue = text

#overlaying button and welcome audio
if not st.session_state.unlocked:
    welcome_text = "Sign Language Translator. This feature requires camera access for real-time translating. Allow camera access to translate Sign Language and communicate with everyone. Click the red start button to begin translation."
    audio_data = speak_audio(welcome_text)
    
    if audio_data:
        play_audio(audio_data, "welcome-id")

    st.markdown("""
        <style>
        div[data-testid="stElementToolbar"] + div:has(button[aria-label="gate_button"]),
        .element-container:has(#gate_button_marker) + .element-container button {
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            z-index: 9999;
            background-color: rgba(205, 242, 247, 0.25) !important;
            cursor: pointer;
            border: none;
        }
        </style>
        <div id="gate_button_marker"></div>
    """, unsafe_allow_html=True)

    if st.button(" ", key="gate_button", help="Click anywhere to unlock"):
        st.session_state.unlocked = True
        st.rerun()

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

#styling text voice-activ. microp.
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
        background-color: white; 
        padding: 20px; border-radius: 10px; 
        border: 2px solid #84fab0; 
        font-size: 24px; 
        min-height: 80px; 
        margin-top: 10px;
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
            
    /* voice-powered microp. */
    [data-testid="stAudioInput"] {
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 50% !important;
        max-width: 400px;
        z-index: 10001;
        background: white !important;
        border-radius: 50px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
        pointer-events: auto !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 5px 20px !important; 
        height: 80px !important;      
    }
    [data-testid="stAudioInput"] > div {
        background-color: transparent !important; 
        border: none !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }
    [data-testid="stAudioInput"] button[aria-label="Record"] {
        background-color: #FF0000 !important;
        color: white !important;
        border-radius: 50% !important;
        margin: 0 auto !important; 
        width: 60px !important;
        height: 60px !important;
        transition: transform 0.2s ease !important;
    }
    [data-testid="stAudioInput"] button svg {
        transform: scale(1.8) !important; 
    }
            
    [data-testid="stAudioInput"] button svg:hover {
            transform: scale(2) !important;
    }   

    [data-testid="stAudioInput"] button[aria-label="Stop recording"] {
        background-color: #FF0000 !important;
        color: white !important;
        border-radius: 50% !important;
        width: 60px !important;
        height: 60px !important;
        transition: transform 0.2s ease !important;
    }    
    [data-testid="stAudioInput"] label {
        display: none !important;
    }
    
    </style>
    """, unsafe_allow_html=True)

if st.button("← Back to Home"):
    st.switch_page("home/app.py")

st.markdown("<h1>Sign Language Translator</h1>", unsafe_allow_html=True)
st.markdown("<p class='access' style='text-align:center;'>This feature requires camera access for real-time translating</p>", unsafe_allow_html=True)
st.markdown("<p class='caption' style='text-align:center;'>Allow camera access to translate Sign Language and communicate with everyone!</p>", unsafe_allow_html=True)

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
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    desired_playing_state=st.session_state.camera_running,
)


if st.session_state.camera_running:
    if st.button("🛑 STOP", type="primary", use_container_width=True):
        st.session_state.camera_running = False
        st.rerun()
else:
    if st.button("🟢 START", type="primary", use_container_width=True):
        st.session_state.camera_running = True
        st.rerun()


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

def perform_capture_and_read(text_to_read):
    if text_to_read:
        audio_data = speak_audio(text_to_read)
        if audio_data:
            #timestamping to play same thing everytime
            play_audio(audio_data, f"audio-{int(time.time())}")
    else:
        warning = speak_audio("Nothing to read.")
        if warning:
            play_audio(warning, f"warn-{int(time.time())}")


if st.button("🔊Read Aloud", type="primary"):
    perform_capture_and_read(sentence_text)

#unlocked
@st.fragment
def process_audio():
    audio_file = st.audio_input("", key=f"voice_{st.session_state.input_key}")

    if audio_file:
        with st.spinner("Processing..."):
            audio_bytes = audio_file.read()
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            result = st.session_state.whisper_model.transcribe(audio_np, fp16=False)
            cmd = result['text'].lower().strip()
            
            nav_map = {
                "home": "/",
                "hompage": "/",
                "visionary": "/",
                "main page": "/",
                "city": "pages/detector.py", 
                "surrounding": "pages/detector.py", 
                "surrounding detector": "pages/detector.py",
                "rainbow": "pages/colors.py", 
                "color": "pages/colors.py", 
                "color vision assist": "pages/colors.py",
                "speaker": "pages/text.py", 
                "text to speech": "pages/text.py", 
                "speech": "pages/speech.py", 
                "speech to text": "pages/speech.py", 
                "transcription": "pages/speech.py",
                "sign": "pages/sign.py", 
                "language": "pages/sign.py", 
                "translator": "pages/sign.py", 
                "sign language translator": "pages/sign.py", 
                "audio": "pages/input.py", 
                "input": "pages/input.py", 
                "text to audio input converter": "pages/input.py"
            }

            #start and stop
            start_keywords = ["start", "begin", "camera on", "turn on", "activate"]
            stop_keywords = ["stop", "off", "end", "stop camera", "turn off"]

            #button keywords            
            detect_keywords = ["detect", "capture", "what do you see", "what sign", "read sign"]
            add_keywords = ["add", "append", "insert"]
            delete_keywords = ["delete", "remove", "backspace", "undo"]
            read_keywords = ["read aloud", "read sentence", "speak sentence", "read text", "read", "speak"]
            clear_keywords = ["clear", "reset", "empty", "erase"] 
            
            if any(kw in cmd for kw in start_keywords):
                st.session_state.camera_running = True
                st.session_state.input_key += 1
                st.rerun()

            elif any(kw in cmd for kw in stop_keywords):
                st.session_state.camera_running = False
                st.session_state.input_key += 1
                st.rerun()

            command_executed = False
            skip_rerun = False
  
            #detecting
            if any(kw in cmd for kw in detect_keywords):
                if st.session_state.camera_running and ctx.video_processor:
                    with ctx.video_processor.lock:
                        current = ctx.video_processor.last_prediction
                    queue_audio(f"I see {current}")
                st.session_state.input_key += 1
                st.rerun()

            #adding
            elif any(kw in cmd for kw in add_keywords):
                command_executed = True
                if st.session_state.camera_running and ctx.video_processor:
                    with ctx.video_processor.lock:
                        word = ctx.video_processor.last_prediction
                    if word not in ["No Hand", "Waiting..."]:
                        st.session_state.sentence.append(word) # THIS updates the data
                        queue_audio(f"Added {word}")
                st.session_state.input_key += 1
                st.rerun()

            #deleting
            elif any(kw in cmd for kw in delete_keywords):
                command_executed = True
                if st.session_state.sentence:
                    removed = st.session_state.sentence.pop()
                    queue_audio(f"Deleted {removed}")
                st.session_state.input_key += 1
                st.rerun()

            #clearing
            elif any(kw in cmd for kw in clear_keywords):
                command_executed = True
                st.session_state.sentence = []
                queue_audio("Cleared everything")
                st.session_state.input_key += 1
                st.rerun()

            #reading aloud
            elif any(kw in cmd for kw in read_keywords):
                command_executed = True
                full_sentence = " ".join(st.session_state.sentence)
                queue_audio(full_sentence if full_sentence else "Nothing to read.")
                skip_rerun = True
                st.session_state.input_key += 1
                st.rerun()

           #finding url for navigating to page
            found_page = None
            for key, page_path in nav_map.items():
                if key in cmd:
                    found_page = page_path
                    break

            if found_page:
                st.session_state.input_key += 1
                
                #native command
                st.switch_page(found_page)

            if skip_rerun:
                #does NOT rerun
                st.session_state.input_key += 1 
            else:
                if command_executed:
                    time.sleep(0.5) 
                    st.session_state.input_key += 1
                    st.rerun() #reruns for visual updates to show in sentence box
                else:
                    st.session_state.input_key += 1
                    st.rerun(scope="fragment")

            #relocking system
            if "lock" in cmd or "re-lock" in cmd or "relock" in cmd:
                audio_data = speak_audio("System Relocked")
                if audio_data:
                    play_audio(audio_data, "lock-id")
                time.sleep(1.5)
                st.session_state.unlocked = False
                st.session_state.input_key += 1
                st.rerun()


if st.session_state.unlocked:
    process_audio()

if st.session_state.audio_queue:
    audio_data = speak_audio(st.session_state.audio_queue)
    if audio_data:
        play_audio(audio_data, f"play-{int(time.time())}")
    # Wipe the queue immediately so it can never play again by accident
    st.session_state.audio_queue = None
