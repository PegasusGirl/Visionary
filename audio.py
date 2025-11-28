import streamlit as st
import streamlit.components.v1 as components

def list_voices_debug():
    js_code = """
    <script>
        function logVoices() {
            let voices = window.speechSynthesis.getVoices();
            if (voices.length === 0) {
                console.log("Voices not yet loaded. Waiting for 'voiceschanged' event.");
            } else {
                console.log("--- Available Voices ---");
                voices.forEach(voice => {
                    console.log(`Name: ${voice.name} | Lang: ${voice.lang} | Default: ${voice.default}`);
                });
                console.log("--------------------------");
            }
        }

        // Wait for voices to load
        window.speechSynthesis.onvoiceschanged = logVoices;
        // Also run once in case they are already loaded
        logVoices();
    </script>
    """
    components.html(js_code, height=0, width=0)

# --- Streamlit App ---
st.title("Voice Debugger")
st.markdown("Open your browser's **Developer Tools** (press `F12` or right-click -> Inspect, then go to the **Console** tab) to see the list of exact voice names.")

list_voices_debug()
