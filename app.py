#VISIONARY HOMEPAGE

import streamlit as st # pyright: ignore[reportMissingImports]
import base64
from pathlib import Path
import streamlit.components.v1 as components # pyright: ignore[reportMissingImports]


# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Visionary",
    page_icon="💡",
    layout="wide", # Essential for responsiveness
)

# --- BACKGROUND GRADIENT ---
page_bg_gradient = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, rgba(232, 245, 252, 0.7), rgba(252, 232, 248, 0.7));
    background-size: cover;
}
</style>
"""
st.markdown(page_bg_gradient, unsafe_allow_html=True)


# --- 2. TITLE STYLES (Responsive Text) ---
st.markdown ("""
    <style>
    /* Base sizes for large screens (using viewport units for flexibility) */
    h1 {
        font-size: 6vw ! important;
        text-align: center;
        letter-spacing: 1px;
        word-break: break-word;
    }

    .text {
        font-size: 2vw ! important;
        text-align: center;
        letter-spacing: 1px;    
    }


    /* Override Streamlit's main block padding for better vertical spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
   
    /* Media text for phones and tablets */
    @media (max-width: 768px) {
        h1 {
            /* Large size for mobile/tablet */
            font-size: 12vw ! important;
        }
        .text {
            /* Large size for mobile/tablet */
            font-size: 6vw ! important;
        }
    }
    </style>
""", unsafe_allow_html=True
)
st.markdown("<h1>Welcome to Visionary</h1>", unsafe_allow_html=True)
st.markdown("<p class='text'>See Beyond. Hear Beyond.</p>", unsafe_allow_html=True)




# --- 3. CSS FOR CENTERED FLEXBOX GRID & SQUARE ASPECT RATIO ---
st.markdown("""
    <style>
    /* --- CSS FLEXBOX GRID CONTAINER (Centered) --- */
    .square-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: center; /* Ensures the last row of items is centered */
        gap: 30px;
       
        /* KEY TO CENTERING THE ENTIRE GRID BLOCK */
        max-width: 1200px; /* Limit the overall width of the grid */
        margin: 0 auto;    /* Pushes equal space on left/right to center the block */
    }




    /* --- RESPONSIVE GRID ITEM (How many per row) --- */
    .grid-item {
        flex: 1 1 30%; /* Default: A flexible basis for 3 items per row */
        min-width: 200px;
        max-width: 300px;
    }
   
    /* Media for Tablet (2 items per row) */
    @media (max-width: 768px) {
        .grid-item {
            flex: 1 1 45%; /* Basis allows two items with the gap */
        }
    }
   
    /* Media Phone (1 item per row) */
    @media (max-width: 480px) {
        .grid-item {
            flex: 1 1 100%; /* Takes full width of the container */
            max-width: 100%;
        }
    }


    /* --- SQUARE IMAGE CONTAINER (The <a> tag) --- */
    .clickable-grid-link {
        display: block;
        text-decoration: none;
       
        /* CORE SQUARE FIX: Forces height = width using the padding-top hack */
        position: relative;
        width: 100%;
        padding-top: 100%; /* FORCES A SQUARE SHAPE */
        height: 0;
       
        /* Visual styles */
        border-radius: 20px !important;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1) !important;
        transition: box-shadow 0.3s ease !important;
        overflow: hidden;
        cursor: pointer !important;
    }
   
    /* --- THE IMAGE ITSELF --- */
    .clickable-grid-img {
        /* Absolute position to cover the square container */
        position: absolute;
        top: 0;
        left: 0;
        width: 100% !important;
        height: 100% !important;
       
        /* Other styles */
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



# --- HELPER FUNCTIONS TO CREATE CLICKABLE HTML ---
def get_base64_of_bin_file(bin_file):
    """Reads a binary file and returns its Base64 encoded string."""
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
    """Generates clickable HTML for a local image file."""
    img_base64 = get_base64_of_bin_file(image_file)
    if not img_base64:
        # Return an error placeholder if image is missing
        return f"""
        <div class="clickable-grid-link" style='background-color: #f8d7da; color: #721c24;
             display: flex; align-items: center; justify-content: center;
             border: 1px solid #f5c6cb; border-radius: 15px;
             text-align: center; font-size: 14px;'>
            {image_file} Missing
        </div>
        """
    # Extract image_id from filename (e.g., "city.png" -> "city")
    image_id = Path(image_file).stem
   
    # Map image ID to page links
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


# --- 4. REFRACTORED IMAGE GRID (using a single Flexbox container) ---
images = [
    "city.png",
    "rainbow.png",
    "speaker.png",
    "text.png",
    "sign.png",
    "input.png",
]




# Build the entire grid HTML string
grid_html_items = ""
for image_file in images:
    html_content = create_clickable_html(image_file)
    # Wrap each clickable item in the responsive grid-item class
    grid_html_items += f'<div class="grid-item">{html_content}</div>'


# Display the final responsive grid using a single markdown call
st.markdown(f'<div class="square-grid">{grid_html_items}</div>', unsafe_allow_html=True)









