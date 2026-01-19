#INPUT

import streamlit as st # pyright: ignore[reportMissingImports]
from gtts import gTTS # pyright: ignore[reportMissingImports]
import io
import streamlit.components.v1 as components # pyright: ignore[reportMissingImports]


st.set_page_config(
    page_title="Text to Audio",
    page_icon="💬",
    layout="wide"
)

# --- 1. INITIALIZE SESSION STATE ---
# This fixes your specific error
if "speech_placeholder" not in st.session_state:
    st.session_state.speech_placeholder = None

# --- 2. STYLING ---
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

st.markdown("""
    <style>
    h1 { font-size: 5vw !important; text-align: center !important; }
    .info { font-size: 2.1vw ! important; text-align: center; }
    @media (max-width: 768px) {
        h1 { font-size: 13vw !important; }
        .info { font-size: 6.5vw !important; }
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown("<h1>Text to Audio Input Converter</h1>", unsafe_allow_html=True)
st.markdown("<p class='info'>Type any text and let others hear what you have to say</p>", unsafe_allow_html=True)

# --- 3. SPEECH FUNCTIONS ---

def autoplay_text_with_js(text_to_speak):
    """Uses the browser's Native Voice (Fastest for initial load)"""
    js_code = f"""
    <script>
        function speak() {{
            if ('speechSynthesis' in window) {{
                var utterance = new SpeechSynthesisUtterance('{text_to_speak}');
                window.speechSynthesis.speak(utterance);
            }}
        }}
        speak();
    </script>
    """
    components.html(js_code, height=0, width=0)

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

# --- 4. UI AND LOGIC ---

# Run the initial welcome voice
if "first_load" not in st.session_state:
    autoplay_text_with_js("Text to Audio Input converter. Type any text and let others hear what you have to say.")
    st.session_state.first_load = False

user_text = st.text_area("Enter your message here:")

# Create the placeholder globally so the function can find it
speech_area = st.empty()

if st.button("Speak", type="primary"):
    if user_text:
        with st.spinner("Generating speech..."):
            audio_data = text_to_speak(user_text)
            if audio_data:
                # On mobile, the widget is the most 'trustworthy' way to play sound
                st.audio(audio_data, format="audio/mpeg", autoplay=True)
    else:
        st.warning("Please enter some text to convert to speech.")
