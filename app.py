import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from data_analyzer import (
    analyze_post_engagement,
    analyze_posting_patterns,
    analyze_hashtags,
    analyze_content_length,
    sentiment_analysis,
    get_optimal_posting_time
)

from content_generator import generate_post, update_feedback_preferences

from database import (
    initialize_database,
    get_profile_urls,
    get_profile_data_by_url,
    get_posts_by_profile_url,
    save_analysis_result
)

# Page configuration
st.set_page_config(
    page_title="LinkedIn Content Creator AI",
    page_icon="📊",
    layout="wide"
)

def make_serializable(obj):
    if isinstance(obj, dict):
        return {str(k): make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (np.float64, np.int64, np.int32, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.ndarray, pd.Series)):
        return make_serializable(obj.tolist())
    elif isinstance(obj, pd.Timestamp):
        return obj.to_pydatetime()
    elif isinstance(obj, float) and np.isnan(obj):
        return None
    return obj

# Initialize the database (MongoDB)
initialize_database()

# Main page title
st.title("LinkedIn Content Creator AI")
st.markdown("This tool helps you analyze LinkedIn data stored in MongoDB and generate optimized posts.")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", ["Profile Analysis", "Content Insights", "Post Generator", "Feedback Dashboard"])

# ─── PROFILE ANALYSIS ───────────────────────────────────────────────────────────
if page == "Profile Analysis":
    st.header("LinkedIn Profile Analysis")

    # Fetch all profile URLs from MongoDB
    profile_urls = get_profile_urls()
    if not profile_urls:
        st.warning("No profiles found in the database.")
    else:
        profile_option = st.selectbox("Select a profile to analyze", profile_urls)

        if st.button("Load Profile Data"):
            st.spinner("Loading profile data...")
            profile_data = get_profile_data_by_url(profile_option)
            if not profile_data:
                st.error("No data found for this profile.")
            else:
                posts_data = get_posts_by_profile_url(profile_option)
                st.success(f"Loaded profile: {profile_data['name']}")

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Profile Information")
                    st.write(f"**Name:** {profile_data['name']}")
                    st.write(f"**Headline:** {profile_data['headline']}")
                    st.write(f"**Location:** {profile_data['location']}")
                    st.write(f"**Connections:** {profile_data['connections_count']}")
                    st.write(f"**Followers:** {profile_data['followers_count']}")
                with col2:
                    st.subheader("Activity Overview")
                    st.write(f"**Total Accessed Posts:** {profile_data['posts']}")
                    st.write(f"**Average Engagement:** {profile_data['avg_engagement']:.1f}")

                st.subheader("Recent Posts")
                selected_columns = ['post_url', 'date', 'time', 'content_length_type', 'type', 'likes', 'comments', 'shares', 'engagement']
                posts_df = pd.DataFrame(posts_data)
                posts_df = posts_df[selected_columns]
                posts_df.index = posts_df.index + 1
                st.dataframe(posts_df)


# ─── CONTENT INSIGHTS ───────────────────────────────────────────────────────────
elif page == "Content Insights":
    profile_urls = get_profile_urls()
    if not profile_urls:
        st.warning("No profiles found in the database.")
    else:
        profile_option = st.selectbox("Select a profile for insights", profile_urls, key="insights_profile")
        posts_df = get_posts_by_profile_url(profile_option)

        st.header("Content Insights & Trends")

        if posts_df.empty:
            st.warning("No posts data for this profile.")
        else:
            # ───────────────────────────── Engagement Analysis ─────────────────────────────
            st.subheader("📈 Engagement Analysis")
            col1, col2 = st.columns(2)

            with col1:
                fig, ax = plt.subplots(figsize=(10, 6))
                engagement_by_type = analyze_post_engagement(posts_df)
                engagement_by_type.plot.bar(ax=ax)
                ax.set(title="Average Engagement by Content Type", xlabel="Type", ylabel="Engagement")
                st.pyplot(fig)

            with col2:
                sentiment_counts = sentiment_analysis(posts_df)
                st.write("Sentiment Breakdown:")
                for sentiment, count in sentiment_counts.items():
                    st.write(f"**{sentiment}**: {count}")

            # ───────────────────────────── Posting Patterns ─────────────────────────────
            st.subheader("⏰ Posting Patterns")
            engagement_by_hour, correlation = analyze_posting_patterns(posts_df)

            fig, ax = plt.subplots(figsize=(10, 6))
            engagement_by_hour.plot.line(marker='o', ax=ax)
            ax.set(title="Posting Time vs Engagement", xlabel="Hour of Day", ylabel="Engagement")
            ax.grid(True, linestyle='--', alpha=0.7)
            st.pyplot(fig)

            st.info(f"**Optimal posting time**: {get_optimal_posting_time(posts_df)}")
            st.info(f"**Correlation between posting time and engagement**: {correlation:.2f}")

            # ───────────────────────────── Content Length Analysis ─────────────────────────────
            st.subheader("📝 Content Length Analysis")
            engagement_by_length, length_correlation = analyze_content_length(posts_df)

            fig, ax = plt.subplots(figsize=(10, 6))
            engagement_by_length.plot.bar(ax=ax)
            ax.set(title="Content Length Category vs Engagement", xlabel="Length Category", ylabel="Engagement")
            st.pyplot(fig)

            if length_correlation.get('r_squared') is not None:
                st.info(f"**Correlation (R²) between content length and engagement**: {length_correlation['r_squared']:.2f}")
            else:
                st.warning("⚠️ Not enough variation in post lengths to calculate correlation.")

            # ───────────────────────────── Hashtag Analysis ─────────────────────────────
            st.subheader("🔍 Hashtag Analysis")
            top_hashtags, hashtag_engagement = analyze_hashtags(posts_df)

            if top_hashtags:
                st.write("🔝 **Top 5 Hashtags by Usage**")
                for hashtag, count in top_hashtags:
                    st.markdown(f"- **#{hashtag}** — {count} uses")

                engagement_data = pd.DataFrame([
                    {"Hashtag": f"#{hashtag}", "Avg. Engagement": round(engagement, 2)}
                    for hashtag, engagement in hashtag_engagement.items()
                ])
                engagement_data = engagement_data.sort_values(by="Avg. Engagement", ascending=False).reset_index(drop=True)

                st.write("📊 **Average Engagement by Hashtag**")
                st.dataframe(engagement_data, use_container_width=True, hide_index=True)

                fig, ax = plt.subplots(figsize=(10, 6))
                engagement_data.plot.bar(x='Hashtag', y='Avg. Engagement', ax=ax, legend=False, color='#4c91f0')
                ax.set_title("Hashtag Engagement", fontsize=14)
                ax.set_ylabel("Average Engagement")
                ax.set_xlabel("")
                ax.grid(True, linestyle='--', alpha=0.5)
                st.pyplot(fig)
            else:
                st.warning("No hashtags found in the data.")

            # ───────────────────────────── Background Save to MongoDB ─────────────────────────────
            try:
                analysis_data = {
                "engagement_by_type": make_serializable(engagement_by_type.to_dict()),
                "sentiment_counts": make_serializable(sentiment_counts),
                "engagement_by_hour": make_serializable(engagement_by_hour.to_dict()),
                "posting_time_correlation": make_serializable(correlation),
                "optimal_posting_time": get_optimal_posting_time(posts_df),
                "engagement_by_length": make_serializable(engagement_by_length.to_dict()),
                "length_correlation": make_serializable(length_correlation),
                "top_hashtags": make_serializable(dict(top_hashtags)),
                "hashtag_engagement": make_serializable(hashtag_engagement),
            }
                save_analysis_result(profile_option, analysis_data)
            except Exception as e:
                st.warning(f"⚠️ Failed to save analysis to database: {e}")

