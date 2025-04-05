import os
import google.generativeai as genai
import subprocess
import json
import hashlib
import glob
import shutil
import re
import sys
import threading
import tempfile
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.editor import vfx
import tempfile  # Add this if not already imported

# Set page config
st.set_page_config(
    page_title="Python Tutorial Generator",
    page_icon="🐍",
    layout="wide"
)

# App title and description
st.title("🐍 Python Tutorial Video Generator")
st.markdown("""
This application generates educational Python tutorial videos using AI. 
It creates a script, Manim animation, and voice narration for any Python topic you choose.
""")

# Configure Gemini API
def setup_gemini_api(api_key=None):
    """Set up the Gemini API with the provided key or from environment variables"""
    try:
        # If no API key is provided, try to get it from environment variables
        if api_key is None:
            import os
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                st.error("No API key found in environment variables")
                return False
        
        # Configure Gemini with the API key
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Failed to configure Gemini API: {str(e)}")
        return False

# Generate script using Gemini API
def generate_script(topic):
    try:
        with st.spinner("Generating script with Gemini..."):
            model = genai.GenerativeModel('gemini-1.5-pro')
            generation_config = {
                "temperature": 0.2,
                "max_output_tokens": 8192
            }

            prompt = f"""
            Create a comprehensive educational script about {topic} for a Python educational video.

            Format the script exactly like this example:

            Welcome to Python Lists! ...

            Lists are ordered collections of items in Python.
            They can store multiple values of different types in a single variable.

            In Python, a list looks like this: ...

            numbers = [10, 20, 30, 40]

            Here, numbers is a list containing four values.
            We use square brackets [] to define a list.

            Lists are mutable, meaning you can change their content after creation.
            Let's explore lists in more detail!

            You can access elements in a list using their index position.
            Python uses zero-based indexing, so the first element is at index 0.

            [Continue with detailed explanation, examples, and use cases]

            Great job! ...

            Today, we learned:
            ✔ How to create and access lists
            ✔ How to modify list contents
            ✔ Common list operations and methods
            ✔ When to use lists in your programs

            Keep practicing, and you'll master Python in no time!

            Make sure the script:
            1. Has a clear introduction to the concept
            2. Provides code examples with explanations
            3. Covers all important aspects of {topic}
            4. Has a summary with 4-5 key points at the end
            5. Is detailed enough for a 5-7 minute educational video
            6. Uses simple language suitable for beginners
            7. Includes encouragement and motivation
            """

            response = model.generate_content(prompt, generation_config=generation_config)
            return response.text
    except Exception as e:
        st.error(f"Failed to generate script: {str(e)}")
        return f"Error generating script for {topic}. Please try again."

# Validate Manim code
def validate_manim_code(manim_code):
    """Check if the Manim code is syntactically valid Python"""
    try:
        # Print the raw input for debugging
        print("VALIDATING CODE:")
        print(manim_code[:200] + "..." if len(manim_code) > 200 else manim_code)

        # Remove any potential markdown code block markers
        cleaned_code = manim_code

        # Look for the actual Python class in case the code is wrapped in markdown
        class_pattern = re.compile(r'class\s+\w+\s*\(\s*Scene\s*\)\s*:')
        class_match = class_pattern.search(cleaned_code)

        if not class_match:
            print("No class definition found in initial search")

            # Try to extract code from markdown blocks
            code_block_pattern = re.compile(r'```(?:python)?(.*?)```', re.DOTALL)
            code_blocks = code_block_pattern.findall(cleaned_code)

            if code_blocks:
                # Use the largest code block that contains a class definition
                for block in sorted(code_blocks, key=len, reverse=True):
                    if 'class' in block and 'Scene' in block:
                        cleaned_code = block.strip()
                        print(f"Found class in code block, length: {len(cleaned_code)}")
                        break

        # Basic check for required elements
        if "class" not in cleaned_code:
            return False, "No class definition found in the code"

        if "def construct(self):" not in cleaned_code:
            return False, "No construct method found"

        # If we get here, basic structure looks good, try to ensure the code is clean
        # Remove initial/trailing backticks and any extra whitespace
        cleaned_code = cleaned_code.strip('`').strip()

        # Attempt to compile the code
        try:
            compile(cleaned_code, '<string>', 'exec')
            return True, cleaned_code
        except SyntaxError as e:
            # If compilation fails, we may need a more thorough cleaning
            print(f"Compilation failed: {str(e)}")

            # Try to extract just the Python class and related code
            try:
                # Find the start of the first class definition
                class_start = cleaned_code.find("class ")
                if class_start >= 0:
                    # Extract from class definition to the end
                    class_code = cleaned_code[class_start:]
                    # Validate this extracted portion
                    compile(class_code, '<string>', 'exec')
                    return True, class_code
            except Exception:
                pass

            return False, str(e)

    except Exception as e:
        return False, str(e)

