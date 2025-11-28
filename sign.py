"""
ASL Translator Application
Main Streamlit application for ASL translation and communication
"""


import streamlit as st
import numpy as np
import av
from datetime import datetime
import time
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration, WebRtcMode
from modules import ASLRecognizer, SpeechToText, TextToSpeech, ConversationLogger
from config import Config




# Page configuration
st.set_page_config(
   page_title="ASL Translator",
   page_icon="🤟",
   layout="wide",
   initial_sidebar_state="expanded"
)


# Custom CSS for accessibility and better UI
st.markdown("""
<style>
   /* Large, readable fonts */
   .big-font {
       font-size: 32px !important;
       font-weight: bold;
       padding: 20px;
       background-color: #f0f2f6;
       border-radius: 10px;
       margin: 10px 0;
   }


   .asl-text {
       font-size: 28px !important;
       color: #1f77b4;
       font-weight: bold;
       padding: 15px;
       background-color: #e3f2fd;
       border-left: 5px solid #1f77b4;
       border-radius: 5px;
       margin: 10px 0;
   }


   .speech-text {
       font-size: 28px !important;
       color: #2ca02c;
       font-weight: bold;
       padding: 15px;
       background-color: #e8f5e9;
       border-left: 5px solid #2ca02c;
       border-radius: 5px;
       margin: 10px 0;
   }


   .status-box {
       font-size: 18px;
       padding: 10px;
       border-radius: 5px;
       margin: 5px 0;
   }


   .stButton>button {
       font-size: 20px !important;
       padding: 15px 30px !important;
       border-radius: 10px !important;
       font-weight: bold !important;
   }


   /* High contrast for accessibility */
   .stSelectbox label, .stCheckbox label {
       font-size: 18px !important;
       font-weight: bold !important;
   }


   /* Message history styling */
   .message-history {
       max-height: 400px;
       overflow-y: auto;
       padding: 10px;
       background-color: #fafafa;
       border-radius: 10px;
       border: 2px solid #ddd;
   }


   .message-item {
       padding: 10px;
       margin: 5px 0;
       border-radius: 5px;
       font-size: 16px;
   }


   .message-asl {
       background-color: #e3f2fd;
       border-left: 4px solid #1f77b4;
   }


   .message-speech {
       background-color: #e8f5e9;
       border-left: 4px solid #2ca02c;
   }
</style>
""", unsafe_allow_html=True)




def initialize_session_state():
   """Initialize Streamlit session state variables"""
   if 'asl_recognizer' not in st.session_state:
       st.session_state.asl_recognizer = ASLRecognizer()


   if 'speech_to_text' not in st.session_state:
       st.session_state.speech_to_text = SpeechToText()


   if 'text_to_speech' not in st.session_state:
       st.session_state.text_to_speech = TextToSpeech()


   if 'conversation_logger' not in st.session_state:
       st.session_state.conversation_logger = ConversationLogger()


   if 'camera_active' not in st.session_state:
       st.session_state.camera_active = False


   if 'listening_active' not in st.session_state:
       st.session_state.listening_active = False


   if 'current_asl_text' not in st.session_state:
       st.session_state.current_asl_text = ""


   if 'current_speech_text' not in st.session_state:
       st.session_state.current_speech_text = ""


   if 'last_gesture' not in st.session_state:
       st.session_state.last_gesture = None


   if 'conversation_active' not in st.session_state:
       st.session_state.conversation_active = False


   if 'asl_sentence' not in st.session_state:
       st.session_state.asl_sentence = []


   if 'camera_object' not in st.session_state:
       st.session_state.camera_object = None


   if 'frame_count' not in st.session_state:
       st.session_state.frame_count = 0


   if 'last_refresh_time' not in st.session_state:
       st.session_state.last_refresh_time = time.time()


   if 'auto_refresh_enabled' not in st.session_state:
       st.session_state.auto_refresh_enabled = True




