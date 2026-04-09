# VISIONARY HOMEPAGE
import streamlit as st # pyright: ignore[reportMissingImports]
import base64
from pathlib import Path
import io
from gtts import gTTS
import whisper
import numpy as np
import streamlit.components.v1 as components
import time

#page details
st.set_page_config(
    page_title="Visionary",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed" 
)


#intializing all session states
if 'whisper_model' not in st.session_state:
    st.session_state.whisper_model = whisper.load_model("tiny")
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = None



#setting up the audios for automatic voice
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

audio_placeholder = st.empty()

#overlaying button to unlock audio
if not st.session_state.unlocked:

    #styling overlaying button
    st.markdown("""
        <style>
        /* Target the div that contains our specific button key */
        div[data-testid="stElementToolbar"] + div:has(button[aria-label="gate_button"]),
        .element-container:has(#gate_button_marker) + .element-container button {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 9999;
            background-color: rgba(205, 242, 247, 0.25); !important; /* Blue Tint */
            cursor: pointer;
            border: none;
        }
        </style>
        <div id="gate_button_marker"></div>
    """, unsafe_allow_html=True)

    #actual overlaying button
    if st.button(" ", key="gate_button", help="Click anywhere to unlock"):
        queue_audio("Welcome to Visionary. See Beyond. Hear Beyond.")
        st.session_state.unlocked = True 
        st.rerun()


#background gradient
page_bg_gradient = """
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to right, rgba(232, 245, 252, 0.7), rgba(252, 232, 248, 0.7));
        background-size: cover;
    }
</style>
"""
st.markdown(page_bg_gradient, unsafe_allow_html=True)

#styling text and voice-powered microphone
st.markdown("""
    <style>
        h1 { 
            font-size: 6vw !important; 
            text-align: center; 
            letter-spacing: 1px; 
            word-break: break-word; 
        }
        .text { 
            font-size: 2vw !important; 
            text-align: center; 
            letter-spacing: 1px; 
        }
        .block-container { 
            padding-top: 2rem; 
            padding-bottom: 2rem; 
        }
        @media (max-width: 768px) {
            h1 { font-size: 12vw !important; }
            .text { font-size: 6vw !important; }
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

st.markdown("<h1>Welcome to Visionary</h1>", unsafe_allow_html=True)
st.markdown("<p class='text'>See Beyond. Hear Beyond.</p>", unsafe_allow_html=True)


#styling for grid boxes
st.markdown("""
    <style>
    /* ENTIRE GRID CONTAINER */
    .square-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 30px;
       
        max-width: 1200px;
        margin: 0 auto; 
    }
            
    .grid-item {
        flex: 1 1 30%; /* Default: A flexible basis for 3 items per row */
        min-width: 200px;
        max-width: 300px;
    }
   
    /* 2 boxes per row for TABLETS */
    @media (max-width: 768px) {
        .grid-item {
            flex: 1 1 45%;
        }
    }
   
    /* 1 box per row for PHONES*/
    @media (max-width: 480px) {
        .grid-item {
            flex: 1 1 100%;
            max-width: 100%;
        }
    }

    /* Image box as link */
    .clickable-grid-link {
        display: block;
        text-decoration: none;
       
        position: relative;
        width: 100%;
        padding-top: 100%;
        height: 0;
       
        /* visual styles */
        border-radius: 20px !important;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1) !important;
        transition: box-shadow 0.3s ease !important;
        overflow: hidden;
        cursor: pointer !important;
    }
   
    /* image itself */
    .clickable-grid-img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100% !important;
        height: 100% !important;
       
        object-fit: cover;
        transition: transform 0.3s ease !important;
        border-radius: 15px !important;
        box-shadow: none !important;
    }
   
    /* hover effects */
    .clickable-grid-link:hover {
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3) !important;
        position: relative;
        z-index: 10;
    }
   
    .clickable-grid-link:hover .clickable-grid-img {
        transform: scale(1.1) !important;
    }
    </style>
""", unsafe_allow_html=True)



#create clickable html image
def get_base64_of_bin_file(bin_file):
    """reads a binary file and returns its base64 encoded string."""
    try:
        # NOTE: This part assumes you have local image files like "city.png"
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        # Using st.warning instead of changing the return value here
        st.warning(f"Image file not found: {bin_file}. Please ensure this file exists.")
        # Return None to handle the missing image gracefully later
        return None


def create_clickable_html(image_file):
    """generates clickable HTML for a local image file."""
    img_base64 = get_base64_of_bin_file(image_file)
    if not img_base64:
        # Return an error placeholder if image is missing
        return f"""
        <div class="clickable-grid-link" 
            style='background-color: #f8d7da; 
            color: #721c24;
            display: flex; 
            align-items: center; 
            justify-content: center;
            border: 1px solid #f5c6cb; 
            border-radius: 15px;
            text-align: center; 
            font-size: 14px;'>
            {image_file} Missing
        </div>
        """
    #extract image id from each image
    image_id = Path(image_file).stem
   
    #image id to specific page
    links = {
        "city": "detector",
        "rainbow": "colors",
        "speaker": "text",
        "text": "speech",
        "sign": "sign",
        "input": "input",
    }
   
    page_link = f"/{links.get(image_id)}?image_id={image_id}"
   

    return f"""
    <a href="{page_link}" target="_self" class="clickable-grid-link">
        <img src="data:image/png;base64,{img_base64}" alt="{image_id}" class="clickable-grid-img">
    </a>
    """

#images
images = [
    "city.png",
    "rainbow.png",
    "speaker.png",
    "text.png",
    "sign.png",
    "input.png",
]

#build html grid
grid_html_items = ""
for image_file in images:
    html_content = create_clickable_html(image_file)
    # Wrap each clickable item in the responsive grid-item class
    grid_html_items += f'<div class="grid-item">{html_content}</div>'


#final display
st.markdown(f'<div class="square-grid">{grid_html_items}</div>', unsafe_allow_html=True)

#unlocked state
if st.session_state.unlocked:
    #microphone for voice-powered feature
    audio_file = st.audio_input("", key=f"voice_{st.session_state.input_key}")

    if audio_file:
        with st.spinner("Processing..."):
            audio_bytes = audio_file.read()
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            result = st.session_state.whisper_model.transcribe(audio_np, fp16=False)
            cmd = result['text'].lower().strip()
            
            #phrases with the corresponding links
            nav_map = {
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

            #relocking system
            if "lock" in cmd or "re-lock" in cmd or "relock" in cmd:
                audio_data = speak_audio("System Relocked")
                if audio_data:
                    play_audio(audio_data, "lock-id")
                time.sleep(1.5)
                st.session_state.unlocked = False
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

if st.session_state.audio_queue:
    audio_data = speak_audio(st.session_state.audio_queue)
    if audio_data:
        play_audio(audio_data, f"play-{int(time.time())}")
    # Wipe the queue immediately so it can never play again by accident
    st.session_state.audio_queue = None