# Add a fallback function to create a minimal valid Manim class
def create_fallback_manim_class(topic, safe_topic):
    return f"""from manim import *

class {safe_topic}(Scene):
    def construct(self):
        # Introduction
        self.introduction_to_{safe_topic.lower()}()
        self.wait(5)

        # Main content
        self.main_content()
        self.wait(5)

        # Conclusion
        self.conclusion()
        self.wait(5)

    def introduction_to_{safe_topic.lower()}(self):
        title = Text("{topic}", font_size=40, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(75)

        subtitle = Text("Introduction", font_size=30)
        subtitle.next_to(title, DOWN, buff=0.5)
        self.play(Write(subtitle))
        self.wait(75)

        self.play(FadeOut(title), FadeOut(subtitle))

    def main_content(self):
        title = Text("Main Concepts", font_size=40, color=GREEN)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(75)

        points = VGroup(
            Text("• First key point", font_size=24),
            Text("• Second key point", font_size=24),
            Text("• Third key point", font_size=24)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        points.next_to(title, DOWN, buff=1)

        for point in points:
            self.play(Write(point))
            self.wait(0.5)

        self.wait(75)
        self.play(FadeOut(title), FadeOut(points))

    def conclusion(self):
        title = Text("Conclusion", font_size=40, color=RED)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(75)

        summary = Text("Thank you for watching!", font_size=30)
        summary.next_to(title, DOWN, buff=1)
        self.play(Write(summary))
        self.wait(75)

        self.play(FadeOut(title), FadeOut(summary))
"""

