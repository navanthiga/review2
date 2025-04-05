
Python Learning Platform - README

🚀 Overview
This interactive platform combines AI-generated Python tutorial videos with adaptive quizzes to create an engaging learning experience. The system automatically generates educational content including scripts, animations, and voice narration for any Python topic.

✨ Features
🎥 AI-generated Python tutorial videos

📝 Adaptive quizzes with performance analysis

🎨 Manim-powered animations

🗣️ Text-to-speech narration

📊 Learning progress tracking

🛠️ Installation
Prerequisites
Python 3.8 or higher

FFmpeg (for video/audio processing)

1. Clone the Repository
```
git clone https://github.com/navanthiga/review2.git
```
2. Set Up Environment
Create a .env file in the project root with your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```
3. Install Required Packages
```
pip install manim gtts ffmpeg moviepy google-generative-ai nltk streamlit-ace streamlit pydub
```
4. Additional Setup (if needed)
For some systems, you might need to install these dependencies separately:

🏃‍♂️ Running the Application
```
streamlit run main4.py
```
The application will start and automatically open in your default browser at http://localhost:8501.

📂 Project Structure
Copy
.
├── main4.py                # Main application file
├── g_video_gen.py          # Video generation module
├── s_quiz.py               # Quiz generation module
├── .env                    # Environment configuration
├── requirements.txt        # Python dependencies
├── media/                  # Generated media files
├── output/                 # Final video outputs
└── audio/                  # Generated audio files

