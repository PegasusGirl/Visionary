#WHISPER

import collections
collections.Callable = collections.abc.Callable

import streamlit as st # pyright: ignore[reportMissingImports]
import pyaudio # pyright: ignore[reportMissingModuleSource]
import numpy as np # pyright: ignore[reportMissingImports] 
import whisper # pyright: ignore[reportMissingImports]
from datetime import datetime 

#page details
st.set_page_config(
    page_title="Speech to Text Transcription",
    page_icon="📝",
    layout="wide",
)

if st.button("← Back to Home"):
    st.switch_page("home/app.py")


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

st.markdown("<h1>Speech to Text Transcription</h1>", unsafe_allow_html=True)
st.markdown("<p class='access'>This feature requires audio access for transcription.</p>", unsafe_allow_html=True)
st.markdown("<p class='picture'>Allow audio access and hear what others say!</p>", unsafe_allow_html=True)


#intialize session state
if 'transcription' not in st.session_state:
    st.session_state.transcription = []
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'audio_buffer' not in st.session_state:
    st.session_state.audio_buffer = []
if 'whisper_model' not in st.session_state:
    st.session_state.whisper_model = None

#audio details
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

#TRANSCRIBING FUNCTIONS:

#load whisper model
def load_whisper_model(model_size):
    try:
        with st.spinner(f"Loading Whisper {model_size} model"):
            model = whisper.load_model(model_size)
        return model
    except Exception as e:
        st.error(f"Error loading Whisper model: {str(e)}")
        return None

#transcribing
def transcribe_audio(audio_data, model, language="en"):
    try:
        #converts audio bytes to numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        #transcribe
        result = model.transcribe(
            audio_np, 
            language=language,
            fp16=False, 
            task='transcribe'
        )
        return result['text'].strip()
    except Exception as e:
        return f"Error: {str(e)}"

class AudioRecorder:
    #handles audio recording
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.frames = []

    #starts recording audio     
    def start_recording(self):
        self.frames = []
        self.is_recording = True
        
        try:
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            return True
        except Exception as e:
            st.error(f"Error starting recording: {str(e)}")
            return False
    
    #records a chunk of audio
    def record_chunk(self):
        if self.stream and self.is_recording:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
                return data
            except Exception as e:
                st.error(f"Error recording: {str(e)}")
                return None
        return None
    
    #stops recording
    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        audio_data = b''.join(self.frames)
        self.frames = []
        return audio_data
    
    #cleanin up
    def cleanup(self):
        if self.stream:
            self.stream.close()
        self.audio.terminate()


#loading model
if st.session_state.whisper_model is None:
    st.session_state.whisper_model = load_whisper_model("base")
    if st.session_state.whisper_model is not None:
        st.sidebar.success("✅ Model loaded!")

#recording buttons
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if st.button(
        "🔴 Start Recording" if not st.session_state.is_recording else "⏹️ Stop Recording",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.whisper_model is None
    ):
        st.session_state.is_recording = not st.session_state.is_recording
        if not st.session_state.is_recording:
            st.session_state.audio_buffer = []
        st.rerun()

with col2:
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.transcription = []
        st.session_state.audio_buffer = []
        st.rerun()

with col3:
    if st.button("💾 Save", use_container_width=True):
        if st.session_state.transcription:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcription_{timestamp}.txt"
            text = "\n\n".join(st.session_state.transcription)
            st.download_button(
                "⬇️ Download",
                text,
                file_name=filename,
                mime="text/plain"
            )

#statuses
status_placeholder = st.empty()
if st.session_state.is_recording:
    status_placeholder.success("🔴 Recording in progress... Speak now!")
elif st.session_state.whisper_model is None:
    status_placeholder.error("❌ Please wait for model to load")
else:
    status_placeholder.info("⚪ Ready to record - Click 'Start Recording' to begin")

#display
st.markdown("### 📝 Live Transcription")
transcription_container = st.container()

with transcription_container:
    if st.session_state.transcription:
        for i, text in enumerate(st.session_state.transcription):
            st.markdown(f"**[{i+1}]** {text}")
    else:
        st.info("Your transcription will appear here...")

#recording
if st.session_state.is_recording and st.session_state.whisper_model is not None:
    recorder = AudioRecorder()
    
    if recorder.start_recording():
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        chunks_needed = int((RATE / CHUNK) * 5)
        
        try:
            chunk_count = 0
            
            while st.session_state.is_recording:
                #records chunk
                data = recorder.record_chunk()
                if data:
                    st.session_state.audio_buffer.append(data)
                    chunk_count += 1
                    
                    #updating progress of words
                    progress = min((chunk_count % chunks_needed) / chunks_needed, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Recording... {chunk_count * CHUNK / RATE:.1f}s")
                    
                    if chunk_count >= chunks_needed:
                        status_text.text("🔄 Transcribing...")
                        
                        #combining data
                        audio_data = b''.join(st.session_state.audio_buffer)
                        
                        #transcribe
                        text = transcribe_audio(
                            audio_data, 
                            st.session_state.whisper_model,
                            "en"
                        )
                        
                        #adds to transcription
                        if text and not text.startswith("Error"):
                            st.session_state.transcription.append(text)
                            st.rerun()
                        
                        #clearing buffer
                        st.session_state.audio_buffer = []
                        chunk_count = 0
                        progress_bar.progress(0)
                        
        finally:
            recorder.stop_recording()
            recorder.cleanup()
            progress_bar.empty()
            status_text.empty()