# Generate Manim code using Gemini API
def generate_manim_code(topic, script):
    try:
        with st.spinner("Generating Manim animation code with Gemini..."):
            model = genai.GenerativeModel('gemini-1.5-pro')
            generation_config = {
                "temperature": 0.2,
                "max_output_tokens": 8192
            }

            safe_topic = topic.replace(' ', '').replace('-', '_')

            # Make the prompt more specific about providing a complete class
            prompt = f"""
            Create COMPLETE Manim code for an educational video about "{topic}" based on this script:

            {script}

            CRITICAL: YOU MUST PROVIDE THE ENTIRE MANIM CODE AS A COMPLETE CLASS, not just snippets.

            Requirements:

              1. Create a Manim Scene class named {safe_topic}
              2. Divide the content into 5-6 separate methods, each handling one section
              3. Each method should be 40-50 seconds in animation length
              4. Include engaging visual elements (arrows, highlights, color changes)
              5. Use a clean, educational style with good typography
              6. IMPORTANT: INCLUDE ALL CODE for EACH method - NO placeholder comments like  "# ... (similar structure)"
              7. IMPORTANT: The final construct method must call each section method with self.wait(0.1) between them
              8. IMPORTANT: Each section method must include all animations and cleanup with FadeOut at the end
              9. IMPORTANT: DO NOT use the Code class, ONLY use Text class for code examples
              10. Add self.wait() appropriately to make each section 40-50 seconds long
              11. CRITICAL: DO NOT use the t2c parameter in Text objects at all
              12. Instead of using t2c, create separate Text objects for different parts and color them individually, then group them together with VGroup
              13. CRITICAL: Do not include any SVGs or images
              14. CRITICAL: Each method must properly clean up all elements with FadeOut before ending
              15.VERY CRITICAL: Do not overwrite,Make sure you donot overwrite
              16.VERY VERY CRITICAL : Each section should be around 50 seconds which is very important

            Your response should contain only the complete Python code with no explanations, like this:

            ```python
            from manim import *

            class {safe_topic}(Scene):
                def construct(self):
                    # Introduction
                    self.introduction_to_{safe_topic.lower()}()
                    self.wait(0.1)

                    # [Additional methods called here]

                    # Conclusion
                    self.recap_and_conclusion()
                    self.wait(0.1)

                def introduction_to_{safe_topic.lower()}(self):
                    title = Text("{topic}: Introduction", font_size=40, color=BLUE)
                    title.to_edge(UP)
                    self.play(Write(title))
                    self.wait(1)

                    # [Rest of the method code]

                    self.play(FadeOut(title), FadeOut(explanation))

                # [All other methods defined here]
            ```

            Make sure your code contains a complete class definition with all methods fully implemented.
            """

            response = model.generate_content(prompt, generation_config=generation_config)
            manim_code = response.text

            print("ORIGINAL RESPONSE FROM GEMINI:")
            print(manim_code[:200] + "..." if len(manim_code) > 200 else manim_code)

            # Extract code from a code block if it exists
            code_block_pattern = re.compile(r'```(?:python)?(.*?)```', re.DOTALL)
            code_blocks = code_block_pattern.findall(manim_code)

            if code_blocks:
                # Use the largest code block
                cleaned_code = max(code_blocks, key=len).strip()
            else:
                # If no code blocks found, clean up the raw text
                cleaned_code = manim_code.strip()

            # If we still don't have a class definition, create a fallback minimal class
            if "class" not in cleaned_code or "def construct(self):" not in cleaned_code:
                print("WARNING: No valid class found in Gemini response, creating fallback class")
                cleaned_code = create_fallback_manim_class(topic, safe_topic)

            print("AFTER CLEANING:")
            print(cleaned_code[:200] + "..." if len(cleaned_code) > 200 else cleaned_code)

            return cleaned_code
    except Exception as e:
        st.error(f"Failed to generate Manim code: {str(e)}")
        return f"Error generating Manim code for {topic}. Please try again."

