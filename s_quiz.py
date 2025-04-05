import streamlit as st
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from config import API_KEY

# Configure Gemini API
genai.configure(api_key=API_KEY)

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'completed' not in st.session_state:
    st.session_state.completed = False
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'topic' not in st.session_state:
    st.session_state.topic = ""
if 'question_categories' not in st.session_state:
    st.session_state.question_categories = {}
if 'time_taken' not in st.session_state:
    st.session_state.time_taken = {}

def generate_mcqs(topic):
    prompt = (
        f"Generate 7 multiple-choice questions on the topic: {topic}. "
        "Each question should belong to one of these categories: Basic Concepts, Application, Advanced Concepts, Problem Solving. "
        "Format each question as: 'Q: <question>? Category: <category> | Options: A) <option1> | B) <option2> | C) <option3> | D) <option4>. Answer: <correct_option>'."
    )

    model = genai.GenerativeModel("gemini-1.5-flash")

    try:
        response = model.generate_content(prompt)
        output_text = response.text
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []

    questions = []

    # Improved parsing using structured splitting
    for item in output_text.strip().split("\n"):
        if "Q:" in item and "Options:" in item and "Answer:" in item:
            try:
                # First split the question part
                if "Category:" in item:
                    question_part, rest = item.split("Category:")
                    category_part, options_part = rest.split("Options:")
                    category = category_part.strip()
                else:
                    question_part, options_part = item.split("Options:")
                    category = "General"  # Default category if none provided
                
                # Then split options and answer
                options_part, answer_part = options_part.split("Answer:")

                question = question_part.replace("Q:", "").strip()
                options_text = options_part.strip()
                
                # Handle options that might be separated by different delimiters
                if " | " in options_text:
                    option_list = options_text.split(" | ")
                else:
                    option_list = options_text.split(" ")
                
                # Extract just the text of each option, removing the A), B), etc.
                options = []
                for opt in option_list:
                    if len(opt) > 2 and opt[0] in "ABCD" and opt[1] == ")":
                        options.append(opt[2:].strip())
                    else:
                        options.append(opt.strip())

                correct_answer = answer_part.strip()

                if len(options) == 4 and correct_answer in "ABCD":
                    correct_option = options["ABCD".index(correct_answer)]
                    questions.append({
                        "question": question, 
                        "options": options, 
                        "correct_answer": correct_option,
                        "category": category
                    })

            except Exception as parse_error:
                st.warning(f"Skipping malformed question: {item}")
                print(f"Parse error: {parse_error}")

    return questions

def start_assessment():
    st.session_state.questions = generate_mcqs(st.session_state.topic)
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.completed = False
    st.session_state.answers = {}
    st.session_state.question_categories = {}
    st.session_state.time_taken = {}
    
    # Extract categories from questions
    for i, q in enumerate(st.session_state.questions):
        st.session_state.question_categories[i] = q.get("category", "General")

def submit_answer(question_idx):
    if question_idx in st.session_state.answers and st.session_state.answers[question_idx]:
        user_answer = st.session_state.answers[question_idx]
        correct_answer = st.session_state.questions[question_idx]["correct_answer"]
        
        if user_answer == correct_answer:
            st.session_state.score += 1
        
        if st.session_state.current_question < len(st.session_state.questions) - 1:
            st.session_state.current_question += 1
        else:
            st.session_state.completed = True
    else:
        st.error("Please select an answer before submitting.")

def restart():
    st.session_state.questions = []
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.completed = False
    st.session_state.answers = {}
    st.session_state.topic = ""
    st.session_state.question_categories = {}
    st.session_state.time_taken = {}