class ASLVideoTransformer(VideoTransformerBase):
   """Video transformer to process frames and detect ASL gestures."""
   def __init__(self, asl_recognizer):
       self.asl_recognizer = asl_recognizer
       self.status_placeholder = st.empty()
       self.last_gesture_update = time.time()


   def recv(self, frame):
       img = frame.to_ndarray(format="bgr24")
      
       annotated_frame, gesture, confidence = self.asl_recognizer.process_frame(img)


       # Update gesture display periodically
       if gesture and (time.time() - self.last_gesture_update > 1):
            if gesture != st.session_state.last_gesture:
               st.session_state.asl_sentence.append(gesture)
               st.session_state.last_gesture = gesture
               self.status_placeholder.success(f"✅ Detected: **{gesture}** (Confidence: {confidence:.2f})")
               self.last_gesture_update = time.time()
            elif gesture:
               self.status_placeholder.info(f"👁️ Tracking: **{gesture}** (Confidence: {confidence:.2f})")
            else:
               st.session_state.last_gesture = None
               self.status_placeholder.info("👋 Show a hand gesture...")


       return av.VideoFrame.from_ndarray(annotated_frame, format="bgr24")

initialize_session_state()

def main():
   """Main application function"""


   def create_video_transformer():
       return ASLVideoTransformer(st.session_state.asl_recognizer)


   # Title
   st.title("🤟 ASL Translator")
   st.markdown("### Bridging Communication Between Deaf and Hearing Communities")


   # Sidebar for settings and conversation management
   with st.sidebar:
       st.header("⚙️ Settings")


       # Conversation controls
       st.subheader("Conversation")


       if not st.session_state.conversation_active:
           if st.button("🆕 Start New Conversation", use_container_width=True):
               st.session_state.conversation_logger.start_new_conversation()
               st.session_state.conversation_active = True
               st.session_state.asl_sentence = []
               st.session_state.current_asl_text = ""
               st.session_state.current_speech_text = ""
               st.success("New conversation started!")
               st.rerun()
       else:
           if st.button("💾 Save & End Conversation", use_container_width=True):
               filepath = st.session_state.conversation_logger.save_conversation()
               if filepath:
                   st.success(f"Conversation saved!")
                   st.session_state.conversation_active = False
                   st.session_state.asl_sentence = []
                   st.rerun()


       st.divider()


       # Speech recognition controls
       st.subheader("Voice Input")
       if st.button("🎤 Listen to Speech", use_container_width=True):
           with st.spinner("Listening..."):
               text, success = st.session_state.speech_to_text.listen_once()
               if success and text:
                   st.session_state.current_speech_text = text
                   if st.session_state.conversation_active:
                       st.session_state.conversation_logger.add_message(
                           'hearing_person', text, 'speech'
                       )
                   st.rerun()


       st.divider()


       # ASL sentence controls
       st.subheader("ASL Controls")
       if st.button("🗣️ Speak ASL Sentence", use_container_width=True):
           if st.session_state.asl_sentence:
               sentence = " ".join(st.session_state.asl_sentence)
               st.session_state.text_to_speech.speak(sentence, blocking=False)
               st.session_state.current_asl_text = sentence
               if st.session_state.conversation_active:
                   st.session_state.conversation_logger.add_message(
                       'deaf_person', sentence, 'asl'
                   )


       if st.button("🔄 Clear ASL Sentence", use_container_width=True):
           st.session_state.asl_sentence = []
           st.session_state.asl_recognizer.reset_gesture_buffer()
           st.rerun()


       st.divider()


       # View past conversations
       st.subheader("📚 Past Conversations")
       conversations = st.session_state.conversation_logger.list_conversations()


       if conversations:
           for conv in conversations[:5]:  # Show last 5
               with st.expander(f"{conv['start_time']} ({conv['message_count']} messages)"):
                   if st.button("Load", key=f"load_{conv['filename']}"):
                       data = st.session_state.conversation_logger.load_conversation(conv['filename'])
                       if data:
                           st.write("**Messages:**")
                           for msg in data['messages']:
                               sender = "🤟 ASL" if msg['sender'] == 'deaf_person' else "🗣️ Speech"
                               st.write(f"{sender}: {msg['message']}")


                   if st.button("Export to Text", key=f"export_{conv['filename']}"):
                       output_path = st.session_state.conversation_logger.export_to_text(conv['filename'])
                       if output_path:
                           st.success(f"Exported to {output_path}")
       else:
           st.info("No saved conversations yet")


   # Main content area
   col1, col2 = st.columns(2)


   with col1:
       st.header("📹 ASL Recognition")


       webrtc_ctx = webrtc_streamer(
           key="asl-video",
           mode=WebRtcMode.SENDRECV,
           rtc_configuration=RTCConfiguration(
               {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
           ),
           video_processor_factory=create_video_transformer,
           media_stream_constraints={"video": True, "audio": False},
           async_processing=True,
       )


       # Display current ASL sentence
       st.subheader("Current ASL Sentence")
       if st.session_state.asl_sentence:
           sentence = " ".join(st.session_state.asl_sentence)
           st.markdown(f'<div class="asl-text">🤟 {sentence}</div>', unsafe_allow_html=True)
       else:
           st.markdown('<div class="asl-text">🤟 (empty)</div>', unsafe_allow_html=True)


   with col2:
       st.header("🗣️ Speech Recognition")


       # Display recognized speech
       st.subheader("Recognized Speech")
       if st.session_state.current_speech_text:
           st.markdown(f'<div class="speech-text">🎤 {st.session_state.current_speech_text}</div>',
                      unsafe_allow_html=True)
       else:
           st.markdown('<div class="speech-text">🎤 Click "Listen to Speech" to start</div>',
                      unsafe_allow_html=True)


       st.divider()


       # Conversation history
       st.subheader("💬 Conversation History")
       if st.session_state.conversation_active:
           messages = st.session_state.conversation_logger.get_current_conversation()


           if messages:
               # Create scrollable message history
               history_html = '<div class="message-history">'
               for msg in messages[-10:]:  # Show last 10 messages
                   msg_class = "message-asl" if msg['sender'] == 'deaf_person' else "message-speech"
                   sender_icon = "🤟" if msg['sender'] == 'deaf_person' else "🗣️"
                   sender_label = "ASL" if msg['sender'] == 'deaf_person' else "Speech"


                   history_html += f'''
                   <div class="message-item {msg_class}">
                       <strong>{sender_icon} {sender_label}</strong>
                       <span style="color: #666; font-size: 12px;">({msg['timestamp']})</span><br/>
                       {msg['message']}
                   </div>
                   '''
               history_html += '</div>'


               st.markdown(history_html, unsafe_allow_html=True)
           else:
               st.info("No messages yet. Start communicating!")


           # Show conversation stats
           summary = st.session_state.conversation_logger.get_conversation_summary()
           st.metric("Total Messages", summary['message_count'])
           col_a, col_b = st.columns(2)
           with col_a:
               st.metric("ASL Messages", summary['asl_messages'])
           with col_b:
               st.metric("Speech Messages", summary['speech_messages'])
           st.metric("Duration", summary['duration'])
       else:
           st.info("Start a new conversation to begin!")


   # Instructions at the bottom
   with st.expander("ℹ️ How to Use"):
       st.markdown("""
       ### Getting Started
       1. **Start a Conversation**: Click "Start New Conversation" in the sidebar
       2. **Enable Camera**: Turn on the camera to recognize ASL hand gestures
       3. **Show Gestures**: Make ASL hand signs in front of the camera
       4. **Build Sentence**: Recognized gestures are added to your sentence
       5. **Speak Sentence**: Click "Speak ASL Sentence" to voice your message
       6. **Capture Speech**: Click "Listen to Speech" to capture voice input
       7. **Save**: Click "Save & End Conversation" when done


       ### Supported ASL Gestures
       - The new model supports a wide range of ASL gestures, including the full alphabet and various words.
       - For a full list of supported gestures, please refer to the project documentation.


       ### Accessibility Features
       - Large, high-contrast text
       - Clear visual feedback
       - Text-to-speech for ASL translations
       - Speech-to-text for voice input
       - Conversation history and saving


       ### Tips
       - Hold gestures steady for clear recognition
       - Good lighting improves accuracy
       - Position your hand clearly in frame
       - Clear the sentence if you make a mistake
       """)




if __name__ == "__main__":
   main()

