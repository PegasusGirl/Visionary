# YOLO - ULTRALYTICS
import collections
import collections.abc
collections.Callable = collections.abc.Callable

import streamlit as st
from ultralytics import YOLOWorld
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
from gtts import gTTS
import threading
import io
import base64
import streamlit.components.v1 as components
import time
import numpy as np
import whisper
from collections import Counter

#page details
st.set_page_config(
    page_title="Surrounding Detector",
    page_icon="📷",
    layout="wide",
)

#intializing all session states
if 'whisper_model' not in st.session_state:
    st.session_state.whisper_model = whisper.load_model("base")
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "camera_running" not in st.session_state:
    st.session_state.camera_running = False
if "last_detected" not in st.session_state:
    st.session_state.last_detected = []
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

def format_detection_sentence(items):
    """Groups items (e.g., '2 chairs') and builds a natural sentence."""
    if not items:
        return "I don't see anything clearly yet."
    
    counts = Counter(items)
    parts = []
    
    for item, count in counts.items():
        if count > 1:
            parts.append(f"{count} {item}s")
        else:
            article = "an" if item[0].lower() in 'aeiou' else "a"
            parts.append(f"{article} {item}")
            
    if len(parts) == 1:
        return f"I see {parts[0]}."
    else:
        return f"I see {', '.join(parts[:-1])} and {parts[-1]}."

#overlaying button to unlock audio
if not st.session_state.unlocked:
    welcome_text = "Surrounding Detector. This feature requires camera access for real-time detection. Allow camera access and let the AI see for you! Click the red start button to begin detection"
    audio_data = speak_audio(welcome_text)
    
    if audio_data:
        play_audio(audio_data, "welcome-id")

    #styling overlaying button
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

    #actual overlaying button
    if st.button(" ", key="gate_button", help="Click anywhere to unlock"):
        st.session_state.unlocked = True
        st.rerun()