def analyze_performance():
    """Analyze performance by category and generate feedback"""
    categories = {}
    for q_idx, category in st.session_state.question_categories.items():
        if category not in categories:
            categories[category] = {"total": 0, "correct": 0}
        
        categories[category]["total"] += 1
        
        if q_idx in st.session_state.answers:
            user_answer = st.session_state.answers[q_idx]
            correct_answer = st.session_state.questions[q_idx]["correct_answer"]
            if user_answer == correct_answer:
                categories[category]["correct"] += 1
    
    # Calculate performance by category
    performance = {}
    strengths = []
    weaknesses = []
    
    for category, stats in categories.items():
        if stats["total"] > 0:
            score_pct = (stats["correct"] / stats["total"]) * 100
            performance[category] = {
                "score_pct": score_pct,
                "correct": stats["correct"],
                "total": stats["total"]
            }
            
            if score_pct >= 75:
                strengths.append(category)
            elif score_pct < 50:
                weaknesses.append(category)
    
    return performance, strengths, weaknesses

def display_performance_charts(performance):
    """Generate and display performance charts"""
    if not performance:
        return
    
    # Prepare data for charts
    categories = list(performance.keys())
    scores = [p["score_pct"] for p in performance.values()]
    correct_counts = [p["correct"] for p in performance.values()]
    total_counts = [p["total"] for p in performance.values()]
    
    # Create a 2x1 layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Category performance bar chart
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        bars = ax1.bar(categories, scores, color='skyblue')
        ax1.set_ylim(0, 100)
        ax1.set_ylabel('Score (%)')
        ax1.set_title('Performance by Category')
        ax1.set_xticklabels(categories, rotation=30, ha='right')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f"{height:.0f}%", ha='center', va='bottom')
        
        st.pyplot(fig1)
    
    with col2:
        # Pie chart of overall performance
        total_correct = sum(correct_counts)
        total_questions = sum(total_counts)
        total_incorrect = total_questions - total_correct
        
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        labels = ['Correct', 'Incorrect']
        sizes = [total_correct, total_incorrect]
        colors = ['#4CAF50', '#F44336']
        explode = (0.1, 0)  # explode the 1st slice (Correct)
        
        ax2.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=140)
        ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        ax2.set_title('Overall Performance')
        
        st.pyplot(fig2)
    
    # Radar chart for category proficiency
    categories_radar = list(performance.keys())
    if len(categories_radar) >= 3:  # Only create radar chart if we have at least 3 categories
        # Number of variables
        N = len(categories_radar)
        
        # What will be the angle of each axis in the plot
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Normalize scores to range 0-1 for the radar chart
        normalized_scores = [s/100 for s in scores]
        normalized_scores += normalized_scores[:1]  # Close the loop
        
        # Create the radar chart
        fig3 = plt.figure(figsize=(8, 6))
        ax3 = fig3.add_subplot(111, polar=True)
        
        # Draw one axis per variable and add labels
        plt.xticks(angles[:-1], categories_radar, color='grey', size=10)
        
        # Draw the chart
        ax3.plot(angles, normalized_scores, linewidth=2, linestyle='solid')
        ax3.fill(angles, normalized_scores, alpha=0.25)
        
        # Add radial axes and labels
        ax3.set_rlabel_position(0)
        plt.yticks([0.25, 0.5, 0.75], ["25%", "50%", "75%"], color="grey", size=8)
        plt.ylim(0, 1)
        
        st.pyplot(fig3)

def get_feedback_and_resources(strengths, weaknesses, topic):
    """Generate personalized feedback and learning resources"""
    feedback = ""
    
    if strengths:
        feedback += f"### 💪 Your Strengths\n"
        feedback += f"You demonstrated strong understanding in: {', '.join(strengths)}.\n\n"
    
    if weaknesses:
        feedback += f"### 🚀 Areas for Improvement\n"
        feedback += f"Consider focusing more on: {', '.join(weaknesses)}.\n\n"
    
    # Generate personalized learning resources
    feedback += f"### 📚 Suggested Learning Resources\n"
    
    if weaknesses:
        # We'll generate different types of resources for their weak areas
        feedback += f"Based on your performance, here are some resources to help you improve:\n\n"
        
        for area in weaknesses:
            feedback += f"*For {area}:*\n"
            
            # These are hypothetical resources - in a real app, you might pull from a database or API
            if "Basic" in area:
                feedback += f"- Review foundational concepts in {topic} tutorials\n"
                feedback += f"- Practice with beginner-level exercises\n"
            elif "Advanced" in area:
                feedback += f"- Explore advanced documentation on {topic}\n"
                feedback += f"- Try building complex projects that use {topic}\n"
            elif "Problem Solving" in area:
                feedback += f"- Work through coding challenges focused on {topic}\n"
                feedback += f"- Join study groups or forums to discuss problem-solving approaches\n"
            elif "Application" in area:
                feedback += f"- Build small projects applying {topic} concepts\n"
                feedback += f"- Follow tutorials that show practical applications\n"
            
            feedback += "\n"
    else:
        feedback += f"You're doing great! To continue advancing your knowledge of {topic}, consider:\n\n"
        feedback += f"- Exploring more advanced topics related to {topic}\n"
        feedback += f"- Teaching others to solidify your understanding\n"
        feedback += f"- Working on projects that combine {topic} with other technologies\n"
    
    return feedback

