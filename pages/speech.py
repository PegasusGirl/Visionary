#WHISPER

import collections
collections.Callable = collections.abc.Callable

import streamlit as st # pyright: ignore[reportMissingImports]
import numpy as np # pyright: ignore[reportMissingImports] 
import whisper # pyright: ignore[reportMissingImports]
from datetime import datetime
import time
import io
import base64
import streamlit.components.v1 as components
from gtts import gTTS

#page details
st.set_page_config(
    page_title="Speech to Text Transcription",
    page_icon="📝",
    layout="wide",
)

#all session states
if 'whisper_model' not in st.session_state:
    st.session_state.whisper_model = whisper.load_model("base")
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "transcription" not in st.session_state:
    st.session_state.transcription = 0
if "voice" not in st.session_state:
    st.session_state.voice = 0
if "last_detected" not in st.session_state:
    st.session_state.last_detected = []
if 'history' not in st.session_state:
    st.session_state.history = []


#intitate all audios
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


#overlaying button and welcome audio
if not st.session_state.unlocked:
    welcome_text = "Speech to Text Transcription. This feature requires audio access for transcription. Allow audio access and hear what others say!"
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

#styling main text & voice-activ. microphone
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
            
    /* microphone */        
    [data-testid="stVerticalBlock"] > div:has(div[class*="st-key-voice_"]) {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        height: 0px !important; 
        min-height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    div[class*="st-key-voice_"] [data-testid="stAudioInput"] {
        position: fixed !important;
        bottom: 30px !important; 
        left: 50% !important;
        transform: translateX(-50%) !important;
        
        background-color: white !important;
        border-radius: 100px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2) !important;
        border: 1px solid #f0f0f0 !important;
        

        width: 400px !important;
        height: 85px !important;
        z-index: 999999 !important;
        
      
        display: flex !important;
        align-items: center !important;
        padding: 0 15px !important;
    }

    div[class*="st-key-voice_"] [data-testid="stAudioInput"] > div {
        background-color: transparent !important;
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }

    div[class*="st-key-voice_"] button[aria-label="Record"],
    div[class*="st-key-voice_"] button[aria-label="Stop recording"] {
        background-color: #FF0000 !important;
        color: white !important;
        border-radius: 50% !important;
        min-width: 65px !important;
        height: 65px !important;
        border: none !important;
        flex-shrink: 0 !important;
        margin: 0 !important; /* Ensures it stays left */
    }

    div[class*="st-key-voice_"] [data-testid="stAudioInput"] span {
        color: #333 !important;
        font-weight: 600 !important;
        margin-left: 20px !important;
    }


    [data-testid="stAudioInput"] label { 
            display: none !important;
    }
    [data-testid="stAudioInput"] svg { 
        fill: white !important; 
        transform: scale(1.5) !important; 
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>Speech to Text Transcription</h1>", unsafe_allow_html=True)
st.markdown("<p class='access'>This feature requires audio access for transcription.</p>", unsafe_allow_html=True)
st.markdown("<p class='picture'>Allow audio access and hear what others say!</p>", unsafe_allow_html=True)



#styling actual speech transcription microphone
st.markdown("""
    <style>
    /* Target the audio input button specifically */
    div[class*="st-key-audio_"] > div button[aria-label="Record"]  {
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
            transform: scale(1.85) !important;
    }   

    [data-testid="stAudioInput"] button[aria-label="Stop recording"] {
        background-color: #FF0000 !important;
        color: white !important;
        height: 150px !important;
        width: 75px !important;
        border-radius: 30px !important;
                

        width: 60px !important;  
        height: 60px !important;  
        transition: transform 0.2s ease !important;
    }            

    .text {
        font-size: 24px !important; 
        margin-left: 5px !important;
    }
        
    </style>
    """, unsafe_allow_html=True)


#recording buttons
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    with st.container(key="transcription-container"):
        transcription_file = st.audio_input("", key=f"audio_{st.session_state.transcription}")


#display
st.markdown("### 📝 Live Transcription")
transcription_container = st.container()

if transcription_file:
    with st.spinner("Transcribing..."):
        audio_bytes = transcription_file.read()
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        result = st.session_state.whisper_model.transcribe(audio_np, fp16=False)
        
        st.session_state.history.append(result['text'])
        
        #increase key and rerun (restarts microp.)
        st.session_state.transcription += 1
        st.rerun()



for text in st.session_state.history:
    st.markdown(f'<p class="text">{text}</p>', unsafe_allow_html=True)

with col2:
    if st.session_state.history:
        if st.button("🗑️ Clear All", use_container_width=True):
            #reset history list
            st.session_state.history = [] 

            #increase key to reset the audio widget
            st.session_state.transcription += 1
            st.rerun()
    else:
        st.button("🗑️ Clear All", disabled=True, use_container_width=True)

with col3:
    if st.session_state.history:
        #preparing file data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcription_{timestamp}.txt"
        full_text = "\n\n".join(st.session_state.history)

        #uses pending downloads if voice-triggered
        if "pending_download" in st.session_state:
            data = st.session_state.pending_download["data"]
            fname = st.session_state.pending_download["file_name"]

            #clear after one use
            del st.session_state.pending_download
        else:
            data = full_text
            fname = filename
        
        st.download_button(
            label="💾 Save",
            data=full_text,
            file_name=filename,
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.button("💾 Save", disabled=True, use_container_width=True)

def perform_capture_and_read(text_to_read):
    if text_to_read:
        audio_data = speak_audio(text_to_read)
        if audio_data:
            #put a time stamp to ensure audio is played even tho text is still the same
            play_audio(audio_data, f"audio-{int(time.time())}")
    else:
        warning = speak_audio("Nothing to read.")
        if warning:
            play_audio(warning, f"warn-{int(time.time())}")



#unlocked state
@st.fragment
def process_audio():
    with st.container(key="voice-pill-container"):
        voice_file = st.audio_input("", key=f"voice_{st.session_state.voice}")

    if voice_file:
        with st.spinner("Processing..."):
            audio_bytes = voice_file.read()
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

            clear_keywords = [
                "clear", "clear all", "delete", "delete all", "reset", 
                "clear everything", "new session", "start over", "erase"
            ]

            #deleting
            if any(kw in cmd for kw in clear_keywords):
                st.session_state.history = []
                st.session_state.voice += 1
                speak_audio_data = speak_audio("Transcription history cleared.")
                if speak_audio_data:
                    play_audio(speak_audio_data, "cmd-feedback")
                st.rerun()

            #finding url for navigating to page
            found_page = None
            for key, page_path in nav_map.items():
                if key in cmd:
                    found_page = page_path
                    break

            if found_page:
                st.session_state.voice += 1
                
                #native command
                st.switch_page(found_page)

            else:
                st.session_state.voice += 1
                st.rerun(scope="fragment") #ensures only partial rerun


            #relocking system
            if "lock" in cmd or "re-lock" in cmd or "relock" in cmd:
                audio_data = speak_audio("System Relocked")
                if audio_data:
                    play_audio(audio_data, "lock-id")
                time.sleep(1.5)
                st.session_state.unlocked = False
                st.session_state.voice += 1
                st.rerun()

if st.session_state.unlocked:
    process_audio()