#background gradient
page_bg_gradient = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, rgba(232, 245, 252, 0.7), rgba(252, 232, 248, 0.7));
}
</style>
"""
st.markdown(page_bg_gradient, unsafe_allow_html=True)


if st.button("← Back to Home"):
    st.switch_page("home/app.py")

#styling text & microphone for voice-activ. 
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
    /* microp. for voice-activ. */
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


st.markdown("<h1>Surrounding Detector</h1>", unsafe_allow_html=True)
st.markdown("<p class='access'>This feature requires camera access for real-time detection.</p>", unsafe_allow_html=True)
st.markdown("<p class='picture'>Allow camera access and let the AI see for you!</p>", unsafe_allow_html=True)

#loading yolo
@st.cache_resource
def load_yolo_world():
    model = YOLOWorld("yolov8m-worldv2.pt") 
    everything_list = [
        "person", "trip hazard on floor", "navigation sign", "handrail", "pedestrian crossing", "stairs", "door", "chair", "table", "phone", "keys", "wallet", "bottle", "cup", "plate", "knife", "fork", "spoon", "computer", "mouse", "keyboard", "backpack", "umbrella", "handbag", "tie", "suitcase", "bicycle", "car", "motorcycle", "bus", "train", "truck", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "dog", "cat", "bed", "toilet", "globe stand", "television", "laptop", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair dryer", "toothbrush", "pill bottle", "spectacles", "walking cane", "ramp", "elevator", "pothole", "curb", "trash can", "step", "speaker", "framed photo on the wall", "painting on the wall", "printed photo on table", "bookshelf filled with books", "religious statue", "laptop stand", "lamp", "coaster", "wall",
        "sedan", "hatchback", "station wagon", "SUV", "crossover", "pickup truck", "minivan", "van", "delivery van", "cargo van", "box truck", "semi truck", "tractor trailer", "dump truck", "garbage truck", "tow truck", "flatbed truck", "tanker truck", "cement mixer truck", "fire truck", "ladder truck", "ambulance", "police car", "school bus", "city bus", "coach bus", "double-decker bus", "tram", "subway train", "freight train", "passenger train", "high-speed train", "locomotive", "railcar", "boxcar", "flatcar", "hopper car", "caboose",
        "piano", "grand piano", "upright piano", "digital piano", "synthesizer", "MIDI keyboard", "keytar", "harpsichord", "accordion", "harmonica", "kazoo", "flute", "piccolo", "oboe", "bassoon", "clarinet", "saxophone", "trumpet", "trombone", "French horn", "tuba", "violin", "viola", "cello", "double bass", "harp", "guitar", "electric guitar", "bass guitar", "ukulele", "banjo", "mandolin", "sitar", "oud", "lute", "drum kit", "snare drum", "bass drum", "cymbal", "hi-hat", "tambourine", "maracas", "bongo drum", "conga drum", "djembe", "xylophone", "marimba", "vibraphone", "triangle", "cowbell", "gong", "metronome", "tuner", "microphone", "amplifier", "subwoofer", "mixer", "audio interface", "effects pedal", "loop pedal",
        "smartphone", "tablet", "desktop computer", "server", "monitor", "trackpad", "printer", "scanner", "router", "modem", "Wi-Fi extender", "Ethernet cable", "USB cable", "HDMI cable", "power strip", "surge protector", "charger", "battery", "power bank", "flash drive", "external hard drive", "SSD", "memory card", "graphics card", "CPU", "motherboard", "RAM stick", "cooling fan", "PC case", "server rack", "network switch", "webcam", "microphone stand", "VR headset", "AR glasses", "smart watch", "fitness tracker", "game console", "game controller", "joystick", "steering wheel controller", "drone", "camera", "tripod", "projector", "laser pointer", "calculator", "alarm clock", "radio", "walkie-talkie",
        "sofa", "armchair", "recliner", "rocking chair", "stool", "coffee table", "side table", "dining table", "desk", "cabinet", "dresser", "wardrobe", "nightstand", "bed frame", "mattress", "pillow", "blanket", "comforter", "sheet set", "curtain", "blinds", "rug", "carpet", "doormat", "table lamp", "floor lamp", "ceiling fan", "wall clock", "mirror", "picture frame", "plant pot", "recycling bin", "laundry basket", "ironing board", "iron", "vacuum cleaner", "broom", "dustpan", "mop", "bucket", "sponge", "dish rack", "soap dispenser", "toothpaste", "hair straightener", "hairbrush", "comb", "razor", "shaving cream", "perfume bottle", "deodorant stick", "tissue box", "paper towel roll", "toilet paper roll", "shower curtain", "bath mat", "towel",
        "bowl", "mug", "wine glass", "shot glass", "teaspoon", "chopsticks", "cutting board", "mixing bowl", "measuring cup", "measuring spoon", "colander", "strainer", "blender", "food processor", "toaster oven", "stovetop", "kettle", "coffee maker", "espresso machine", "freezer", "ice tray", "lunchbox", "thermos", "water bottle", "storage container", "aluminum foil", "plastic wrap", "parchment paper", "baking sheet", "roasting pan", "frying pan", "saucepan", "stock pot",
        "whiteboard", "chalkboard", "marker", "chalk", "eraser", "ruler", "protractor", "compass", "pen", "pencil", "colored pencil", "highlighter", "crayon", "marker set", "notebook", "spiral notebook", "composition book", "binder", "folder", "paper clip", "binder clip", "stapler", "tape dispenser", "glue stick", "lunch bag", "locker", "textbook", "workbook", "worksheet", "index card", "flash card", "microscope", "test tube", "beaker", "graduated cylinder", "Bunsen burner", "lab goggles", "lab coat", "globe", "map", "projector screen",
        "shopping cart", "hand basket", "checkout counter", "barcode scanner", "cash register", "receipt printer", "price tag", "freezer case", "refrigerated shelf", "bread rack", "produce bin", "egg carton", "milk jug", "juice carton", "soda bottle", "cereal box", "pasta bag", "rice bag", "flour sack", "sugar bag", "salt shaker", "pepper grinder", "spice jar", "ketchup bottle", "mustard bottle", "mayonnaise jar", "jam jar", "peanut butter jar", "cheese block", "butter stick", "yogurt cup", "ice cream tub", "bread loaf", "tortilla pack", "chip bag", "cracker box",
        "stuffed animal", "doll", "action figure", "toy car", "toy truck", "toy train", "model airplane", "LEGO bricks", "wooden blocks", "building blocks", "puzzle", "jigsaw puzzle", "board game", "card game", "video game cartridge", "playdough", "slime toy", "jump rope", "yo-yo", "kite", "frisbee", "hula hoop", "bubble wand", "toy kitchen", "toy hammer", "toy sword", "toy shield", "water gun", "squirt bottle", "sandbox", "plastic shovel", "bucket and spade", "rubber duck", "bath toy", "tricycle", "balance bike", "scooter", "skateboard", "roller skates",
        "lollipop", "hard candy", "jawbreaker", "candy cane", "caramel candy", "fudge", "chocolate bar", "chocolate truffle", "gummy bears", "gummy worms", "jelly beans", "licorice", "taffy", "marshmallow", "cotton candy", "rock candy", "sour candy", "pop rocks", "candy corn", "chocolate bunny", "chocolate egg", "peanut brittle", "nougat", "Turkish delight", "marzipan", "gumdrop", "peppermint patty", "mint candy", "butterscotch", "toffee", "caramel chew", "fruit chew", "bubble gum", "chewing gum", "wrapped candy",
        "T-shirt", "tank top", "blouse", "button-up shirt", "hoodie", "sweater", "cardigan", "jacket", "coat", "parka", "blazer", "dress", "evening gown", "jeans", "shorts", "cargo shorts", "skirt", "leggings", "sweatpants", "track pants", "overalls", "jumpsuit", "romper", "suit jacket", "dress pants", "raincoat", "windbreaker", "pajamas", "nightgown", "bathrobe", "swimsuit", "bikini", "one-piece swimsuit", "board shorts", "rash guard", "shirt",
        "baseball cap", "beanie", "beret", "fedora", "cowboy hat", "sun hat", "helmet", "hard hat", "crown", "tiara", "veil", "headband", "bandana",
        "glasses", "sunglasses", "contact lenses", "face mask", "makeup", "foundation", "concealer", "eyeshadow", "mascara", "lipstick", "lip gloss", "blush", "nail polish", "press-on nails",
        "ring", "wedding ring", "engagement ring", "necklace", "chain necklace", "pendant", "bracelet", "bangle", "earrings", "stud earrings", "hoop earrings", "brooch", "anklet", "nose ring", "body piercing",
        "tote bag", "messenger bag", "coin purse", "purse", "clutch", "carry-on bag", "duffel bag", "briefcase", "flashlight", "piece of clothing", "dumbbell weights",
        "gloves", "mittens", "fingerless gloves", "wristband", "arm sleeve", "bow tie", "scarf", "shawl", "belt", "suspenders", "sneakers", "running shoes", "boots", "work boots", "rain boots", "snow boots", "sandals", "flip-flops", "slides", "slippers", "high heels", "dress shoes", "loafers", "oxfords", "ballet flats", "rollerblades", "ice skates", "cleats",
        "socks", "ankle socks", "crew socks", "knee-high socks", "stockings", "tights", "pantyhose", "shoe laces", "insole", "shoe polish", "puppy", "kitten", "hamster", "guinea pig", "rabbit", "mouse", "rat", "horse", "cow", "sheep", "goat", "pig", "chicken", "duck", "goose", "parrot", "pigeon", "crow", "owl", "hawk", "eagle", "sparrow", "frog", "toad", "lizard", "snake", "turtle", "goldfish", "koi fish", "shark", "dolphin", "whale", "octopus", "crab", "lobster", "jellyfish", "snail", "ant", "bee", "butterfly", "dragonfly", "mosquito", "beetle", "spider", "scorpion", "centipede",
        "fire", "smoke", "toxic gas", "carbon monoxide", "radiation", "acid spill", "chemical burn", "biohazard", "virus", "bacteria", "mold", "asbestos", "lead paint", "sharp object", "broken glass", "exposed wire", "electric shock", "short circuit", "explosion", "flammable liquid", "oil spill", "fuel leak", "flood", "earthquake", "volcanic eruption", "landslide", "sinkhole", "tornado", "hurricane", "thunderstorm", "lightning strike", "blizzard", "heatwave", "wildfire", "power outage", "bridge collapse", "building collapse", "gas leak", "water contamination", "food poisoning", "choking hazard", "slip hazard", "trip hazard", "fall hazard",
        "exercise machine"
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
            self.current_detections = list(detected_this_frame)
        return av.VideoFrame.from_ndarray(results[0].plot(), format="bgr24")

#camera setup
webrtc_ctx = webrtc_streamer(
    key="yolo-world",
    video_processor_factory=YOLOVideoProcessor,
    async_processing=True,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
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


#capturing and reading
def perform_capture_and_read(items):
    sentence = format_detection_sentence(items)
    st.session_state.last_detected = items
    queue_audio(sentence)


if webrtc_ctx.video_processor:
    with webrtc_ctx.video_processor._lock:
        items = list(webrtc_ctx.video_processor.current_detections)
    
    if st.button("📸 Capture & Read", type="primary", use_container_width=True):
        st.subheader("Detected:")
        perform_capture_and_read(items)
        st.write(f"🔍 {format_detection_sentence(items)}")
    else:
        st.write("⚪ Scanning...")
else:
    st.info("Start the camera to begin detection.")

if "last_detected_sentence" in st.session_state:
    st.subheader("Detected:")
    st.write(f"🔍 {st.session_state.last_detected_sentence}")

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


            start_keywords = ["start", "begin", "camera on", "turn on", "activate"]
            stop_keywords = ["stop", "off", "end", "stop camera", "turn off"]
            detect_keywords = ["detect", "capture", "read", "what do you see", "see"]
            

            if any(kw in cmd for kw in start_keywords):
                st.session_state.camera_running = True
                st.session_state.input_key += 1
                st.rerun()

            elif any(kw in cmd for kw in stop_keywords):
                st.session_state.camera_running = False
                st.session_state.input_key += 1
                st.rerun()

            if any(kw in cmd for kw in detect_keywords):
                if st.session_state.camera_running and webrtc_ctx.video_processor:
                    with webrtc_ctx.video_processor._lock:
                        items_to_read = list(webrtc_ctx.video_processor.current_detections)
                    sentence = format_detection_sentence(items_to_read)
                    st.session_state.last_detected_sentence = sentence
                    perform_capture_and_read(items_to_read)
                    st.session_state.input_key += 1
                    st.rerun()
                else:
                    st.warning("Turn on camera first.")

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

        st.session_state.input_key += 1
        st.rerun()


#voice-commands when unlocked
if st.session_state.unlocked:
    process_audio()

if st.session_state.audio_queue:
    audio_data = speak_audio(st.session_state.audio_queue)
    if audio_data:
        play_audio(audio_data, f"play-{int(time.time())}")
    # Wipe the queue immediately so it can never play again by accident
    st.session_state.audio_queue = None
