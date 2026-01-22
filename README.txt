-----------------------------------------------------------------------------------
Visionary Application
-----------------------------------------------------------------------------------
TSA Software Development Event
-----------------------------------------------------------------------------------
Overview:

This application was developed for the Technology Student Association (TSA) Software Development event with the goal of improving accessibility for individuals with visual or hearing disabilities. The project integrates computer vision, speech processing, and real-time translation technologies to enhance communication and environmental awareness.
-----------------------------------------------------------------------------------
Functionality and Purpose:

The purpose of this application is to increase accessibility and independence for individuals with visual or hearing impairments through real-time detection, translation, and audio-visual assistance.
-----------------------------------------------------------------------------------
Features:

Surroundings Detector (Visual Impairments):
    Detects nearby objects using the device camera, identifies them, and verbally announces what is detected to help visually impaired users understand their environment.

Color Filtering (Visual Impairments):
    Applies adaptive color filters to the camera feed to enhance color contrast for users with different types of color blindness, making hard-to-distinguish colors easier to see.

Text-to-Speech Detector (Visual Impairments):
    Uses Optical Character Recognition (OCR) to detect written text from the camera feed and reads the detected text aloud.

Speech-to-Text Transcription (Hearing Impairments):
    Converts spoken language into real-time text to support communication for individuals who are deaf or hard of hearing.

ASL Translator (Hearing Impairments):
    Translates American Sign Language (ASL) into text in real time, enabling users who cannot hear to communicate effectively with others.

Text Input to Audio Converter (Visual Impairments):
    Converts typed text into spoken audio, allowing visually impaired users to understand written content through speech output.
-----------------------------------------------------------------------------------
Software Dependencies:

Python Version: 3.11.9

Download URL:
	https://www.python.org/downloads/
-----------------------------------------------------------------------------------
Additional Dependencies:

Install all required Python packages using:

    pip install -r requirements.txt
-----------------------------------------------------------------------------------
Mobile Application Support:

To enable access on mobile devices, Cloudflare Tunnel must be installed.

Download URL:
    https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/
-----------------------------------------------------------------------------------
Additional Installation Instructions:

Method - 1 (GitHub Method)
	Follow the isntructions as below to download full content from GitHub
	- git clone https://github.com/PegasusGirl/Visionary
	- Unzip/extract venv_311.zip 

Method - 2 (If "Visionary App" archive file is locally available)
	1. If available, unzip "Visionary App.zip" under C:\users\<Username> where <Username> is the name of the user logged in (Alternate folder location could be chosen)
	2. Install Python environment, execute the following commands (requires Internet)
		>python -m venv venv_311

MANDATORY STEP:
	- Open Command Prompt using "Run as Administrator" option
	- Execute command:
		>powershell Set-ExecutionPolicy RemoteSigned

NOTE: A fully operational preconfigured, Python environment could be made available in a USB drive.
-----------------------------------------------------------------------------------
Running the Program:

1. Open the run_app.bat file.

2. The website will request permission on the first launch and then open automatically on the local device.

3. After approximately 4 seconds, an HTTPS URL will appear in the command prompt inside a dashed-line box.

4. Open this HTTPS link on a mobile device to access the web application.
-----------------------------------------------------------------------------------
Notes:

This application is conceptual and was designed with accessibility, usability, and inclusivity as its core principles, aligning with TSA’s emphasis on real-world problem solving through technology.

Please watch the demonstration video, "Program_Demo.mp4," for more details (May require Media Player or similar to view the video).
-----------------------------------------------------------------------------------