def main():
    st.sidebar.title("Adaptive MCQ Generator")

    if not st.session_state.questions:
        topic = st.sidebar.text_input("Enter a coding topic:", key="topic_input")
        
        if st.sidebar.button("Start Assessment") and topic:
            st.session_state.topic = topic
            start_assessment()
    else:
        if st.sidebar.button("Start New Assessment", key="sidebar_new_assessment"):
            restart()

    # Display quiz content
    if st.session_state.questions:
        st.title(f"📚 Adaptive Assessment: {st.session_state.topic}")
        
        if not st.session_state.completed:
            # Display current question
            q_idx = st.session_state.current_question
            question_data = st.session_state.questions[q_idx]
            
            st.subheader(f"Question {q_idx + 1} of {len(st.session_state.questions)}")
            st.write(question_data["question"])
            
            # Display category
            category = question_data.get("category", "General")
            st.caption(f"Category: {category}")
            
            # Create a unique key for each radio button
            radio_key = f"radio_{q_idx}"
            
            # Initialize the answer in session state if not present
            if radio_key not in st.session_state:
                st.session_state[radio_key] = None
                
            # Display options
            selected_option = st.radio(
                "Select your answer:",
                question_data["options"],
                key=radio_key
            )
            
            # Store the answer in session state
            st.session_state.answers[q_idx] = selected_option
            
            # Submit button
            if st.button("Submit Answer", key=f"submit_{q_idx}"):
                submit_answer(q_idx)
                st.rerun()
                
            # Display progress
            progress = (q_idx + 1) / len(st.session_state.questions)
            st.progress(progress)
            
        else:
            # Quiz completed - show results
            st.success("### Assessment Complete! 🎉")
            st.write(f"Your score: {st.session_state.score}/{len(st.session_state.questions)}")
            
            percentage = (st.session_state.score / len(st.session_state.questions)) * 100
            
            if percentage == 100:
                st.balloons()
                st.success("🎯 Perfect Score! Excellent work!")
            elif percentage >= 70:
                st.info("👍 Good job! Keep practicing!")
            else:
                st.warning("📚 You might need more practice on this topic.")
                
            # Analyze performance by category
            performance, strengths, weaknesses = analyze_performance()
            
            # Display performance charts
            st.subheader("📊 Performance Analysis")
            display_performance_charts(performance)
            
            # Generate personalized feedback
            feedback = get_feedback_and_resources(strengths, weaknesses, st.session_state.topic)
            st.markdown(feedback)
            
            # Review answers
            st.subheader("📝 Review Your Answers")
            for i, q in enumerate(st.session_state.questions):
                with st.expander(f"Question {i+1} - {q.get('category', 'General')}"):
                    st.write(q["question"])
                    user_answer = st.session_state.answers.get(i, "Not answered")
                    
                    if user_answer == q["correct_answer"]:
                        st.success(f"Your answer: {user_answer} ✅")
                    else:
                        st.error(f"Your answer: {user_answer} ❌")
                        st.info(f"Correct answer: {q['correct_answer']}")
            
            if st.button("Start New Assessment", key="main_new_assessment"):
                restart()
                st.rerun()
    else:
        st.write("Enter a topic in the sidebar and click 'Start Assessment' to begin.")

if __name__ == "__main__":
    main()