def render_manim_animation(manim_code, topic):
    try:
        with st.spinner("Rendering animation (this may take a few minutes)..."):
            # Create a unique temporary directory for rendering
            temp_dir = tempfile.mkdtemp()
            
            # Status placeholder for tracking progress
            status_placeholder = st.empty()
            status_placeholder.info("Setting up Manim rendering environment...")
            
            try:
                # Validate the code
                is_valid, result = validate_manim_code(manim_code)
                if not is_valid:
                    status_placeholder.error(f"Generated Manim code has syntax errors: {result}")
                    status_placeholder.info("Attempting to fix the code...")
                    fixed_code = manim_code
                    for delimiter in ["```python", "```", "'''python", "'''"]:
                        if delimiter in fixed_code:
                            parts = fixed_code.split(delimiter)
                            if len(parts) > 1:
                                fixed_code = parts[1]
                                break
                    fixed_code = fixed_code.strip()
                    is_valid, result = validate_manim_code(fixed_code)
                    if not is_valid:
                        status_placeholder.error(f"Could not fix code: {result}")
                        return None
                    manim_code = fixed_code
                else:
                    manim_code = result

                # Prepare class and file names
                safe_topic = topic.replace(' ', '_').replace("'", "").replace('"', '')
                class_name = topic.replace(' ', '').replace('-', '_')

                # Ensure we use absolute paths for media output
                media_dir = os.path.join(temp_dir, "media")
                os.makedirs(media_dir, exist_ok=True)
                
                # Create the necessary subdirectories
                for quality in ["720p30", "1080p60", "480p15"]:
                    os.makedirs(os.path.join(media_dir, "videos", quality), exist_ok=True)
                    os.makedirs(os.path.join(media_dir, "videos", quality, "partial_movie_files", class_name), exist_ok=True)
                
                # Add rendering code with explicit quality and output path settings
                render_code = f"""
# Configure Manim with explicit paths
import os
from manim import config

# Set rendering options
config.quality = "medium_quality"  # 720p30, less resource-intensive
config.frame_rate = 30
config.media_dir = r"{media_dir.replace(os.sep, '/')}"
config.output_file = r"{class_name}"

# Render the scene
if __name__ == "__main__":
    scene = {class_name}()
    scene.render()
"""
                manim_code = manim_code.rstrip() + "\n\n" + render_code

                # Save the Manim code to a file in the temp directory with UTF-8 encoding
                script_file = os.path.join(temp_dir, f"{safe_topic}.py")
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(manim_code)

                # Change to the temp directory for rendering
                original_cwd = os.getcwd()
                os.chdir(temp_dir)
                
                status_placeholder.info(f"Starting Manim rendering process (check console for progress)...")
                
                # Execute the Python script with properly configured environment
                command = f"{sys.executable} {script_file}"
                
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Modified read_output function that doesn't update Streamlit UI
                stdout_output, stderr_output = [], []
                def read_output(pipe, store):
                    for line in iter(pipe.readline, ''):
                        message = line.strip()
                        store.append(message)
                        print(f"Rendering: {message}")  # Only print to console, not to Streamlit

                stdout_thread = threading.Thread(target=read_output, args=(process.stdout, stdout_output))
                stderr_thread = threading.Thread(target=read_output, args=(process.stderr, stderr_output))
                stdout_thread.start()
                stderr_thread.start()

                # Wait for the process to complete
                process.wait()
                stdout_thread.join()
                stderr_thread.join()

                # Change back to original directory
                os.chdir(original_cwd)

                # Update status after threads are done
                if process.returncode != 0:
                    status_placeholder.error(f"Manim render failed with return code {process.returncode}")
                    for line in stderr_output[-5:]:  # Show last 5 error lines
                        st.error(line)
                    return None
                else:
                    status_placeholder.success("Manim rendering completed successfully!")

                # Find the generated video file with absolute paths
                video_path = None
                
                # Define potential paths with the absolute temp directory
                potential_paths = [
                    os.path.join(media_dir, "videos", "720p30", f"{class_name}.mp4"),
                    os.path.join(media_dir, "videos", "1080p60", f"{class_name}.mp4"),
                    os.path.join(media_dir, "videos", "480p15", f"{class_name}.mp4"),
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        video_path = path
                        break
                
                # If no direct match, search for partial movie files
                if not video_path:
                    for quality in ["720p30", "1080p60", "480p15"]:
                        partial_dir = os.path.join(media_dir, "videos", quality, "partial_movie_files", class_name)
                        if os.path.exists(partial_dir):
                            mp4_files = glob.glob(os.path.join(partial_dir, "*.mp4"))
                            if mp4_files:
                                video_path = max(mp4_files, key=os.path.getctime)
                                break
                
                # Last resort: Recursive search for any MP4 in the media directory
                if not video_path:
                    mp4_files = glob.glob(os.path.join(media_dir, "**", "*.mp4"), recursive=True)
                    if mp4_files:
                        video_path = max(mp4_files, key=os.path.getctime)
                
                if not video_path or not os.path.exists(video_path):
                    status_placeholder.error("Could not find rendered video file")
                    for line in stdout_output[-10:]:  # Show last 10 lines of output
                        st.error(f"Output: {line}")
                    return None
                
                # Copy to a more permanent location in the Streamlit app directory
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                final_path = os.path.join(output_dir, f"{safe_topic}.mp4")
                shutil.copy(video_path, final_path)
                
                status_placeholder.success(f"Video rendered successfully!")
                return final_path
                
            finally:
                # Clean up the temporary directory
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"Warning: Failed to clean up temp directory: {e}")
                    
    except Exception as e:
        st.error(f"Error rendering Manim animation: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Function to clean script for TTS
def clean_text_for_tts(text):
    # Remove common markdown symbols and other unwanted characters
    clean_text = re.sub(r'[\`#*~_>]', '', text)  # Removes backticks, #, *, ~, _, >
    clean_text = re.sub(r'\[.*?\]\(.*?\)', '', clean_text)  # Removes Markdown links
    clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.S)  # Removes code blocks
    clean_text = re.sub(r'`.*?`', '', clean_text)  # Removes inline code
    return clean_text.strip()

