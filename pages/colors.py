#COLOR FILTERING

import streamlit as st # pyright: ignore[reportMissingImports]
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase # pyright: ignore[reportMissingImports]
import numpy as np # pyright: ignore[reportMissingImports]
import av # pyright: ignore[reportMissingImports] 
import threading
import streamlit.components.v1 as components # pyright: ignore[reportMissingImports]


st.set_page_config(
    page_title="Color Filters",
    page_icon="🌈",
    layout="wide"
)


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
        # 1. Identify 'Red' pixels that would normally look dark/black to protanopes
        # We shift them toward PINK by adding blue.

        red_mask = np.maximum(0, R - G) 
        R_corr = R
        B_corr = np.clip(B + (red_mask * 0.7), 0, 1) # Shift red -> pink/magenta

        # 2. Identify 'Green' pixels and make them 'Neon'
        # We boost the intensity (brightness) and shift slightly toward cyan/yellow
        green_mask = np.maximum(0, G - R)
        G_corr = np.clip(G * 1.3, 0, 1) # Brighten significantly
        
        # Keep R as is or boost it slightly to make it 'Yellow-Green' (Neon)
        R_corr = np.clip(R_corr + (green_mask * 0.2), 0, 1) 
        
        corrected = np.stack([R_corr, G_corr, B_corr], axis=-1)
        
    elif mode == "Deuteranopia (Green Weak)":
        # 1. ENHANCE RED HUES (Shift toward Pink/Magenta)
        # We find areas where Red is stronger than Green and add Blue
        red_mask = np.maximum(0, R - G)
        R_corr = R
        # Adding blue to red creates Magenta, which is highly visible
        B_corr = np.clip(B + (red_mask * 0.8), 0, 1) 

        # 2. ENHANCE GREEN HUES (Shift toward Cyan/Bright Yellow)
        # We find areas where Green is stronger than Red
        green_mask = np.maximum(0, G - R)
        # Boost Green intensity and add a touch of Blue to create Cyan
        G_corr = np.clip(G * 1.25, 0, 1) 
        B_corr = np.clip(B_corr + (green_mask * 0.4), 0, 1) 

        # 3. FIX MID-RANGE CONFUSION (Browns, Dark Reds, and Rose-Pinks)
        # Rose-pink often has R > B and R > G but looks gray. 
        # We force a strong blue tint to anything that looks 'muddy'.
        confusion_mask = np.where((R > 0.3) & (R < 0.7) & (abs(R - G) < 0.1), 1.0, 0.0)
        
        # Shift these 'grayish' pinks/browns toward a distinct Blue/Violet
        B_corr = np.clip(B_corr + (confusion_mask * 0.5), 0, 1)
        
        # Darken Browns/Dark Reds to separate them from Greens
        dark_red_mask = np.where((R < 0.4) & (R > G), 1.0, 0.0)
        R_corr = np.clip(R_corr - (dark_red_mask * 0.2), 0, 1)

        corrected = np.stack([R_corr, G_corr, B_corr], axis=-1)

    elif mode == "Tritanopia (Blue Weak)":
        # 1. ENHANCE BLUES & VIOLETS (Shift toward Vivid Red/Magenta)
        # We find areas where Blue is stronger than Green
        blue_mask = np.maximum(0, B - G)
        # Adding Red to Blue creates Magenta, making 'invisible' Blue look like a warm 'pop'
        R_corr = np.clip(R + (blue_mask * 0.8), 0, 1)
        G_corr = G
        B_corr = B

        # 2. ENHANCE YELLOWS & ORANGES (Shift toward Bright Green/Cyan)
        # Yellow is naturally high R and G. We find where Yellow is strong and B is low.
        yellow_mask = np.maximum(0, (R + G) / 2 - B)
        # We shift Yellow toward Green/Cyan by boosting G and adding a Blue component
        G_corr = np.clip(G_corr + (yellow_mask * 0.3), 0, 1)
        B_corr = np.clip(B_corr + (yellow_mask * 0.5), 0, 1)
        # Reduce Red slightly in yellow areas to push it further into the 'cool' Cyan/Green range
        R_corr = np.clip(R_corr - (yellow_mask * 0.2), 0, 1)

        # 3. ENHANCE GREEN HUES (Luminosity & Contrast Shift)
        # We find 'Pure' Greens (where G is much higher than R and B)
        green_mask = np.maximum(0, G - (R + B) / 2)
        # Increase luminosity of greens and shift them slightly away from teal
        G_corr = np.clip(G_corr * 1.2, 0, 1)
        R_corr = np.clip(R_corr + (green_mask * 0.1), 0, 1) # Add a tiny bit of yellow-tint for purity

        corrected = np.stack([R_corr, G_corr, B_corr], axis=-1)
        
    else:
        # Standard fallback for other modes
        return img
       
    return (corrected * 255).astype("uint8")


class ColorBlindTransformer(VideoTransformerBase):
    def __init__(self):
        # We don't initialize with the type directly anymore.
        # We need a lock to safely access shared state.
        self.lock = threading.Lock()
        # Initialize a temporary state to hold the filter type in the transform thread
        self.colorblind_type = "None"


    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # 1. Convert video frame to numpy array and convert BGR to RGB
        img = frame.to_ndarray(format="bgr24")
        img_rgb = img[:, :, ::-1]
       
        # 2. Safely read the *current* colorblind type using the lock
        with self.lock:
            current_type = self.colorblind_type
       
        # 3. Apply the correction logic using the current type
        corrected_rgb = apply_color_correction(img_rgb, current_type)
       
        # 4. Convert back to BGR and return the processed frame
        corrected_bgr = corrected_rgb[:, :, ::-1]
        return av.VideoFrame.from_ndarray(corrected_bgr, format="bgr24")


   
def update_filter_callback(transformer_container):
    # This runs when the selectbox changes.
    # It accesses the running transformer instance and updates its internal state safely using the lock.
    if transformer_container.video_transformer:
        with transformer_container.video_transformer.lock:
            transformer_container.video_transformer.colorblind_type = st.session_state.selected_filter
            


webrtc_ctx = webrtc_streamer(
    key="real-time-correction",
    video_processor_factory=ColorBlindTransformer, # Use the class name directly
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False}
)


# Initialize session state if not present
if 'selected_filter' not in st.session_state:
    st.session_state.selected_filter = "None"


# 2. User selects the correction type AFTER the stream context is created
st.selectbox(
    "Choose Your Color-Blind Type",
    ["None", "Protanopia (Red Weak)", "Deuteranopia (Green Weak)", "Tritanopia (Blue Weak)"],
    key="selected_filter", # Bind the selectbox value to session state
    on_change=update_filter_callback, # Call this function every time the selectbox changes
    args=(webrtc_ctx,) # Pass the streamer context to the callback
)


# Display a helper message using the session state value
st.warning(
    f"Current Correction: **{st.session_state.selected_filter}**.")


if not webrtc_ctx.video_transformer:
    st.info("Click 'START' above to begin the live feed.")




