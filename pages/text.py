#EASYOCR

import streamlit as st # pyright: ignore[reportMissingImports]
import easyocr # pyright: ignore[reportMissingImports]
import numpy as np # pyright: ignore[reportMissingImports]
from PIL import Image # pyright: ignore[reportMissingImports]
import io
from gtts import gTTS # pyright: ignore[reportMissingImports] 
from streamlit_back_camera_input import back_camera_input # pyright: ignore[reportMissingImports]

#page details
st.set_page_config(
    page_title="OCR Text to Speech",
    page_icon="🔊",
    layout="wide"
)

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

#styling text
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

#gtts for saying words out loud
def text_to_speak(text):
    """Converts text to speech using gTTS and returns audio for the widget"""
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        st.error(f"Speech Error: {e}")
        return None

#back camera
captured_file = back_camera_input()

#separate button for scanning text
if st.button("🔍 Scan Text", type="primary", use_container_width=True):
    if captured_file:
        img = Image.open(captured_file)
        snap = np.array(img)
        
        with st.spinner("Processing..."):
            # Line grouping logic as requested
            results = reader.readtext(snap, paragraph=True, y_ths=-0.1, x_ths=10.0)
            
            if len(results) > 0:
                st.success(f"Detected {len(results)} Line(s):")
                
                full_text_list = []
                for res in results:
                    line_text = res[1]
                    full_text_list.append(line_text)
                
                #combined with pauses
                combined_text = " . ".join(full_text_list)
                audio_data = text_to_speak(combined_text)
                if audio_data:
                    st.audio(audio_data, format="audio/mpeg", autoplay=True)
    
            else:
                audio_data = text_to_speak("No text detected. Please try again.")
                if audio_data:
                    st.audio(audio_data, format="audio/mpeg", autoplay=True)
    else:
        audio_data = text_to_speak("Camera not ready. Tap the camera to intialize recognition")
        if audio_data:
                    st.audio(audio_data, format="audio/mpeg", autoplay=True)