# Function to split script into sections for TTS
def split_script_into_sections(script):
    paragraphs = [p for p in script.split('\n\n') if p.strip()]
    return {f"part{i+1}": section for i, section in enumerate(paragraphs)}

# Function to generate TTS audio from script
def generate_audio(script, topic):
    try:
        with st.spinner("Generating voice narration..."):
            audio_dir = "audio"
            os.makedirs(audio_dir, exist_ok=True)

            # Split the script into sections
            sections = split_script_into_sections(script)

            audio_files = []
            progress_bar = st.progress(0)
            total_sections = len(sections)

            for i, (section_name, section_text) in enumerate(sections.items()):
                section_filename = f"{audio_dir}/{topic.replace(' ', '')}{section_name}.mp3"

                # Clean the text for TTS
                clean_text = clean_text_for_tts(section_text)

                # Generate the audio
                tts = gTTS(text=clean_text, lang='en', slow=False)
                tts.save(section_filename)
                audio_files.append(section_filename)

                # Update progress
                progress_bar.progress((i + 1) / total_sections)

            # Combine all audio files
            combined_audio = AudioSegment.empty()
            for audio_file in audio_files:
                sound = AudioSegment.from_mp3(audio_file)
                combined_audio += sound

            # Export the combined audio
            final_audio_path = f"{audio_dir}/{topic.replace(' ', '_')}_complete.mp3"
            combined_audio.export(final_audio_path, format="mp3")

            return final_audio_path

    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None
    
# Combine video and audio using MoviePy

