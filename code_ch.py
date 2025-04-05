# code_challenges.py
import streamlit as st
import time
import json
import random
import datetime
from db_utils import get_db_connection, log_activity
import streamlit_ace as ace
import streamlit.components.v1 as components
import re
from db_utils import get_db_connection, init_challenges_tables, migrate_challenges_tables



# Add the confetti code at the top of your file
CONFETTI_HTML = """
<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
<script>
function launchConfetti() {
    confetti({
        particleCount: 150,
        spread: 70,
        origin: { y: 0.6 }
    });
}
</script>
"""

# Add custom CSS for kid-friendly UI
def add_kid_friendly_styling():
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #4CAF50 !important;
            color: white !important;
            border-radius: 10px !important;
            font-size: 18px !important;
            padding: 10px !important;
            border: none !important;
        }
        .stButton>button:hover {
            background-color: #45a049 !important;
        }
        .ace_editor {
            border: 3px solid #00ced1 !important;
            border-radius: 10px !important;
            background-color: #fffacd !important;
        }
        .stAlert {
            background-color: #ffdead !important;
            border-radius: 10px !important;
        }
        .story-container {
            background-color: #f0f8ff !important;
            padding: 20px !important;
            border-radius: 15px !important;
            border: 3px solid #1e90ff !important;
            margin-bottom: 20px !important;
        }
        .feedback-box {
            background-color: #98fb98 !important;
            padding: 15px !important;
            border-radius: 10px !important;
            border: 2px dashed #32cd32 !important;
            margin-top: 15px !important;
        }
        .badge-earned {
            background-color: #ffe4e1 !important;
            border: 3px solid #ff6347 !important;
            border-radius: 15px !important;
            padding: 20px !important;
            text-align: center !important;
            margin: 20px 0 !important;
            animation: pop-in 0.5s cubic-bezier(0.18, 0.89, 0.32, 1.28) !important;
        }
        .challenge-card {
            background-color: #e8f5e9 !important;
            border-left: 5px solid #4CAF50 !important;
            border-radius: 10px !important;
            padding: 15px !important;
            margin-bottom: 15px !important;
            position: relative !important;
        }
        .hidden {
            display: none !important;
        }
        @keyframes pop-in {
            0% { transform: scale(0); opacity: 0; }
            80% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }
        </style>
    """, unsafe_allow_html=True)

def run_challenge_test(code, test_cases, function_name):
    """Run code against test cases with better feedback."""
    try:
        # Execute the code in a safe environment
        local_vars = {}
        exec(code, {}, local_vars)
        
        if function_name not in local_vars:
            return False, f"❌ Oops! You need to define a function called '{function_name}'.", []
        
        # Test all the test cases
        test_results = []
        all_passed = True
        
        for i, test in enumerate(test_cases):
            input_val = test["input"]
            expected = test["expected"]
            
            try:
                result = local_vars[function_name](*input_val) if isinstance(input_val, tuple) else local_vars[function_name](input_val)
                if result == expected:
                    test_results.append({
                        "test_num": i+1,
                        "success": True,
                        "message": f"Test {i+1} passed! Input: {input_val}, Output: {result}"
                    })
                else:
                    all_passed = False
                    test_results.append({
                        "test_num": i+1,
                        "success": False,
                        "message": f"Test {i+1} failed! Input: {input_val}, Expected: {expected}, Got: {result}"
                    })
            except Exception as e:
                all_passed = False
                test_results.append({
                    "test_num": i+1,
                    "success": False,
                    "message": f"Error in test {i+1}: {str(e)}"
                })
        
        if all_passed:
            feedback = "🎉 Amazing job! All tests passed. You're a coding star! ⭐"
        else:
            feedback = "Almost there! Keep trying - you can do it! 💪"
            
        return all_passed, feedback, test_results
            
    except Exception as e:
        return False, f"❌ Uh-oh! Something went wrong: {str(e)}", []

def get_sample_challenges():
    """Return a list of sample code challenges"""
    return [
        {
            "title": "The Lost Space Ship",
            "story": """
                🚀 **Space Adventure: The Lost Control Panel** 🚀
                
                You're an astronaut aboard the *Stellar Explorer*, humanity's most advanced spacecraft. 
                Suddenly, the main control panel malfunctions! The ship is veering off course and heading 
                toward an asteroid field.
                
                The emergency system requires you to fix a Python function that calculates the correct 
                navigation coordinates. Without this function, the ship's autopilot can't redirect to safety!
                
                The navigation officer has left notes about the function, but needs your programming skills to implement it.
                Can you save the ship and crew by writing the correct code?
            """,
            "description": "Create a function called `calculate_coordinates` that takes two parameters: `current_position` (a list with x, y coordinates) and `asteroid_field` (a list with x, y coordinates). Return the safe coordinates as a list [new_x, new_y] that is in the opposite direction from the asteroid field.",
            "difficulty": "Easy",
            "category": "Functions",
            "initial_code": """def calculate_coordinates(current_position, asteroid_field):
    # Your code goes here
    # current_position is a list [x, y]
    # asteroid_field is a list [x, y]
    # Return a list [new_x, new_y] with the safe coordinates
    
    # Hint: To move away from the asteroid field, move in the opposite direction
    
    return [0, 0]  # Replace with your solution""",
            "solution_code": """def calculate_coordinates(current_position, asteroid_field):
    # Calculate the direction vector from current position to asteroid field
    direction_x = asteroid_field[0] - current_position[0]
    direction_y = asteroid_field[1] - current_position[1]
    
    # Move in the opposite direction (negative direction vector)
    new_x = current_position[0] - direction_x
    new_y = current_position[1] - direction_y
    
    return [new_x, new_y]""",
            "test_cases": [
                {"input": ([0, 0], [5, 5]), "expected": [-5, -5]},
                {"input": ([2, 2], [-3, 4]), "expected": [7, 0]}
            ],
            "hints": [
                "Calculate the direction by subtracting current from asteroid coordinates",
                "To go in the opposite direction, move by the negative of that direction",
                "Make sure to handle both the x and y coordinates separately"
            ],
            "xp_reward": 50,
            "badge_id": "space_explorer"
        },
        {
            "title": "Treasure Map Decoder",
            "story": """
                🏝️ **Pirate Adventure: The Hidden Treasure** 🏝️
                
                Ahoy, matey! You've joined the crew of the infamous pirate ship *Black Pearl* in search of
                the legendary treasure of Captain Codebeard. After months at sea, you've found a mysterious map
                on a deserted island.
                
                The map is encoded in a strange way - it uses a list of numbers that need to be decoded to reveal 
                the exact location of the treasure. Captain Codebeard was known for his love of Python programming,
                and left this puzzle to ensure only the worthy could find his gold!
                
                Can you write the function to decode the map and lead your crew to unimaginable riches?
            """,
            "description": "Create a function called `decode_map` that takes a list of numbers. The treasure location is found by: (1) Finding the sum of all numbers, (2) Finding the product of the first and last number, (3) Returning a list with [sum, product].",
            "difficulty": "Easy",
            "category": "Lists",
            "initial_code": """def decode_map(encoded_map):
    # Your code goes here
    # encoded_map is a list of numbers, e.g. [3, 1, 4, 1, 5, 9]
    # Return a list [sum_of_all, product_of_first_and_last]
    
    # Hint: You can use sum() function to add all numbers in a list
    
    return [0, 0]  # Replace with your solution""",
            "solution_code": """def decode_map(encoded_map):
    # Find the sum of all numbers
    total_sum = sum(encoded_map)
    
    # Find the product of the first and last number
    product = encoded_map[0] * encoded_map[-1]
    
    return [total_sum, product]""",
            "test_cases": [
                {"input": [3, 1, 4, 1, 5, 9], "expected": [23, 27]},
                {"input": [-2, 5, 10, -8], "expected": [5, 16]}
            ],
            "hints": [
                "Use the sum() function to add all numbers in the list",
                "To get the first element of a list, use list[0]",
                "To get the last element of a list, use list[-1]"
            ],
            "xp_reward": 50,
            "badge_id": "treasure_hunter"
        }
    ]

