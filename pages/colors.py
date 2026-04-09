#COLOR FILTERING

import streamlit as st # pyright: ignore[reportMissingImports]
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase # pyright: ignore[reportMissingImports]
import numpy as np # pyright: ignore[reportMissingImports]
import av # pyright: ignore[reportMissingImports] 
import threading
import io
import base64
import streamlit.components.v1 as components
import time
import numpy as np
import whisper
from gtts import gTTS
import re


#page details
st.set_page_config(
    page_title="Color Filters",
    page_icon="🌈",
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
if 'selected_filter' not in st.session_state:
    st.session_state.selected_filter = "None"
if "requested_filter" not in st.session_state:
    st.session_state.requested_filter = None
if "requested_intensity" not in st.session_state:
    st.session_state.requested_intensity = None
if "filter_intensity" not in st.session_state:
    st.session_state.filter_intensity = 1.0
if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = None

#all audios
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
    welcome_text = "Color Vision Assistance. This feature requires camera access for real-time color filtering. Allow camera access and see the world with color. Click the red start button to begin filtering."

    #styling button
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

#styling text & microphone
st.markdown("""
    <style>
    h1 {
        font-size: 6vw !important;
        text-align: center !important;
    }
    .access {
        font-size: 2.1vw ! important;
    }
    .allow {
        font-size: 1.9vw !important;
    }
    @media (max-width: 768px) {
        h1 {
            font-size: 13vw !important;
        }
        .access {
            font-size: 6.5vw !important;
        }
        .allow {
            font-size: 5.5vw !important;
        }         
    }
            
    /* voice-activ. microph. */
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
    }

    </style>
    """, unsafe_allow_html=True
    )
st.markdown("<h1>Color Vision Assistance</h1>", unsafe_allow_html=True)
st.markdown("<p class='access'>This feature requires camera access for real-time color filtering</p>", unsafe_allow_html=True)
st.markdown("<p class='allow'>Allow camera access and see the world with color</p>", unsafe_allow_html=True)


def apply_color_correction(img, mode, intensity=1.0):
    if mode == "None" or intensity <= 0.0:
        return img
    
    img_f = img.astype("float32") / 255.0
    R, G, B = img_f[:, :, 0], img_f[:, :, 1], img_f[:, :, 2]

    if mode == "Protanopia (Red Weak)":

        #shift red tones toward pink/magenta
        red_mask = np.maximum(0, R - G) 
        R_corr = R
        B_corr = np.clip(B + (red_mask * 0.7), 0, 1)

        #shift green tones toward cyan/yellow
        green_mask = np.maximum(0, G - R)
        G_corr = np.clip(G * 1.3, 0, 1)
        R_corr = np.clip(R_corr + (green_mask * 0.2), 0, 1) 
        
        #fully enhanced
        corrected = np.stack([R_corr, G_corr, B_corr], axis=-1)
        
    elif mode == "Deuteranopia (Green Weak)":

        #shift red tones toward pink/magenta
        red_mask = np.maximum(0, R - G)
        R_corr = R
        B_corr = np.clip(B + (red_mask * 0.8), 0, 1) 

        #shift green tones toward cyan/yellow (more intensity)
        green_mask = np.maximum(0, G - R)
        G_corr = np.clip(G * 1.25, 0, 1) 
        B_corr = np.clip(B_corr + (green_mask * 0.4), 0, 1) 

        #strong blue tint
        confusion_mask = np.where((R > 0.3) & (R < 0.7) & (abs(R - G) < 0.1), 1.0, 0.0)
        
        #muddy/dull pinks to enhanced violet/blue
        B_corr = np.clip(B_corr + (confusion_mask * 0.5), 0, 1)
        
        #distinguish red from green
        dark_red_mask = np.where((R < 0.4) & (R > G), 1.0, 0.0)
        R_corr = np.clip(R_corr - (dark_red_mask * 0.2), 0, 1)

        #fully corrected
        corrected = np.stack([R_corr, G_corr, B_corr], axis=-1)

    elif mode == "Tritanopia (Blue Weak)":
        
        #shift blue tones toward red/magenta
        blue_mask = np.maximum(0, B - G)
        R_corr = np.clip(R + (blue_mask * 0.8), 0, 1)
        G_corr = G
        B_corr = B

        #shift yellow/orange tones toward cyan/green tones
        yellow_mask = np.maximum(0, (R + G) / 2 - B)
        G_corr = np.clip(G_corr + (yellow_mask * 0.3), 0, 1)
        B_corr = np.clip(B_corr + (yellow_mask * 0.5), 0, 1)
        R_corr = np.clip(R_corr - (yellow_mask * 0.2), 0, 1)

        #enhance green tones (luminosity)
        green_mask = np.maximum(0, G - (R + B) / 2)
        G_corr = np.clip(G_corr * 1.2, 0, 1)
        R_corr = np.clip(R_corr + (green_mask * 0.1), 0, 1) #add a tiny bit of yellow-tint for purity

        #fully corrected
        corrected = np.stack([R_corr, G_corr, B_corr], axis=-1)
        
    else:
        #raw camera feed
        return img
    
    #important for intensity
    blended = (img_f * (1.0 - intensity)) +((corrected * intensity))
       
    return (blended* 255).astype("uint8")


class ColorBlindTransformer(VideoTransformerBase):
    def __init__(self):

        #intialize lock
        self.lock = threading.Lock()

        #temporary state to hold filter type
        self.colorblind_type = "None"
        self.intensity = 1.0


    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        #convert video frame to numpy array and convert bgr to rgb
        img = frame.to_ndarray(format="bgr24")
        img_rgb = img[:, :, ::-1]
       
        #safely read current colorblind type using the lock
        with self.lock:
            current_type = self.colorblind_type
            current_intensity = self.intensity
       
        #apply correction logic based on type of color blindess
        corrected_rgb = apply_color_correction(img_rgb, current_type, current_intensity)
       
        #convert rgb frame back bgr frame and return it
        corrected_bgr = corrected_rgb[:, :, ::-1]
        return av.VideoFrame.from_ndarray(corrected_bgr, format="bgr24")

if st.session_state.requested_filter is not None:
    st.session_state.selected_filter = st.session_state.requested_filter
    st.session_state.filter_intensity = (
        st.session_state.requested_intensity
        if st.session_state.requested_intensity is not None
        else st.session_state.filter_intensity
    )
    #clear the request so it doesn't repeat on next run
    st.session_state.requested_filter = None
    st.session_state.requested_intensity = None


#the filter selectbox (based on type of filter)  
def update_filter_callback(transformer_container):
    if transformer_container.video_transformer:
        with transformer_container.video_transformer.lock:
            transformer_container.video_transformer.colorblind_type = st.session_state.selected_filter
            transformer_container.video_transformer.intensity = st.session_state.get("filter_intensity", 1.0)

#webrtc camera
webrtc_ctx = webrtc_streamer(
    key="real-time-correction",
    video_processor_factory=ColorBlindTransformer,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
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

#styling intensity slider & selectbox
st.markdown("""
    <style>
    /*  SLIDER CONTAINER */
    div[data-testid="stSlider"] {
        background: rgba(255, 255, 255, 0.75);
        border-radius: 16px;
        padding: 20px 24px; 
        border: 1px solid rgba(200,200,255,0.3);
        margin: 16px 0;
    }

    div[data-testid="stSlider"] label p {
        font-size: 1.25rem !important; 
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-bottom: 12px !important;
    }

    div[data-baseweb="slider"] > div {
        height: 12px !important; 
    }

    div[data-baseweb="slider"] > div > div:first-child {
        height: 12px !important;
        border-radius: 6px !important;
    }

    div[data-baseweb="slider"] > div > div > div {
        background: linear-gradient(to right, #808080, #ff0000) !important;
        height: 12px !important;
        border-radius: 6px !important;
    }
                
    div[data-baseweb="slider"] div[role="slider"] {
        background: white !important;
        border: 3px solid #ff0000 !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4) !important;
        width: 26px !important;
        height: 26px !important;
        border-radius: 50% !important;
        top: -7px !important; 
        transition: all 0.2s ease;
    }

    div[data-baseweb="slider"] div[role="slider"]:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.6) !important;
    }


    div[data-testid="stTickBarMin"], div[data-testid="stTickBarMax"] {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: #ff0000 !important;
        margin-top: 25px !important;           
    }
                
    /* SELECTBOX CONTAINER */
    div[data-testid="stSelectbox"] {
        background: rgba(255, 255, 255, 0.75);
        border-radius: 16px;
        padding: 20px 24px;
        border: 1px solid rgba(200,200,255,0.3);
        margin: 16px 0;
    }


    div[data-testid="stSelectbox"] label p {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-bottom: 12px !important;
    }


    div[data-testid="stSelectbox"] > div:nth-child(2) > div {
        border: 2px solid #ff0000 !important; /* Red border */
        border-radius: 8px !important;
        background-color: white !important;
    }


    div[data-testid="stSelectbox"] > div:nth-child(2) > div:focus-within {
        box-shadow: 0 0 0 0.2rem rgba(255, 0, 0, 0.25) !important;
    }
    </style>
    """, unsafe_allow_html=True)


#the actual filter selecbox
st.selectbox(
    "Choose Your Color-Blind Type",
    ["None", "Protanopia (Red Weak)", "Deuteranopia (Green Weak)", "Tritanopia (Blue Weak)"],
    key="selected_filter", #selectbox with session state
    on_change=update_filter_callback, #updates the filter based on the type of filter selected
    args=(webrtc_ctx,)
)

#intensity slider
st.slider(
    "Correction Intensity",
    min_value = 0.0,
    max_value = 1.0,
    value = st.session_state.filter_intensity,
    step=0.1,
    key="filter_intensity",
    on_change=update_filter_callback,
    args=(webrtc_ctx,)
)

st.warning(f"Current Correction: **{st.session_state.selected_filter}**.")

if not webrtc_ctx.video_transformer:
    st.info("Click 'START' above to begin the live feed.")


#voice-activ. when unlocked
if st.session_state.unlocked:
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

            filters = {
                "protanopia":    "Protanopia (Red Weak)",
                "red weak":      "Protanopia (Red Weak)",
                "red":           "Protanopia (Red Weak)",  
                "deuteranopia":  "Deuteranopia (Green Weak)",
                "green weak":    "Deuteranopia (Green Weak)",
                "green":         "Deuteranopia (Green Weak)",
                "tritanopia":    "Tritanopia (Blue Weak)",
                "blue weak":     "Tritanopia (Blue Weak)",
                "blue":          "Tritanopia (Blue Weak)",
                "none":          "None",
                "normal":        "None",
                "reset":         "None",
                "off":           "None",
                "no filter":     "None",
            }  

            for spoken_key, filter_name in filters.items():
                if spoken_key in cmd:
                    st.session_state.requested_filter = filter_name

                    #still updates filter on live
                    if webrtc_ctx.video_transformer is not None:
                        with webrtc_ctx.video_transformer.lock:
                            webrtc_ctx.video_transformer.colorblind_type = filter_name
                            webrtc_ctx.video_transformer.intensity = (
                                st.session_state.requested_intensity
                                if st.session_state.requested_intensity is not None
                                else st.session_state.filter_intensity)
                    st.session_state.input_key += 1
                    st.rerun()
                    break


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

if st.session_state.audio_queue:
    audio_data = speak_audio(st.session_state.audio_queue)
    if audio_data:
        play_audio(audio_data, f"play-{int(time.time())}")
    # Wipe the queue immediately so it can never play again by accident
    st.session_state.audio_queue = None