def merge_video_audio(video_path, audio_path, topic):
    try:
        with st.spinner("Merging video and audio..."):
            if not video_path or not audio_path:
                raise ValueError("Video or audio path is missing")

            if not os.path.exists(video_path):
                raise ValueError(f"Video file not found: {video_path}")

            if not os.path.exists(audio_path):
                raise ValueError(f"Audio file not found: {audio_path}")

            safe_topic = topic.replace(' ', '_').replace("'", "").replace('"', '')
            output_path = f"{safe_topic}_final.mp4"

            # Load the video and audio
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)

            # Get durations
            audio_duration = audio_clip.duration
            video_duration = video_clip.duration

            # Adjust video speed to match audio duration
            if video_duration != audio_duration:
                speed_factor = video_duration / audio_duration
                adjusted_video = video_clip.fx(vfx.speedx, factor=speed_factor)
            else:
                adjusted_video = video_clip

            # Set the audio of the adjusted video
            final_clip = adjusted_video.set_audio(audio_clip)

            # Write the result to a file
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )

            # Close the clips to free resources
            video_clip.close()
            audio_clip.close()
            adjusted_video.close()
            final_clip.close()

            return output_path

    except Exception as e:
        st.error(f"Error merging video and audio: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Session state initialization
if 'script' not in st.session_state:
    st.session_state.script = None
if 'manim_code' not in st.session_state:
    st.session_state.manim_code = None
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None
if 'final_video_path' not in st.session_state:
    st.session_state.final_video_path = None
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # API Key input
    api_key = st.text_input("Gemini API Key", type="password",  help="Get your Gemini API key from Google AI Studio")
    
    if st.button("Validate API Key"):
        if api_key:
            if setup_gemini_api(api_key):
                st.session_state.api_key_valid = True
                st.success("API key is valid!")
            else:
                st.session_state.api_key_valid = False
                st.error("Invalid API key. Please check and try again.")
        else:
            st.warning("Please enter an API key.")
    
    # Topic input
    topic = st.text_input("Python Topic",  help="Enter a Python topic (e.g., 'Python Lists', 'Recursion', 'For Loops')")
    
    # Generation button
    generate_button = st.button("Generate Tutorial", disabled=not (st.session_state.api_key_valid and topic))

# Main content area
if generate_button and topic:
    # Reset session state for a new generation
    st.session_state.script = None
    st.session_state.manim_code = None
    st.session_state.video_path = None
    st.session_state.audio_path = None
    st.session_state.final_video_path = None
    
    # Step 1: Generate script
    st.header("Step 1: Generate Script")
    st.session_state.script = generate_script(topic)
    
    if st.session_state.script:
        st.success("Script generated successfully!")
        st.subheader("Generated Script")
        st.text_area("Script", st.session_state.script, height=300)
        
        # Step 2: Generate Manim code
        st.header("Step 2: Generate Animation Code")
        st.session_state.manim_code = generate_manim_code(topic, st.session_state.script)
        
        if st.session_state.manim_code:
            st.success("Animation code generated successfully!")
            st.subheader("Generated Manim Code")
            st.code(st.session_state.manim_code, language="python")
            
            # Step 3: Render animation
            st.header("Step 3: Render Animation")
            st.session_state.video_path = render_manim_animation(st.session_state.manim_code, topic)
            
            if st.session_state.video_path:
                st.success("Animation rendered successfully!")
                st.subheader("Generated Animation")
                st.video(st.session_state.video_path)
                
                # Step 4: Generate audio
                st.header("Step 4: Generate Voice Narration")
                st.session_state.audio_path = generate_audio(st.session_state.script, topic)
                
                if st.session_state.audio_path:
                    st.success("Voice narration generated successfully!")
                    st.subheader("Generated Audio")
                    st.audio(st.session_state.audio_path)
                    
                    # Step 5: Merge video and audio
                    st.header("Step 5: Create Final Tutorial")
                    st.session_state.final_video_path = merge_video_audio(
                        st.session_state.video_path, 
                        st.session_state.audio_path, 
                        topic
                    )
                    
                    if st.session_state.final_video_path:
                        st.success("🎉 Tutorial video created successfully!")
                        st.subheader("Final Tutorial Video")
                        st.video(st.session_state.final_video_path)
                        
                        # Download button
                        with open(st.session_state.final_video_path, "rb") as file:
                            st.download_button(
                                label="Download Tutorial Video",
                                data=file,
                                file_name=f"{topic.replace(' ', '_')}_tutorial.mp4",
                                mime="video/mp4"
                            )
                    else:
                        st.error("Failed to merge video and audio.")
                else:
                    st.error("Failed to generate audio narration.")
            else:
                st.error("Failed to render animation.")
        else:
            st.error("Failed to generate animation code.")
    else:
        st.error("Failed to generate script.")

# If nothing has been generated yet, show instructions
if not st.session_state.script:
    st.info("""
    ### How to use this app:
    1. Enter your Gemini API key in the sidebar
    2. Enter a Python topic you want to learn about
    3. Click 'Generate Tutorial' to create your custom tutorial video
    4. Wait for the process to complete (it may take a few minutes)
    5. Download your finished tutorial video
    
    This app will create a complete educational video with:
    - A detailed script explaining the Python topic
    - Animated visualizations created with Manim
    - Professional voice narration
    """)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit, Gemini AI, Manim, and gTTS")