def get_available_challenges(user_id):
    """Get a list of available challenges for the user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all challenges with completion status for this user
    cursor.execute("""
        SELECT c.id, c.title, c.difficulty, c.category, c.xp_reward, c.badge_id,
               uc.completed, uc.attempts
        FROM code_challenges c
        LEFT JOIN user_challenges uc ON c.id = uc.challenge_id AND uc.user_id = ?
        ORDER BY c.difficulty, c.id
    """, (user_id,))
    
    challenges = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    result = []
    for challenge in challenges:
        result.append({
            "id": challenge[0],
            "title": challenge[1],
            "difficulty": challenge[2],
            "category": challenge[3],
            "xp_reward": challenge[4],
            "badge_id": challenge[5],
            "completed": challenge[6] == 1 if challenge[6] is not None else False,
            "attempts": challenge[7] or 0
        })
    
    return result

def get_challenge_details(challenge_id):
    """Get detailed information about a specific challenge"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, story, description, difficulty, category, 
               initial_code, solution_code, test_cases, hints, xp_reward, badge_id
        FROM code_challenges
        WHERE id = ?
    """, (challenge_id,))
    
    challenge = cursor.fetchone()
    conn.close()
    
    if not challenge:
        return None
    
    return {
        "id": challenge[0],
        "title": challenge[1],
        "story": challenge[2],
        "description": challenge[3],
        "difficulty": challenge[4],
        "category": challenge[5],
        "initial_code": challenge[6],
        "solution_code": challenge[7],
        "test_cases": json.loads(challenge[8]) if challenge[8] else [],
        "hints": json.loads(challenge[9]) if challenge[9] else [],
        "xp_reward": challenge[10],
        "badge_id": challenge[11]
    }

def get_user_challenge_progress(user_id, challenge_id):
    """Get the user's progress on a specific challenge"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT completed, attempts, last_code, completed_at
        FROM user_challenges
        WHERE user_id = ? AND challenge_id = ?
    """, (user_id, challenge_id))
    
    progress = cursor.fetchone()
    conn.close()
    
    if not progress:
        return {
            "completed": False,
            "attempts": 0,
            "last_code": None,
            "completed_at": None
        }
    
    return {
        "completed": progress[0] == 1,
        "attempts": progress[1],
        "last_code": progress[2],
        "completed_at": progress[3]
    }

def submit_challenge(user_id, challenge_id, code):
    """Submit and evaluate a code challenge with improved testing"""
    # Get challenge details
    challenge = get_challenge_details(challenge_id)
    if not challenge:
        return {"success": False, "message": "Challenge not found"}
    
    # Get user's progress
    progress = get_user_challenge_progress(user_id, challenge_id)
    
    # Update attempts count
    attempts = progress["attempts"] + 1
    
    # Initialize test results
    results = {
        "success": False,
        "message": "",
        "details": [],
        "attempts": attempts,
        "completed": False
    }
    
    # Extract the function name from the challenge description
    function_name = None
    # Look for function definitions in the description
    func_match = re.search(r'function\s+called\s+`([a-zA-Z0-9_]+)`', challenge["description"])
    if func_match:
        function_name = func_match.group(1)
    else:
        # Look for function definitions in the initial code
        func_match = re.search(r'def\s+([a-zA-Z0-9_]+)\(', challenge["initial_code"])
        if func_match:
            function_name = func_match.group(1)
    
    if not function_name:
        return {"success": False, "message": "Could not determine function name from challenge"}
    
    # Get test cases from challenge
    test_cases = challenge["test_cases"]
    
    # Run the enhanced test function
    try:
        success, feedback, test_details = run_challenge_test(code, test_cases, function_name)
        
        # Set results
        results["success"] = success
        results["message"] = feedback
        results["completed"] = success
        results["details"] = test_details
            
    except Exception as e:
        # Error in running tests
        results["success"] = False
        results["message"] = f"Error in testing: {str(e)}"
    
    # Save progress to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if record exists
    cursor.execute("""
        SELECT id FROM user_challenges
        WHERE user_id = ? AND challenge_id = ?
    """, (user_id, challenge_id))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update existing record
        cursor.execute("""
            UPDATE user_challenges
            SET attempts = ?, 
                last_code = ?,
                completed = ?,
                completed_at = ?
            WHERE user_id = ? AND challenge_id = ?
        """, (
            attempts,
            code,
            1 if results["completed"] else progress["completed"],
            datetime.datetime.now().isoformat() if results["completed"] and not progress["completed"] else progress["completed_at"],
            user_id,
            challenge_id
        ))
    else:
        # Insert new record
        cursor.execute("""
            INSERT INTO user_challenges
            (user_id, challenge_id, completed, attempts, last_code, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            challenge_id,
            1 if results["completed"] else 0,
            attempts,
            code,
            datetime.datetime.now().isoformat() if results["completed"] else None
        ))
    
    # If challenge is completed for the first time, award XP and badge
    if results["completed"] and not progress["completed"]:
        try:
            log_activity(
                user_id, 
                "challenge_completed", 
                json.dumps({
                    "challenge_id": challenge_id, 
                    "challenge_title": challenge["title"],
                    "xp_reward": challenge["xp_reward"]
                })
            )
            
            # Record badge earned
            if challenge["badge_id"]:
                log_activity(
                    user_id, 
                    "badge_earned", 
                    json.dumps({
                        "badge_id": challenge["badge_id"],
                        "challenge_id": challenge_id
                    })
                )
                
                # Add badge info to results
                results["badge"] = {
                    "id": challenge["badge_id"],
                    "title": get_badge_title(challenge["badge_id"]),
                    "description": f"Completed the '{challenge['title']}' challenge"
                }
        except Exception as e:
            print(f"Error processing challenge reward: {e}")
    
    conn.commit()
    conn.close()
    
    return results

