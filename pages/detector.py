#YOLO - ULTRALYTICS

import collections
import collections.abc
collections.Callable = collections.abc.Callable

import streamlit as st # pyright: ignore[reportMissingImports]
from ultralytics import YOLOWorld # pyright: ignore[reportMissingImports]
import av # pyright: ignore[reportMissingImports]
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase # pyright: ignore[reportMissingImports]
from gtts import gTTS # pyright: ignore[reportMissingImports]
import threading
import io

#page details
st.set_page_config(
    page_title="Surrounding Detector",
    page_icon="📷",
    layout="wide", # Essential for responsiveness
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


st.markdown("<h1>Surrounding Detector</h1>", unsafe_allow_html=True)
st.markdown("<p class='access'>This feature requires camera access for real-time detection.</p>", unsafe_allow_html=True)
st.markdown("<p class='picture'>Allow camera access and let the AI see for you!</p>", unsafe_allow_html=True)

#detection storage
if "last_detected" not in st.session_state:
    st.session_state.last_detected = []
if "first_load" not in st.session_state:
    st.session_state.first_load = True

#gtts speaking
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


#loading yolo model
@st.cache_resource
def load_yolo_world():
    model = YOLOWorld("yolov8m-worldv2.pt") 
    everything_list = [
        "person", "trip hazard on floor", "navigation sign", "handrail", "pedestrian crossing", 
        "stairs", "door", "chair", "table", "phone", "keys", "wallet", 
        "bottle", "cup", "plate", "knife", "fork", "spoon", "computer", "mouse", 
        "keyboard", "backpack", "umbrella", "handbag", "tie", "suitcase", 
        "bicycle", "car", "motorcycle", "bus", "train", "truck", "traffic light", 
        "fire hydrant", "stop sign", "parking meter", "bench", "dog", "cat", 
        "bed", "toilet", "globe stand", "television", "laptop", "microwave", "oven", "toaster", 
        "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", 
        "hair drier", "toothbrush", "pill bottle", "spectacles", "walking cane",
        "ramp", "elevator", "pothole", "curb", "trash can", "step", "speaker", 
        "framed photo on the wall", "printed photo on table", "bookshelf filled with books", 
        "religious statue", "laptop stand", "lamp", "coaster", "wall"
    ]
    model.set_classes(everything_list)
    return model

model = load_yolo_world()

class YOLOVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.model = model
        self.current_detections = [] 
        self._lock = threading.Lock() 

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        results = self.model.predict(img, conf=0.25, imgsz=320, verbose=False)
        
        names = results[0].names
        detected_this_frame = []
        for box in results[0].boxes:
            label = names[int(box.cls[0])]
            detected_this_frame.append(label)

        with self._lock:
            self.current_detections = list(set(detected_this_frame))

        return av.VideoFrame.from_ndarray(results[0].plot(), format="bgr24")

#webrtc camera
webrtc_ctx = webrtc_streamer(
    key="yolo-world",
    video_processor_factory=YOLOVideoProcessor,
    async_processing=True,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={
        "video": {
        "facingMode": "environment"}, 
        "audio": False}
)

#saying detected objects out loud
if webrtc_ctx.video_processor:
    with webrtc_ctx.video_processor._lock:
        items = webrtc_ctx.video_processor.current_detections
    
    if items:
        st.write(f"🔍 **Seeing:** {', '.join(items)}")
    else:
        st.write("⚪ Scanning...")

    if st.button("📸 Capture & Read", type="primary", use_container_width=True):
        if items:
            text_to_say = f"I see {', '.join(items)}"
            st.success(text_to_say)
            audio_data=text_to_speak(text_to_say) #temporary audio file
            if audio_data:
                st.audio(audio_data, format="audio/mpeg", autoplay=True)
        else:
            warning = "Nothing detected to read."
            st.warning(warning)
            audio_data = text_to_speak(warning)
            if audio_data:
                st.audio(audio_data, format="audio/mpeg", autoplay=True)
else:
    st.info("Start the camera to begin detection.")