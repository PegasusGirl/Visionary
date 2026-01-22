#INPUT

import streamlit as st # pyright: ignore[reportMissingImports]
from gtts import gTTS # pyright: ignore[reportMissingImports]
import io

#page details
st.set_page_config(
    page_title="Text-Input to Audio Converter",
    page_icon="💬",
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

st.markdown("""
    <style>
    h1 { 
        font-size: 5vw !important; 
        text-align: center !important; 
    }
            
    .info { 
        font-size: 2.1vw ! important; 
        text-align: center; 
    }
            
    @media (max-width: 768px) {
        h1 { 
            font-size: 13vw !important; 
    }
        .info { 
            font-size: 6.5vw !important; 
        }
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown("<h1>Text to Audio Input Converter</h1>", unsafe_allow_html=True)
st.markdown("<p class='info'>Type any text and let others hear what you have to say</p>", unsafe_allow_html=True)

#intialize session state
if "speech_placeholder" not in st.session_state:
    st.session_state.speech_placeholder = None

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

#what user types
user_text = st.text_area("Enter your message here:")

# Create the placeholder globally so the function can find it
speech_area = st.empty()

if st.button("Speak", type="primary"):
    if user_text:
        with st.spinner("Generating speech..."):
            audio_data = text_to_speak(user_text)
            if audio_data:
                st.audio(audio_data, format="audio/mpeg", autoplay=True)#saying text out loud
    else:
        st.warning("Please enter some text to convert to speech.")