def get_badge_title(badge_id):
    """Get a friendly title for a badge ID"""
    badge_titles = {
        "space_explorer": "Space Explorer",
        "treasure_hunter": "Treasure Hunter",
        "potion_master": "Potion Master",
        "robot_friend": "Robot Friend",
        "weather_wizard": "Weather Wizard"
    }
    return badge_titles.get(badge_id, badge_id.replace("_", " ").title())

def get_badge_image(badge_id):
    """Get an emoji representation for a badge"""
    badge_images = {
        "space_explorer": "🚀",
        "treasure_hunter": "💎",
        "potion_master": "🧪",
        "robot_friend": "🤖",
        "weather_wizard": "🌦️"
    }
    return badge_images.get(badge_id, "🏆")

def get_hint(challenge_id, hint_index):
    """Get a specific hint for a challenge"""
    challenge = get_challenge_details(challenge_id)
    if not challenge or not challenge["hints"] or hint_index >= len(challenge["hints"]):
        return "No hint available at this level."
    
    return challenge["hints"][hint_index]

def render_challenge_card(challenge):
    """Render a challenge card with HTML/CSS"""
    # Determine color scheme based on difficulty
    if challenge["difficulty"] == "Easy":
        bg_color = "#e8f5e9"
        border_color = "#4CAF50"
        difficulty_color = "#2E7D32"
    elif challenge["difficulty"] == "Medium":
        bg_color = "#e3f2fd"
        border_color = "#2196F3"
        difficulty_color = "#1565C0"
    else:
        bg_color = "#fce4ec"
        border_color = "#F44336"
        difficulty_color = "#C62828"
    
    # Badge and completion status
    badge = get_badge_image(challenge["badge_id"]) if challenge["badge_id"] else "🏆"
    status = "✅ Completed" if challenge["completed"] else f"🔄 Attempts: {challenge['attempts']}"
    
    # Render the card
    return f"""
    <div class="challenge-card" style="background-color: {bg_color}; border-left: 5px solid {border_color};">
        <div style="position: absolute; top: 10px; right: 15px; font-size: 1.5em;">{badge}</div>
        
        <h3 style="margin-top: 0; color: #333;">{challenge["title"]}</h3>
        
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
            <div style="background-color: {difficulty_color}; color: white; padding: 3px 8px; border-radius: 15px; font-size: 0.8em;">
                {challenge["difficulty"]}
            </div>
            <div style="background-color: rgba(0,0,0,0.05); padding: 3px 8px; border-radius: 15px; font-size: 0.8em;">
                {challenge["category"]}
            </div>
            <div style="background-color: #FF9800; color: white; padding: 3px 8px; border-radius: 15px; font-size: 0.8em;">
                +{challenge["xp_reward"]} XP
            </div>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
            <div>{status}</div>
            <button onclick="
            window.parent.document.dispatchEvent(
                new CustomEvent('challengeSelected_{challenge['id']}')
            );
            return false;
        ">
        {("Continue" if challenge["attempts"] > 0 else "Start") if not challenge["completed"] else "View"}
        </button>
        </div>
    </div>
    """

