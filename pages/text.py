#EASYOCR

import streamlit as st # pyright: ignore[reportMissingImports]
import easyocr # pyright: ignore[reportMissingImports]
import numpy as np # pyright: ignore[reportMissingImports]
from PIL import Image # pyright: ignore[reportMissingImports]
import io
from gtts import gTTS # pyright: ignore[reportMissingImports] 
from streamlit_back_camera_input import back_camera_input # pyright: ignore[reportMissingImports]
import base64
import whisper
import streamlit.components.v1 as components
import time



#page details
st.set_page_config(
    page_title="OCR Text to Speech",
    page_icon="🔊",
    layout="wide"
)

#all session states
if 'whisper_model' not in st.session_state:
    st.session_state.whisper_model = whisper.load_model("base")
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "camera_running" not in st.session_state:
    st.session_state.camera_running = False
if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = None

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
    welcome_text = "OCR Text to Speech Recognition. This feature requires camera access for real-time detection. Allow camera access and let the AI see the text for you. Click the camera to start detection."
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

if st.button("← Back to Home"):
    st.switch_page("home/app.py")

#styling text &voice-activ. microph.
st.markdown("""
    <style>
    h1 {
        font-size: 5vw !important;
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


#back camera
captured_file = back_camera_input()

def perform_capture_and_read():
    if captured_file:
        img = Image.open(captured_file)
        snap = np.array(img)
        
        results = reader.readtext(snap, paragraph=True, y_ths=-0.1, x_ths=10.0)
        
        if len(results) > 0:
            st.success(f"Detected {len(results)} Line(s):")
            
            full_text_list = []
            for res in results:
                line_text = res[1]
                full_text_list.append(line_text)
            
            #combined with pauses
            combined_text = " . ".join(full_text_list)
            return combined_text

        else:
            audio_data = speak_audio("No text detected. Please try again.")
            if audio_data:
                play_audio(audio_data, "no-id")
    else:
        audio_data = speak_audio("Camera not ready. Tap the camera to intialize recognition")
        if audio_data:
            play_audio(audio_data, "camera-id")


#separate button for scanning text
if st.button("🔍 Scan Text", type="primary", use_container_width=True):
    text_to_speak = perform_capture_and_read()
    if text_to_speak:
        queue_audio(text_to_speak)
        st.rerun()

#unlocked state for voice-activ.
if st.session_state.unlocked:
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

            detect_keywords = ["detect", "capture", "read", "what do you see", "see"]
            
            is_detecting = False

            if any(kw in cmd for kw in detect_keywords):
                if captured_file:
                    full_text = perform_capture_and_read()
                    queue_audio(full_text)
                    st.session_state.input_key +=1
                    st.rerun()
                else:
                    st.warning("Tap the camera to inititate detection")

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

if st.session_state.audio_queue:
    audio_data = speak_audio(st.session_state.audio_queue)
    if audio_data:
        play_audio(audio_data, f"play-{int(time.time())}")
    # Wipe the queue immediately so it can never play again by accident
    st.session_state.audio_queue = None
