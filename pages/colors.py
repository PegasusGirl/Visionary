#COLOR FILTERING

import streamlit as st # pyright: ignore[reportMissingImports]
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase # pyright: ignore[reportMissingImports]
import numpy as np # pyright: ignore[reportMissingImports]
import av # pyright: ignore[reportMissingImports] 
import threading

#sets page details
st.set_page_config(
    page_title="Color Filters",
    page_icon="🌈",
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


    </style>
    """, unsafe_allow_html=True
    )
st.markdown("<h1>Color Vision Assistance</h1>", unsafe_allow_html=True)
st.markdown("<p class='access'>This feature requires camera access for real-time color filtering</p>", unsafe_allow_html=True)
st.markdown("<p class='allow'>Allow camera access and see the world with color</p>", unsafe_allow_html=True)


def apply_color_correction(img, mode):
    if mode == "None":
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
        
        # Keep R as is or boost it slightly to make it 'Yellow-Green' (Neon)
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
        R_corr = np.clip(R_corr + (green_mask * 0.1), 0, 1) # Add a tiny bit of yellow-tint for purity

        #fully corrected
        corrected = np.stack([R_corr, G_corr, B_corr], axis=-1)
        
    else:
        #raw camera feed
        return img
       
    return (corrected * 255).astype("uint8")


class ColorBlindTransformer(VideoTransformerBase):
    def __init__(self):

        #intialize lock
        self.lock = threading.Lock()
        #temporary state to hold filter type
        self.colorblind_type = "None"


    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        #convert video frame to numpy array and convert bgr to rgb
        img = frame.to_ndarray(format="bgr24")
        img_rgb = img[:, :, ::-1]
       
        # Safely read current colorblind type using the lock
        with self.lock:
            current_type = self.colorblind_type
       
        #apply correction logic based on type of color blindess
        corrected_rgb = apply_color_correction(img_rgb, current_type)
       
        #convert rgb frame back bgr frame and return it
        corrected_bgr = corrected_rgb[:, :, ::-1]
        return av.VideoFrame.from_ndarray(corrected_bgr, format="bgr24")


#the filter selectbox (based on type of filter)  
def update_filter_callback(transformer_container):
    if transformer_container.video_transformer:
        with transformer_container.video_transformer.lock:
            transformer_container.video_transformer.colorblind_type = st.session_state.selected_filter
            

#webrtc camera
webrtc_ctx = webrtc_streamer(
    key="real-time-correction",
    video_processor_factory=ColorBlindTransformer,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False}
)


#intialize session state if not present
if 'selected_filter' not in st.session_state:
    st.session_state.selected_filter = "None"


#the actual filter selecbox
st.selectbox(
    "Choose Your Color-Blind Type",
    ["None", "Protanopia (Red Weak)", "Deuteranopia (Green Weak)", "Tritanopia (Blue Weak)"],
    key="selected_filter", #selectbox with session state
    on_change=update_filter_callback, #updates the filter based on the type of filter selected
    args=(webrtc_ctx,)
)

st.warning(
    f"Current Correction: **{st.session_state.selected_filter}**.")

if not webrtc_ctx.video_transformer:
    st.info("Click 'START' above to begin the live feed.")