def display_challenges_list(challenges):
    """Display the list of available challenges"""
    st.header("Choose Your Coding Adventure")
    
    st.markdown("""
    Welcome to Python Coding Adventures! 🐍✨
    
    Embark on exciting coding missions that will test your Python skills while you help characters solve problems 
    in different fantasy worlds. Each challenge comes with a story, a coding mission, and awesome rewards!
    """)
    
    # Progress stats
    completed = sum(1 for c in challenges if c["completed"])
    total = len(challenges)
    
    if total > 0:
        # Show completion progress
        completion_percent = (completed / total) * 100
        st.markdown(f"""
        <div style="margin: 20px 0;">
            <p>Your progress: <b>{completed}/{total} challenges completed</b></p>
            <div style="background-color: #e0e0e0; border-radius: 10px; height: 10px; margin-top: 5px;">
                <div style="width: {completion_percent}%; background-color: #4CAF50; height: 100%; border-radius: 10px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Organize challenges by difficulty
    easy_challenges = [c for c in challenges if c["difficulty"] == "Easy"]
    medium_challenges = [c for c in challenges if c["difficulty"] == "Medium"]
    hard_challenges = [c for c in challenges if c["difficulty"] == "Hard"]
    
    # Display challenges by difficulty level
    if easy_challenges:
        st.subheader("🌱 Beginner Adventures")
        for challenge in easy_challenges:
            display_challenge_card(challenge)
    
    if medium_challenges:
        st.subheader("🌿 Intermediate Quests")
        for challenge in medium_challenges:
            display_challenge_card(challenge)
    
    if hard_challenges:
        st.subheader("🌲 Expert Missions")
        for challenge in hard_challenges:
            display_challenge_card(challenge)
    
    # If no challenges available
    if not challenges:
        st.info("No coding challenges available yet. Check back soon!")

# Here's the fix for the display_challenge_card function in code_ch.py
# Replace the function with this version:

def display_challenge_card(challenge):
    """Display a challenge card that can be clicked"""
    # Determine color scheme based on difficulty
    if challenge["difficulty"] == "Easy":
        bg_color = "#e8f5e9"
        border_color = "#4CAF50"
        difficulty_color = "#2E7D32"
    elif challenge["difficulty"] == "Medium":
        bg_color = "#e3f2fd"
        border_color = "#2196F3"
        difficulty_color = "#1565C0"
    else:
        bg_color = "#fce4ec"
        border_color = "#F44336"
        difficulty_color = "#C62828"
    
    # Badge and completion status
    badge = get_badge_image(challenge["badge_id"]) if challenge["badge_id"] else "🏆"
    status = "✅ Completed" if challenge["completed"] else f"🔄 Attempts: {challenge['attempts']}"
    
    # Use a clickable card without columns
    st.markdown(f"""
    <div style="display: flex; background-color: {bg_color}; border-left: 5px solid {border_color}; 
                border-radius: 10px; padding: 15px; margin-bottom: 15px; cursor: pointer;"
         onclick="document.getElementById('btn_challenge_{challenge['id']}').click()">
        <div style="flex: 1;">
            <h3 style="margin-top: 0; color: #333;">{challenge["title"]}</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
                <div style="background-color: {difficulty_color}; color: white; padding: 3px 8px; border-radius: 15px; font-size: 0.8em;">
                    {challenge["difficulty"]}
                </div>
                <div style="background-color: rgba(0,0,0,0.05); padding: 3px 8px; border-radius: 15px; font-size: 0.8em;">
                    {challenge["category"]}
                </div>
                <div style="background-color: #FF9800; color: white; padding: 3px 8px; border-radius: 15px; font-size: 0.8em;">
                    +{challenge["xp_reward"]} XP
                </div>
            </div>
            <div>{status}</div>
        </div>
        <div style="font-size: 2em; margin-left: 15px; display: flex; align-items: center;">
            {badge}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Hidden button for actual navigation - remove 'visible' parameter
    # We'll hide it with CSS instead
    st.markdown(
        f"""
        <style>
        #btn_challenge_{challenge['id']} {{
            display: none;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    if st.button("Select", key=f"btn_challenge_{challenge['id']}", help=f"Go to challenge {challenge['id']}"):
        st.session_state.current_challenge = challenge['id']
        st.session_state.view_challenges = False
        st.session_state.need_rerun = True
def display_challenge(challenge_id, user_id):
    """Display a specific coding challenge with enhanced editor and tests"""
    # Add kid-friendly styling
    add_kid_friendly_styling()
    
    # Include confetti script
    components.html(CONFETTI_HTML, height=0)
    
    # Get challenge details
    challenge = get_challenge_details(challenge_id)
    
    if not challenge:
        st.error("Challenge not found!")
        if st.button("Back to Challenges"):
            st.session_state.view_challenges = True
            st.rerun()
        return
    
    # Get user's progress on this challenge
    progress = get_user_challenge_progress(user_id, challenge_id)
    
    # Challenge header with title and difficulty
    st.header(challenge["title"])
    
    # Difficulty and category badges
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # Difficulty badge
        difficulty_color = "#4CAF50" if challenge["difficulty"] == "Easy" else "#2196F3" if challenge["difficulty"] == "Medium" else "#F44336"
        st.markdown(f"""
        <div style="background-color: {difficulty_color}; color: white; padding: 5px 10px; 
                    border-radius: 15px; text-align: center; font-size: 0.9em;">
            {challenge["difficulty"]}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Category badge
        st.markdown(f"""
        <div style="background-color: #9C27B0; color: white; padding: 5px 10px; 
                    border-radius: 15px; text-align: center; font-size: 0.9em;">
            {challenge["category"]}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # XP reward
        st.markdown(f"""
        <div style="text-align: right; color: #FF9800; font-weight: bold; font-size: 1.1em;">
            Reward: +{challenge["xp_reward"]} XP
        </div>
        """, unsafe_allow_html=True)
    
    # Story section with improved styling
    st.markdown(f"""
    <div class="story-container">
        {challenge["story"]}
    </div>
    """, unsafe_allow_html=True)
    
    # Challenge description
    st.markdown("### Your Mission 📋")
    st.markdown(challenge["description"])
    
    # Initialize session state for this challenge
    if f"hints_used_{challenge_id}" not in st.session_state:
        st.session_state[f"hints_used_{challenge_id}"] = 0
    
    if f"results_{challenge_id}" not in st.session_state:
        st.session_state[f"results_{challenge_id}"] = None
    
    # Determine initial code to show
    initial_code = progress["last_code"] if progress["last_code"] else challenge["initial_code"]
    
    # Code editor with improved styling using streamlit-ace
    st.markdown("### Your Code 💻")
    
    # Use the advanced Ace editor
    user_code = ace.st_ace(
        value=initial_code,
        language="python",
        theme="monokai",
        font_size=14,
        key=f"ace_editor_{challenge_id}",
        height=300,
        show_gutter=True,
        wrap=True,
        auto_update=True,
        tab_size=4,
    )
    
    # Submit and hint buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        submit_button = st.button("🚀 Test Code", key=f"submit_{challenge_id}", type="primary", use_container_width=True)
    
    with col2:
        # Only show hint button if the challenge isn't completed yet
        hint_disabled = progress["completed"] or st.session_state[f"hints_used_{challenge_id}"] >= len(challenge["hints"])
        hint_button = st.button("💡 Get Hint", key=f"hint_{challenge_id}", 
                               disabled=hint_disabled,
                               use_container_width=True)
    
    # Process hint request
    if hint_button and not progress["completed"]:
        hint_index = st.session_state[f"hints_used_{challenge_id}"]
        hint_text = get_hint(challenge_id, hint_index)
        
        # Increment hints used
        st.session_state[f"hints_used_{challenge_id}"] += 1
        
        # Display hint with improved styling
        st.markdown(f"""
        <div class="hint-container">
            <h4>Hint {hint_index + 1}</h4>
            <p>{hint_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Process code submission
    if submit_button:
        with st.spinner("Running your code..."):
            # Submit challenge and get results
            results = submit_challenge(user_id, challenge_id, user_code)
            
            # Store results in session state
            st.session_state[f"results_{challenge_id}"] = results
            
            # If challenge was just completed, trigger confetti animation
            if results["completed"] and not progress["completed"]:
                components.html("""
                <script>
                    setTimeout(function() { launchConfetti(); }, 500);
                </script>
                """, height=0)
                
                # If there's a badge, show it with animation
                if results.get("badge"):
                    badge_id = results["badge"]["id"]
                    badge_title = results["badge"]["title"]
                    badge_desc = results["badge"]["description"]
                    badge_emoji = get_badge_image(badge_id)
                    
                    st.markdown(f"""
                    <div class="badge-earned">
                        <div style="font-size: 5em; margin-bottom: 10px;">{badge_emoji}</div>
                        <h2 style="margin: 10px 0; color: #9C27B0;">Badge Earned!</h2>
                        <h3 style="margin: 5px 0;">{badge_title}</h3>
                        <p>{badge_desc}</p>
                        <p style="margin: 15px 0 5px 0; font-weight: bold; color: #FF9800;">+{challenge["xp_reward"]} XP</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Show saved results if available
    if st.session_state[f"results_{challenge_id}"]:
        results = st.session_state[f"results_{challenge_id}"]
        
        success_color = "#4CAF50" if results["success"] else "#F44336"
        
        # Results container with improved styling
        st.markdown(f"""
        <div class="feedback-box" style="border-color: {success_color};">
            <h3 style="margin-top: 0; color: {success_color};">
                {("🎉 Success!" if results["success"] else "❌ Not Quite Right")}
            </h3>
            <p>{results["message"]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Test details if available
        if results["details"]:
            st.markdown("<h4>Test Results:</h4>", unsafe_allow_html=True)
            
            for detail in results["details"]:
                status = "✅" if detail["success"] else "❌"
                st.markdown(f"""
                <div style="margin-bottom: 10px; font-family: monospace; background-color: rgba(0,0,0,0.05); padding: 10px; border-radius: 5px;">
                    <div>{status} <span style="color: {'#4CAF50' if detail['success'] else '#F44336'};">Line {detail['line']}</span>:</div>
                    <div style="margin-left: 20px; margin-top: 5px;">{detail['code']}</div>
                    <div style="margin-left: 20px; color: {'#4CAF50' if detail['success'] else '#F44336'};">{detail['message']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # View solution button (only if challenge is completed or user has attempted many times)
    attempts_threshold = 5  # Show solution after 5 attempts
    if progress["completed"] or progress["attempts"] >= attempts_threshold:
        if st.button("👀 View Solution", key=f"solution_{challenge_id}"):
            st.code(challenge["solution_code"], language="python")
            st.markdown("""
            <div class="feedback-box">
                <h4 style="margin-top: 0; color: #2E7D32;">Solution Explanation</h4>
                <p>This solution works by:</p>
                <ol>
                    <li>Breaking down the problem into smaller steps</li>
                    <li>Using appropriate data structures and algorithms</li>
                    <li>Testing edge cases to ensure robustness</li>
                </ol>
                <p>Try to understand the approach rather than memorizing the code!</p>
            </div>
            """, unsafe_allow_html=True)


def coding_challenge_page():
    """Main coding challenges page with all fixes implemented"""
    st.title("🎮 Python Coding Adventures")
    
    # Initialize database with proper schema
    from db_utils import init_challenges_tables, migrate_challenges_tables
    init_challenges_tables()
    migrate_challenges_tables()
    
    # Check if user is logged in
    if 'user' not in st.session_state or not st.session_state.user:
        st.warning("Please log in to access coding challenges.")
        return
    
    user_id = st.session_state.user['id']
    
    # Initialize session state for navigation
    if "current_challenge" not in st.session_state:
        st.session_state.current_challenge = None
        st.session_state.view_challenges = True
        st.session_state.need_rerun = False
    
    # Handle any pending rerun
    if st.session_state.get('need_rerun'):
        st.session_state.need_rerun = False
        st.rerun()
    
    # Fetch available challenges
    challenges = get_available_challenges(user_id)
    
    # Main content container
    with st.container():
        # Back button when viewing a challenge
        if not st.session_state.view_challenges:
            if st.button("← Back to Challenges", key="back_btn"):
                st.session_state.view_challenges = True
                st.session_state.need_rerun = True
                st.rerun()
        
        # Display either challenges list or specific challenge
        if st.session_state.view_challenges:
            display_challenges_list(challenges)
        elif st.session_state.current_challenge:
            display_challenge(st.session_state.current_challenge, user_id)


def render_challenge_card(challenge):
    """Updated to use event-based navigation"""
    # Determine color scheme based on difficulty
    if challenge["difficulty"] == "Easy":
        bg_color = "#e8f5e9"
        border_color = "#4CAF50"
        difficulty_color = "#2E7D32"
    elif challenge["difficulty"] == "Medium":
        bg_color = "#e3f2fd"
        border_color = "#2196F3"
        difficulty_color = "#1565C0"
    else:
        bg_color = "#fce4ec"
        border_color = "#F44336"
        difficulty_color = "#C62828"
    
    # Badge and completion status
    badge = get_badge_image(challenge["badge_id"]) if challenge["badge_id"] else "🏆"
    status = "✅ Completed" if challenge["completed"] else f"🔄 Attempts: {challenge['attempts']}"
    
    return f"""
    <div class="challenge-card" style="background-color: {bg_color}; border-left: 5px solid {border_color}; cursor: pointer;"
         onclick="window.parent.document.dispatchEvent(new CustomEvent('challengeSelected_{challenge['id']}'))">
        <div style="position: absolute; top: 10px; right: 15px; font-size: 1.5em;">{badge}</div>
        
        <h3 style="margin-top: 0; color: #333;">{challenge["title"]}</h3>
        
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
            <div style="background-color: {difficulty_color}; color: white; padding: 3px 8px; border-radius: 15px; font-size: 0.8em;">
                {challenge["difficulty"]}
            </div>
            <div style="background-color: rgba(0,0,0,0.05); padding: 3px 8px; border-radius: 15px; font-size: 0.8em;">
                {challenge["category"]}
            </div>
            <div style="background-color: #FF9800; color: white; padding: 3px 8px; border-radius: 15px; font-size: 0.8em;">
                +{challenge["xp_reward"]} XP
            </div>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
            <div>{status}</div>
            <div style="background-color: {border_color}; color: white; border: none; padding: 5px 10px; 
                       border-radius: 5px; cursor: pointer;">
                {("Continue" if challenge["attempts"] > 0 else "Start") if not challenge["completed"] else "View"}
            </div>
        </div>
    </div>
    """

def set_current_challenge(challenge_id):
    """Updated to avoid immediate rerun"""
    st.session_state.current_challenge = challenge_id
    st.session_state.view_challenges = False
    st.session_state.need_rerun = True


def complete_daily_challenge(user_id, challenge_data):
    """Mark a daily challenge as completed and award XP"""
    try:
        # Get XP reward from the challenge
        xp_reward = challenge_data["xp_reward"]
        
        # Log the activity
        log_activity(
            user_id, 
            "daily_challenge_completed", 
            json.dumps({
                "challenge": challenge_data["challenge"],
                "topic": challenge_data["topic"],
                "xp_reward": xp_reward
            })
        )
        
        # Return success with the XP amount
        return {
            "success": True,
            "xp_awarded": xp_reward,
            "message": f"Challenge completed! You earned {xp_reward} XP!"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error completing challenge: {str(e)}"
        }

__all__ = ['coding_challenge_page', 'init_challenges_db', 'complete_daily_challenge']