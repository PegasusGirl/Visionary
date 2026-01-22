import streamlit as st # pyright: ignore[reportMissingImports]

pg = st.navigation([
    st.Page("home/app.py", title="Visionary Homepage", icon="💡"),
    st.Page("pages/detector.py", title="Surrounding Detector", icon="📷"),
    st.Page("pages/colors.py", title="Color Vision Filter", icon="🌈"),
    st.Page("pages/text.py", title="Text to Speech Reader", icon="🔊"),
    st.Page("pages/speech.py", title="Speech to Text", icon="📝"),
    st.Page("pages/sign.py", title="Sign Language Translator", icon="🤘"),
    st.Page("pages/input.py", title="Text to Audio Converter", icon="💬")
])

pg.run()