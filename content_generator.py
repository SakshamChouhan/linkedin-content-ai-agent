import json
import random
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv  # To load environment variables
import os
from database import get_analysis_by_profile_url, save_feedback, get_feedback_by_profile_url

# Load environment variables from .env
load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Global preferences based on user feedback
user_preferences = {
    'preferred_tone': 'Conversational',
    'optimal_length': 'medium',
    'preferred_content_types': ['professional development', 'industry trends'],
    'hashtag_preference': True
}

def generate_post(profile_url, topic, tone="Conversational", include_cta=True, max_length=500, include_hashtags=True, num_hashtags=3):
    print("Here")
    try:
        # Get analysis and feedback for the profile
        analysis = get_analysis_by_profile_url(profile_url)
        feedback_df = get_feedback_by_profile_url(profile_url)

        # Extract insights from analysis
        insights = ""
        if analysis:
            if 'optimal_posting_time' in analysis:
                insights += f"Optimal posting time: {analysis['optimal_posting_time']}. "
            if 'top_hashtags' in analysis:
                top_hashtags = ", ".join(analysis['top_hashtags'].keys())
                insights += f"Top performing hashtags: {top_hashtags}. "

        # Extract insights from feedback
        feedback_insights = ""
        if not feedback_df.empty:
            positive_feedback = feedback_df[feedback_df["feedback"] == "positive"]
            negative_feedback = feedback_df[feedback_df["feedback"] == "negative"]
            neutral_feedback = feedback_df[feedback_df["feedback"] == "neutral"]

            feedback_insights += f"\nUser prefers content like:\n"
            for content in positive_feedback["content"].head(2):
                feedback_insights += f"- {content[:150]}...\n"

            if not negative_feedback.empty:
                feedback_insights += "\nAvoid content like:\n"
                for content in negative_feedback["content"].head(2):
                    feedback_insights += f"- {content[:150]}...\n"

            if feedback_df["textual_feedback"].notnull().any():
                feedback_insights += "\nDirect user suggestions:\n"
                for fb in feedback_df["textual_feedback"].dropna().unique()[:2]:
                    feedback_insights += f"- {fb}\n"

        # System prompt
        system_instruction = "You are a LinkedIn content expert who creates engaging posts that drive high engagement."

        # Final prompt
        prompt = f"""
        {system_instruction}
        
        Create 3 variations of a LinkedIn post about {topic}.
        
        Guidelines:
        - Tone: {tone}
        - Max length: {max_length} characters
        - {include_cta and 'Include a call-to-action' or 'No call-to-action needed'}
        - {include_hashtags and f'Include {num_hashtags} relevant hashtags' or 'No hashtags'}

        Insights from LinkedIn analysis:
        {insights}

        Feedback-based content preferences:
        {feedback_insights}

        Ensure posts are professional, engaging, and follow best practices for LinkedIn.

        Return output in this JSON format:
        {{
          "posts": [
            {{
              "content": "Post content here",
              "estimated_engagement": 0-100
            }}
          ]
        }}

        Only return valid JSON. No explanation.
        """

        # Generate using Gemini
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 1500,
            }
        )

        response = model.generate_content(prompt)

        try:
            result = json.loads(response.text)
            return result["posts"]
        except json.JSONDecodeError:
            import re
            json_pattern = r'({[\s\S]*})'
            match = re.search(json_pattern, response.text)
            if match:
                result = json.loads(match.group(1))
                return result["posts"]
            else:
                raise ValueError("Could not parse JSON from Gemini response")

    except Exception as e:
        print(f"Error generating posts: {str(e)}")
        return [
            {"content": f"Here's my thoughts on {topic}. What do you think? #LinkedIn", "estimated_engagement": 50},
            {"content": f"Thoughts on {topic} lately. Curious to hear your take! #Career", "estimated_engagement": 45},
        ]


def update_feedback_preferences(
    post_content,
    feedback,
    profile_url,
    textual_feedback=None,
    topic=None,
    tone=None,
    scheduled_time=None,
):
    """
    Save feedback for a generated post to the database.
    
    Args:
        post_content (str): The content of the post.
        feedback (str): 'positive', 'negative', or 'neutral'.
        profile_url (str): The profile for which this feedback relates.
        textual_feedback (str, optional): Free-form user feedback.
        topic (str, optional): Topic of the post.
        tone (str, optional): Tone of the post.
        scheduled_time (str or datetime, optional): If this post is scheduled in the future.
    """
    try:
        # fallback timestamps for required fields
        now = datetime.now()
        feedback_doc = {
            "profile_url": profile_url,
            "content": post_content,
            "feedback": feedback,
            "textual_feedback": textual_feedback,
            "generation_time": now,
            "topic": topic,
            "tone": tone,
        }
        
        if scheduled_time:
            # Accept string, datetime, or pandas Timestamp
            if isinstance(scheduled_time, str):
                try:
                    feedback_doc["scheduled_time"] = pd.to_datetime(scheduled_time)
                except Exception:
                    feedback_doc["scheduled_time"] = now
            else:
                feedback_doc["scheduled_time"] = scheduled_time
        else:
            feedback_doc["scheduled_time"] = now

        save_feedback(feedback_doc)
        
    except Exception as e:
        print(f"❌ Failed to insert feedback into MongoDB: {e}")

