#INPUT

import streamlit as st # pyright: ignore[reportMissingImports]
from gtts import gTTS # pyright: ignore[reportMissingImports]
import io
import base64
import whisper
import time
import streamlit.components.v1 as components
import numpy as np

#page details
st.set_page_config(
    page_title="Text-Input to Audio Converter",
    page_icon="💬",
    layout="wide"
)

#session states
if 'whisper_model' not in st.session_state:
    st.session_state.whisper_model = whisper.load_model("tiny")
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "speak_count" not in st.session_state:
    st.session_state.speak_count = 0
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

#overlaying button and audio
if not st.session_state.unlocked:
    welcome_text = "Text to Audio Input Converter. Type any text and let others hear what you have to say. "

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

#styling text and microp.
st.markdown("""
    <style>
    h1 { 
        font-size: 6vw !important; 
        text-align: center !important; 
    }
            
    .info { 
        font-size: 2.1vw ! important; 
        text-align: left !important; 
    }
            
    @media (max-width: 768px) {
        h1 { 
            font-size: 13vw !important; 
    }
        .info { 
            font-size: 6.5vw !important; 
        }
    }
                
        /* Floating mic pill */
    [data-testid="stAudioInput"] {
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        width: 50% !important;
        max-width: 375px;
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
    """, unsafe_allow_html=True
)

st.markdown("<h1>Text to Audio Input Converter</h1>", unsafe_allow_html=True)
st.markdown("<p class='info'>Type any text and let others hear what you have to say</p>", unsafe_allow_html=True)


#what user types
user_text = st.text_area("Enter your message here:")


if st.button("🔊Speak", type="primary"):
    if user_text:
        with st.spinner("Generating speech..."):
            queue_audio(user_text)
    else:
        warning = "Please enter some text to speak"
        st.warning(warning)
        queue_audio(warning)

if st.session_state.get("temp_warning"):
    st.warning(st.session_state.temp_warning)
    st.session_state.temp_warning = None


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

            play_keywords = ["speak", "say", "talk", "read this", "speak this", "read"]

            #playing text
            if any(keyword in cmd for keyword in play_keywords):
                if user_text:
                    queue_audio(user_text)
                else:
                    st.session_state.temp_warning = "Please enter some text to speak"
                    queue_audio("Please enter some text to speak")
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
