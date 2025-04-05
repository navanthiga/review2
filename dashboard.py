# dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
import datetime
from db_utils import get_user_progress, log_activity

def dashboard_page():
    """Display user's learning dashboard"""
    st.title("📊 Learning Dashboard")
    
    if not st.session_state.user:
        st.warning("Please login to view your dashboard")
        return
    
    user_id = st.session_state.user['id']
    username = st.session_state.user['username']
    log_activity(user_id, "view_dashboard")
    
    # Get user progress data
    progress = get_user_progress(user_id)
    
    # Welcome message
    st.write(f"## Welcome back, {st.session_state.user['full_name'] or username}!")
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🎬 Videos Watched", 
            value=len(progress['videos_watched'])
        )
    
    with col2:
        quiz_count = sum(item.get('attempt_count', 0) for item in progress['quiz_performance'])
        st.metric(
            label="📝 Quizzes Taken", 
            value=quiz_count
        )
    
    with col3:
        # Calculate average quiz score
        if progress['quiz_performance']:
            avg_score = sum(item.get('avg_percentage', 0) for item in progress['quiz_performance']) / len(progress['quiz_performance'])
            st.metric(
                label="📊 Avg. Quiz Score", 
                value=f"{avg_score:.1f}%"
            )
        else:
            st.metric(
                label="📊 Avg. Quiz Score", 
                value="N/A"
            )
    
    # Display videos watched section
    st.subheader("🎬 Your Learning Progress")
    
    if progress['videos_watched']:
        # Convert to DataFrame for visualization
        videos_df = pd.DataFrame(progress['videos_watched'])
        
        # Create chart
        video_chart = alt.Chart(videos_df).mark_bar().encode(
            x=alt.X('topic:N', title='Topic', sort='-y'),
            y=alt.Y('completion_percentage:Q', title='Completion %'),
            color=alt.value('#4CAF50'),
            tooltip=['topic', 'completion_percentage', 'watch_count']
        ).properties(
            title='Videos Watched',
            height=250
        )
        
        st.altair_chart(video_chart, use_container_width=True)
    else:
        st.info("You haven't watched any videos yet. Start learning!")
    
    # Quiz performance section
    st.subheader("📝 Quiz Performance")
    
    if progress['quiz_performance']:
        # Convert to DataFrame for visualization
        quiz_df = pd.DataFrame(progress['quiz_performance'])
        
        # Create chart
        quiz_chart = alt.Chart(quiz_df).mark_bar().encode(
            x=alt.X('topic:N', title='Topic', sort='-y'),
            y=alt.Y('avg_percentage:Q', title='Average Score %'),
            color=alt.value('#2196F3'),
            tooltip=['topic', 'avg_percentage', 'attempt_count', 'high_score']
        ).properties(
            title='Quiz Performance',
            height=250
        )
        
        st.altair_chart(quiz_chart, use_container_width=True)
    else:
        st.info("You haven't taken any quizzes yet. Test your knowledge!")
    
    # Recent activity section
    st.subheader("🔍 Recent Activity")
    
    if progress['recent_activities']:
        for activity in progress['recent_activities']:
            activity_type = activity['activity_type'].replace('_', ' ').title()
            timestamp = datetime.datetime.fromisoformat(str(activity['timestamp']).replace('Z', '+00:00'))
            time_ago = (datetime.datetime.now() - timestamp).days
            
            if time_ago == 0:
                hours_ago = (datetime.datetime.now() - timestamp).seconds // 3600
                if hours_ago == 0:
                    minutes_ago = (datetime.datetime.now() - timestamp).seconds // 60
                    time_display = f"{minutes_ago} minutes ago"
                else:
                    time_display = f"{hours_ago} hours ago"
            else:
                time_display = f"{time_ago} days ago"
            
            activity_details = ""
            if activity['activity_details']:
                try:
                    details = st.json.loads(activity['activity_details'])
                    if 'topic' in details:
                        activity_details = f" - {details['topic']}"
                    if 'score' in details and 'max_score' in details:
                        activity_details += f" (Score: {details['score']}/{details['max_score']})"
                except:
                    pass
            
            st.write(f"**{activity_type}**{activity_details} - {time_display}")
    else:
        st.info("No recent activity found. Start learning!")