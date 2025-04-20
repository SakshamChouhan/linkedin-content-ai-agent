import os
from pymongo import MongoClient
import pandas as pd
from dotenv import load_dotenv
import datetime

# Load environment variables from .env file
load_dotenv()

# MongoDB connection string
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Client Initialization
client = MongoClient(MONGO_URI)
db = client["linkedin_data"]  # The database

# Collection names
PROFILES_COLLECTION = "profiles"
POSTS_COLLECTION = "posts"
ANALYSIS_COLLECTION = "analysis"
FEEDBACK_COLLECTION = "feedback"

# ────────────────────────────────────────────────────────────────────────────────
# Initialize the database (useful to check connection and collections)
def initialize_database():
    try:
        # Testing the connection by listing collections
        client.admin.command('ping')
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

# ────────────────────────────────────────────────────────────────────────────────
# Get all unique profile URLs
def get_profile_urls():
    profiles = db[PROFILES_COLLECTION].find({}, {"profile_url": 1, "_id": 0})
    return [profile['profile_url'] for profile in profiles]

# ────────────────────────────────────────────────────────────────────────────────
# Get profile data by profile URL
def get_profile_data_by_url(profile_url: str):
    profile = db[PROFILES_COLLECTION].find_one({"profile_url": profile_url})
    if not profile:
        return None
    return {
        "name": profile["name"],
        "headline": profile["headline"],
        "location": profile["location"],
        "connections_count": profile["connections"],
        "followers_count": profile["followers"],
        "posts": profile["posts_scraped"],  # List of posts
        "avg_engagement": profile["avg_engagement"],  # Average engagement
    }

# ────────────────────────────────────────────────────────────────────────────────
# Get posts by profile URL
def get_posts_by_profile_url(profile_url: str):
    posts_cursor = db[POSTS_COLLECTION].find({"profile_url": profile_url})
    posts = list(posts_cursor)
    if not posts:
        return pd.DataFrame() 
    return pd.DataFrame(posts)


def save_analysis_result(profile_url: str, analysis_data: dict):
    doc = {
        "profile_url": profile_url,
        "analysis": analysis_data,
        "timestamp": pd.Timestamp.now()
    }
    db["analysis"].insert_one(doc)


def get_analysis_by_profile_url(profile_url):
    profile_data = db[ANALYSIS_COLLECTION].find_one({"profile_url": profile_url})
    if profile_data:
        return profile_data.get('analysis', {})
    return {}

def save_feedback(data):
   
    db[FEEDBACK_COLLECTION].insert_one(data)


def get_feedback_by_profile_url(profile_url):
    feedback_data = list(db[FEEDBACK_COLLECTION].find({"profile_url": profile_url}))
    if feedback_data:
        return pd.DataFrame(feedback_data)
    return pd.DataFrame()

