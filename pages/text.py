#EASYOCR

import streamlit as st # pyright: ignore[reportMissingImports]
import easyocr # pyright: ignore[reportMissingImports]
import numpy as np # pyright: ignore[reportMissingImports]
from PIL import Image # pyright: ignore[reportMissingImports]
import io
from gtts import gTTS # pyright: ignore[reportMissingImports] 
import base64
import whisper
import streamlit.components.v1 as components
import time
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import threading
import cv2



#page details
st.set_page_config(
    page_title="OCR Text to Speech",
    page_icon="🔊",
    layout="wide"
)

#all session states
if 'whisper_model' not in st.session_state:
    st.session_state.whisper_model = whisper.load_model("tiny")
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "camera_running" not in st.session_state:
    st.session_state.camera_running = False
if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = None
if 'last_captured' not in st.session_state:
    st.session_state.last_captured = None


#automatic audios
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


#overlaying buton and welcome audio
if not st.session_state.unlocked:
    welcome_text = "OCR Text to Speech Recognition. This feature requires camera access for real-time detection. Allow camera access and let the AI see the text for you. Click the red Start button to begin detection."

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
        queue_audio(welcome_text)
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

if st.button("← Back to Home"):
    st.switch_page("home/app.py")

#styling text &voice-activ. microph.
st.markdown("""
    <style>
    h1 {
        font-size: 6vw !important;
        text-align: center !important;
    }
    .access {
        font-size: 2.1vw ! important;
    }
    .picture {
        font-size: 1.9vw !important;
    }
    @media (max-width: 768px) {
        h1 {
            font-size: 13vw !important;
        }
        .access {
            font-size: 6.5vw !important;
        }
        .picture {
            font-size: 5.5vw !important;
        }
    }
            
    /* microphone*/
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

st.markdown("<h1>OCR Text to Speech Recognition</h1>", unsafe_allow_html=True)
st.markdown("<p class='access'>This feature requires camera access for real-time detection.</p>", unsafe_allow_html=True)
st.markdown("<p class='picture'>Allow camera access and let the AI see the text for you!</p>", unsafe_allow_html=True)


#load model once
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

class OCRVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self.latest_frame = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        
        # We lock the frame and save a copy for the OCR to grab later
        with self._lock:
            self.latest_frame = img.copy()
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")
    
# Place this where you want the camera to appear in your UI
webrtc_ctx = webrtc_streamer(
    key="ocr-live-stream",
    video_processor_factory=OCRVideoProcessor,
    async_processing=True,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={
        "video": {"facingMode": "environment"}, # FORCES BACK CAMERA
        "audio": False
    },
    desired_playing_state=st.session_state.get("camera_running", False),
)

if st.session_state.camera_running:
    if st.button("🛑 STOP", type="primary", use_container_width=True):
        st.session_state.camera_running = False
        st.rerun()
else:
    if st.button("🟢 START", type="primary", use_container_width=True):
        st.session_state.camera_running = True
        st.rerun()

def perform_capture_and_read(image_file):
    if image_file is None:
        return "No image captured. Please take a photo first."
    
    try:
        # Convert BGR (Live Stream format) to RGB (EasyOCR format)
        img_rgb = cv2.cvtColor(image_file, cv2.COLOR_BGR2RGB)
        
        # Perform OCR directly on the pixels
        results = reader.readtext(img_rgb, paragraph=True)
        
        if results:
            full_text_list = [res[1] for res in results]
            combined_text = " . ".join(full_text_list)
            return combined_text
        else:
            return "No text detected. Try holding the phone steadier."
            
    except Exception as e:
        return f"Error processing video frame: {str(e)}"
    

#separate button for scanning text
if st.session_state.camera_running:
    if st.button("📸 Capture & Read", type="primary", use_container_width=True):
        if webrtc_ctx.video_processor:
            with webrtc_ctx.video_processor._lock:
                # Quickly grab the image and get OUT of the lock
                snap = webrtc_ctx.video_processor.latest_frame.copy() 
            
            # Show a placeholder so the user knows it's working
            placeholder = st.empty()
            placeholder.info("⌛ AI is reading the text... please hold.")
            
            # Run the heavy OCR
            text_result = perform_capture_and_read(snap)
            
            # Save to session state so it survives the audio rerun
            st.session_state.last_ocr_text = text_result
            queue_audio(text_result)
            
            placeholder.empty() # Remove the "Reading" message
            st.rerun()

#unlocked state for voice-activ.
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
                "home": "home/app.py",
                "hompage": "home/app.py",
                "visionary": "home/app.py",
                "main page": "home/app.py",
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

            detect_keywords = ["detect", "capture", "read", "what do you see", "see"]
            
            start_keywords = ["start", "begin", "camera on", "turn on", "activate"]
            stop_keywords = ["stop", "off", "end", "stop camera", "turn off"]

            if any(kw in cmd for kw in start_keywords):
                st.session_state.camera_running = True
                st.session_state.input_key += 1
                st.rerun()

            elif any(kw in cmd for kw in stop_keywords):
                st.session_state.camera_running = False
                st.session_state.input_key += 1
                st.rerun()

            if any(kw in cmd for kw in detect_keywords):
                if webrtc_ctx.video_processor:
                    with webrtc_ctx.video_processor._lock:
                        img_snapshot = webrtc_ctx.video_processor.latest_frame
                    
                    if img_snapshot is not None:
                        # Use the new array-based function
                        text_to_speak = perform_capture_and_read(img_snapshot)
                        queue_audio(text_to_speak)
                        st.session_state.input_key += 1
                        st.rerun()
                    else:
                        queue_audio("Camera is starting, please try again in a second.")
                        st.rerun()
                else:
                    queue_audio("Please start the camera first by saying 'Start Camera' or clicking the green button.")
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

            #relocking system
            if "lock" in cmd or "re-lock" in cmd or "relock" in cmd:
                audio_data = speak_audio("System Relocked")
                if audio_data:
                    play_audio(audio_data, "lock-id")
                time.sleep(1.5)
                st.session_state.unlocked = False
                st.session_state.input_key += 1
                st.rerun()

            #prevent rerun to play audio
        st.session_state.input_key += 1
        st.rerun()

#voice-commands when unlocked
if st.session_state.unlocked:
    process_audio()

if st.session_state.audio_queue:
    audio_data = speak_audio(st.session_state.audio_queue)
    if audio_data:
        play_audio(audio_data, f"play-{int(time.time())}")
    # Wipe the queue immediately so it can never play again by accident
    st.session_state.audio_queue = None
