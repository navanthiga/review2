import streamlit as st
import os
import re
from g_video_gen import (
    setup_gemini_api, generate_script, generate_manim_code, 
    render_manim_animation, generate_audio, merge_video_audio
)
from s_quiz import (
    generate_mcqs, start_assessment, submit_answer, restart,
    analyze_performance, display_performance_charts, get_feedback_and_resources
)

# Set page config
st.set_page_config(
    page_title="Python Learning Platform",
    page_icon="🐍",
    layout="wide"
)

# Initialize all session state variables
def init_session_state():
    required_states = {
        'auth_status': False,
        'user': None,
        'page': "dashboard",
        # Video generator state
        'script': None,
        'manim_code': None,
        'video_path': None,
        'audio_path': None,
        'final_video_path': None,
        'api_key_valid': False,
        'video_topic': "",
        # Quiz generator state
        'questions': [],
        'current_question': 0,
        'score': 0,
        'completed': False,
        'answers': {},
        'topic': "",  # This is the key fix - matching s_quiz.py expectation
        'question_categories': {}
    }
    
    for key, default_value in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Initialize session state
init_session_state()

# Navigation functions
def navigate_to_dashboard():
    st.session_state.page = "dashboard"

def navigate_to_video_generator():
    st.session_state.page = "video_generator"

def navigate_to_quiz_generator():
    st.session_state.page = "quiz_generator"

# Simple login system
def login_page():
    st.title("Python Learning Platform")
    st.markdown("#### Learn Python through interactive videos and quizzes")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if username and password:
                st.session_state.user = {"username": username}
                st.session_state.auth_status = True
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Please enter both username and password")

# Dashboard page
def dashboard_page():
    st.title(f"Welcome, {st.session_state.user['username']}")
    st.markdown("""
    ### What would you like to do today?
    - 🎥 Create custom Python tutorial videos
    - 📝 Test your knowledge with adaptive quizzes
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Video Generator", use_container_width=True):
            navigate_to_video_generator()
    with col2:
        if st.button("Quiz Generator", use_container_width=True):
            navigate_to_quiz_generator()

# Video generator page
def video_generator_page():
    st.title("🐍 Python Tutorial Video Generator")
    st.markdown("Create custom Python tutorial videos with AI-generated animations and narration")
    
    st.session_state.video_topic = st.text_input(
        "Enter a Python topic (e.g., 'Lists', 'Recursion')",
        value=st.session_state.video_topic
    )
    
    if st.button("Generate Tutorial", disabled=not st.session_state.video_topic):
        with st.spinner("Generating tutorial..."):
            # Reset previous results
            st.session_state.script = None
            st.session_state.manim_code = None
            st.session_state.video_path = None
            st.session_state.audio_path = None
            st.session_state.final_video_path = None
            
            # Generate content
            st.session_state.script = generate_script(st.session_state.video_topic)
            
            if st.session_state.script:
                st.session_state.manim_code = generate_manim_code(
                    st.session_state.video_topic, 
                    st.session_state.script
                )
                
                if st.session_state.manim_code:
                    st.session_state.video_path = render_manim_animation(
                        st.session_state.manim_code, 
                        st.session_state.video_topic
                    )
                    
                    if st.session_state.video_path:
                        st.session_state.audio_path = generate_audio(
                            st.session_state.script, 
                            st.session_state.video_topic
                        )
                        
                        if st.session_state.audio_path:
                            st.session_state.final_video_path = merge_video_audio(
                                st.session_state.video_path, 
                                st.session_state.audio_path, 
                                st.session_state.video_topic
                            )
    
    # Display results
    if st.session_state.final_video_path:
        st.success("Tutorial generated successfully!")
        st.video(st.session_state.final_video_path)
        
        with open(st.session_state.final_video_path, "rb") as file:
            st.download_button(
                label="Download Video",
                data=file,
                file_name=f"{st.session_state.video_topic.replace(' ', '_')}_tutorial.mp4",
                mime="video/mp4"
            )
        
        if st.button("Generate Quiz on This Topic"):
            st.session_state.topic = st.session_state.video_topic  # Set the expected variable name
            navigate_to_quiz_generator()
            start_assessment()
            st.rerun()

# Quiz generator page
def quiz_generator_page():
    st.title("📚 Python Quiz Generator")
    
    if not st.session_state.questions:
        st.markdown("Test your Python knowledge with adaptive quizzes")
        st.session_state.topic = st.text_input(  # Using the expected variable name
            "Enter a Python topic for the quiz",
            value=st.session_state.topic
        )
        
        if st.button("Start Quiz", disabled=not st.session_state.topic):
            # Initialize quiz state
            st.session_state.questions = []
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.completed = False
            st.session_state.answers = {}
            st.session_state.question_categories = {}
            
            start_assessment()
            st.rerun()
    else:
        # Display current question
        q_idx = st.session_state.current_question
        question = st.session_state.questions[q_idx]
        
        st.subheader(f"Question {q_idx + 1} of {len(st.session_state.questions)}")
        st.write(question["question"])
        
        # Display options
        selected = st.radio(
            "Select your answer:", 
            question["options"], 
            key=f"q_{q_idx}"
        )
        st.session_state.answers[q_idx] = selected
        
        if st.button("Submit Answer"):
            submit_answer(q_idx)
            st.rerun()
        
        # Show progress
        st.progress((q_idx + 1) / len(st.session_state.questions))
        
        if st.session_state.completed:
            st.success(f"Quiz complete! Score: {st.session_state.score}/{len(st.session_state.questions)}")
            
            # Performance analysis
            performance, strengths, weaknesses = analyze_performance()
            display_performance_charts(performance)
            
            # Feedback
            feedback = get_feedback_and_resources(
                strengths, 
                weaknesses, 
                st.session_state.topic
            )
            st.markdown(feedback)
            
            if st.button("New Quiz"):
                restart()
                st.rerun()
            
            if st.button("Create Video Tutorial"):
                st.session_state.video_topic = st.session_state.topic
                navigate_to_video_generator()
                st.rerun()

# Main app logic
if not st.session_state.auth_status:
    login_page()
else:
    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div class="logo-container">
            <h2>Python Learning</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.write(f"Welcome, {st.session_state.user['username']}")
        
        if st.button("🏠 Dashboard"):
            navigate_to_dashboard()
        if st.button("🎥 Video Generator"):
            navigate_to_video_generator()
        if st.button("📝 Quiz Generator"):
            navigate_to_quiz_generator()
        
        st.markdown("---")
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Page routing
    if st.session_state.page == "dashboard":
        dashboard_page()
    elif st.session_state.page == "video_generator":
        video_generator_page()
    elif st.session_state.page == "quiz_generator":
        quiz_generator_page()

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center;'>Python Learning Platform</div>", unsafe_allow_html=True)