# ─── POST GENERATOR ─────────────────────────────────────────────────────────────
elif page == "Post Generator":
    st.header("AI Post Generator")

    # Profile selection dropdown
    profile_urls = get_profile_urls()  # Function to fetch profile URLs
    if profile_urls:
        profile_option = st.selectbox("Select a profile to post as", profile_urls)
    else:
        st.warning("No profiles found in the database.")
        profile_option = None  # Handle case if no profiles are available

    # Input for generating post
    topic = st.text_input("Enter a topic or theme for your post:")

    with st.expander("Advanced Options"):
        tone = st.select_slider("Select tone:", ["Professional", "Conversational", "Inspirational", "Educational", "Promotional"])
        include_cta = st.checkbox("Include a call-to-action", True)
        max_length = st.slider("Maximum post length", 100, 1000, 500)
        include_hashtags = st.checkbox("Include hashtags", True)
        num_hashtags = st.slider("Number of hashtags", 1, 10, 3) if include_hashtags else 0

    # Use Session State to track generated posts
    if "latest_posts" not in st.session_state:
        st.session_state.latest_posts = []

    if st.button("Generate Post"):
        if not topic:
            st.warning("Please enter a topic.")
        elif not profile_option:
            st.warning("Please select a profile to post as.")
        else:
            with st.spinner("Generating posts…"):
                posts = generate_post(
                    profile_url=profile_option,
                    topic=topic,
                    tone=tone,
                    include_cta=include_cta,
                    max_length=max_length,
                    include_hashtags=include_hashtags,
                    num_hashtags=num_hashtags
                )
                if not posts:
                    st.error("Failed to generate posts.")
                else:
                    st.session_state.latest_posts = posts

    # For each post variation allow independent feedback submission with session state
    if st.session_state.get("latest_posts"):
        st.subheader("Post Variations")
        for i, p in enumerate(st.session_state.latest_posts):
            st.markdown(f"#### Variation {i+1}")
            st.markdown(p["content"].replace("\n", "<br>"), unsafe_allow_html=True)

            form_key = f"feedback_form_{i}"
            submitted_key = f"submitted_feedback_{i}"

            if submitted_key not in st.session_state:
                st.session_state[submitted_key] = False

            # Allow feedback submission even if posts are regenerated
            with st.form(key=form_key):
                textual_feedback = st.text_area("Provide your feedback:", key=f"textual_feedback_{i}")
                feedback_choice = st.radio(
                    "How do you feel about this post?",
                    ["👍 Like", "👎 Dislike", "💾 Save"], key=f"radio_{i}"
                )
                submit_btn = st.form_submit_button("Submit Feedback")
                if submit_btn:
                    feedback_map = {
                        "👍 Like": "positive",
                        "👎 Dislike": "negative",
                    }

                    # Save feedback to DB
                    try:
                        update_feedback_preferences(
                            post_content=p["content"],
                            feedback=feedback_map[feedback_choice],
                            profile_url=profile_option,
                            textual_feedback=textual_feedback,
                            topic=topic,
                            tone=tone,
                            # scheduled_time intentionally not set here
                        )
                        st.session_state[submitted_key] = True
                        st.success("✅ Feedback submitted & saved to database.")
                        st.info(f"Feedback: {feedback_map[feedback_choice]}\nText: {textual_feedback}")
                    except Exception as e:
                        st.error(f"❌ Failed to save feedback: {e}")
            # Show info about already submitted feedback
            if st.session_state[submitted_key]:
                st.info("Feedback already submitted for this variation. Thank you!")


# Footer
st.markdown("---")
st.markdown("LinkedIn Content Creator AI © 2025")
