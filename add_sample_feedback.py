import sqlite3
from datetime import datetime, timedelta

# Connect to the database
conn = sqlite3.connect('linkedin_data.db')
cursor = conn.cursor()

# Current time
now = datetime.now()

# Sample data with different tones, topics, etc.
sample_posts = [
    {
        "content": "Excited to share my thoughts on AI in marketing! The potential for personalization and customer insights is game-changing. What's your experience with AI tools in your marketing strategy? #AIMarketing #DigitalTransformation #MarketingTrends",
        "topic": "AI in Marketing",
        "tone": "Conversational",
        "include_cta": True,
        "include_hashtags": True,
        "feedback": "positive",
        "generation_time": (now - timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        "content": "Leadership isn't about having all the answers—it's about asking the right questions. Today I challenged my team to think differently about our quarterly goals, and the insights were invaluable. True growth comes from collaborative problem-solving. #Leadership #TeamDevelopment",
        "topic": "Leadership",
        "tone": "Inspirational",
        "include_cta": False,
        "include_hashtags": True,
        "feedback": "positive",
        "generation_time": (now - timedelta(days=12)).strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        "content": "New research reveals that companies with diverse leadership teams outperform competitors by 35%. This data confirms what we already knew: diversity isn't just good ethics, it's good business. Here's a link to the full study. #DiversityInBusiness #Leadership",
        "topic": "Diversity in Business",
        "tone": "Educational",
        "include_cta": True,
        "include_hashtags": True,
        "feedback": "negative",
        "generation_time": (now - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        "content": "Just released our comprehensive guide to remote work best practices. After 2 years of research across 150+ companies, we've identified the key factors that make remote teams successful. Download now (link in comments). #RemoteWork #FutureOfWork #Productivity",
        "topic": "Remote Work",
        "tone": "Professional",
        "include_cta": True,
        "include_hashtags": True,
        "feedback": "positive",
        "generation_time": (now - timedelta(days=8)).strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        "content": "Our Q3 webinar series kicks off next week! Join industry experts as we explore emerging technologies reshaping finance. Reserve your spot now—spaces are limited. #FinTech #DigitalBanking #Innovation",
        "topic": "FinTech Webinar",
        "tone": "Promotional",
        "include_cta": True,
        "include_hashtags": True,
        "feedback": "neutral",
        "generation_time": (now - timedelta(days=6)).strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        "content": "Thrilled to announce our partnership with Green Solutions to reduce our carbon footprint by 40% over the next two years. Sustainability isn't just a goal—it's our responsibility. #Sustainability #ClimateAction",
        "topic": "Sustainability",
        "tone": "Inspirational",
        "include_cta": False,
        "include_hashtags": True,
        "feedback": "positive",
        "generation_time": (now - timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        "content": "Data privacy matters more than ever. Our new white paper examines how regulations like GDPR and CCPA are impacting global businesses and provides actionable compliance strategies. Check it out and share your thoughts! #DataPrivacy #Compliance #GDPR",
        "topic": "Data Privacy",
        "tone": "Educational",
        "include_cta": True,
        "include_hashtags": True,
        "feedback": "positive",
        "generation_time": (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        "content": "Just completed the Advanced Business Strategy certification! Grateful for the opportunity to expand my knowledge and connect with amazing professionals in the program. What professional development are you focusing on this quarter? #ProfessionalDevelopment #LifelongLearning",
        "topic": "Professional Development",
        "tone": "Conversational",
        "include_cta": True,
        "include_hashtags": True,
        "feedback": "positive",
        "generation_time": (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        "content": "Breaking: Our new mobile app launches today! After months of user testing and refinement, we're proud to deliver a seamless experience that will transform how you manage your workflow. Download now from the App Store or Google Play. #ProductLaunch #Innovation #MobileApp",
        "topic": "Product Launch",
        "tone": "Promotional",
        "include_cta": True,
        "include_hashtags": True,
        "feedback": "negative",
        "generation_time": now.strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        "content": "Honored to be speaking at next month's Tech Forward Conference on 'Building Ethical AI Systems.' If you're attending, let's connect! #AI #TechEthics #Conference",
        "topic": "AI Ethics",
        "tone": "Professional",
        "include_cta": True,
        "include_hashtags": True,
        "feedback": "positive",
        "generation_time": now.strftime('%Y-%m-%d %H:%M:%S')
    }
]

# Insert sample posts
for post in sample_posts:
    cursor.execute('''
    INSERT INTO generated_posts
    (content, topic, tone, include_cta, include_hashtags, feedback, generation_time)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        post["content"],
        post["topic"],
        post["tone"],
        post["include_cta"],
        post["include_hashtags"],
        post["feedback"],
        post["generation_time"]
    ))

# Commit changes and close connection
conn.commit()
print(f"Added {len(sample_posts)} sample posts to the database")
conn.close()