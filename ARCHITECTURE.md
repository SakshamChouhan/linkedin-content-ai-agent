# LinkedIn Content Creator AI - Technical Architecture

This document provides a detailed overview of the LinkedIn Content Creator AI's technical architecture, components, and data flow.

## System Architecture

The application follows a modular design with the following key components:

```
+---------------------+     +---------------------+     +----------------------+
|                     |     |                     |     |                      |
|  LinkedIn Profiles  |     |   User Interface    |     |  Gemini AI API       |
|  (Data Source)      |     |   (Streamlit)       |     |  (Content Generation)|
|                     |     |                     |     |                      |
+----------+----------+     +---------+-----------+     +-----------+----------+
           |                          |                             |
           v                          v                             v
+----------+-----------------------------------------------------------+
|                                                                       |
|                       LinkedIn Content Creator AI                     |
|                                                                       |
| +----------------+  +----------------+  +----------------+            |
| |                |  |                |  |                |            |
| | Data Collection|  | Data Analysis  |  | Content        |            |
| | Module         |  | Module         |  | Generation     |            |
| | (Scraper)      |  | (Analyzer)     |  | Module         |            |
| |                |  |                |  |                |            |
| +-------+--------+  +-------+--------+  +-------+--------+            |
|         |                   |                   |                     |
|         v                   v                   v                     |
| +-------+-------------------+-------------------+----------------+    |
| |                                                                |    |
| |                      MongoDB Database                          |    |
| |                                                                |    |
| +----------------------------------------------------------------+    |
|                                                                       |
+-----------------------------------------------------------------------+
```

## Component Details

### 1. Data Collection Module (`linkedin_scraper.py`)

The scraper module is responsible for extracting data from LinkedIn profiles:

- **Functions**:
  - `scrape_linkedin_profile(profile_url)`: Scrape a LinkedIn profile (profile info, posts, engagement)
  - `scrape_multiple_profiles(profile_urls)`: Batch scrape profiles

- **Data Collected**:
  - Profile information (name, headline, connections)
  - Post content and engagement metrics (likes, comments, shares)
  - Posting patterns (time, date, frequency)

### 2. Data Analysis Module (`data_analyzer.py`)

This module processes the raw data into actionable insights:

- **Functions**:
  - `analyze_post_engagement(posts_df)`: Analyze engagement metrics
  - `analyze_posting_patterns(posts_df)`: Identify optimal posting times
  - `analyze_content_length(posts_df)`: Analyze content length & correlations
  - `get_optimal_posting_time(posts_df)`: Recommend best time to post
  - `analyze_hashtags(posts_df)`: Hashtag effectiveness
  - `sentiment_analysis(posts_df)`: Post sentiment breakdown

- **Analysis Types**:
  - Engagement correlation with content type
  - Time-based engagement patterns
  - Content length optimization
  - Topic, tone, and sentiment performance analysis

### 3. Content Generation Module (`content_generator.py`)

Interfaces with Google's Gemini AI to generate LinkedIn posts:

- **Functions**:
  - `generate_post(profile_url, topic, tone, ...)`: Create LinkedIn post variations
  - `update_feedback_preferences(...)`: Learn from feedback

- **AI Integration**:
  - Uses Gemini-1.5-pro for content
  - Prompt engineering based on user profile, history, and feedback
  - Receives content suggestions, hashtags, and tones

### 4. Database Module (`database.py`)

Handles all data persistence and retrieval using MongoDB:

- **Functions**:
  - `initialize_database()`: Connect and verify MongoDB connection
  - `save_profile(profile_data)`: Store profile info
  - `get_profile_urls()`: List available profile URLs
  - `get_profile_data_by_url(profile_url)`: Retrieve full profile data
  - `get_posts_by_profile_url(profile_url)`: Posts for a given profile (returns DataFrame)
  - `save_analysis_result(profile_url, analysis_data)`: Save analytics for display
  - `save_feedback(data)`: Store user feedback (with timestamp)
  - `get_feedback_by_profile_url(profile_url)`: Retrieve all feedback for analytics

- **MongoDB Collections**:
  - `profiles`: LinkedIn profile information
  - `posts`: Scraped posts & engagement data
  - `analysis`: Analysis results for profiles
  - `feedback`: User feedback on posts and content

### 5. Web Interface (`app.py`)

Streamlit-based user interface with multiple interactive pages:

- **Pages**:
  - Profile Analysis: View scraped LinkedIn data by profile
  - Content Insights: Explore content performance and trends
  - Post Generator: Create & customize AI-powered LinkedIn posts
  - Feedback Dashboard: Track post performance, likes/dislikes/saves, feedback trends

- **Features**:
  - Interactive visualizations (matplotlib, pandas)
  - Feedback-driven learning loop
  - Form-based content generation & feedback submission
  - All analytics live-updated from MongoDB

## Data Flow

1. **Data Collection Process**:
   - User enters LinkedIn profile URL
   - System scrapes profile and post data (via Data Collection Module)
   - Data is processed and stored in MongoDB

2. **Analysis Process**:
   - Raw data retrieved from MongoDB
   - Analysis functions run on posts, profiles, or feedback
   - Insights and visualizations displayed in Streamlit UI

3. **Content Generation Process**:
   - User provides topic, profile selection, and preferences
   - System constructs Gemini AI prompt using profile history and feedback
   - Content and hashtags generated; user provides feedback

4. **Learning & Feedback Loop**:
   - User and analytics feedback is saved in MongoDB
   - System adapts suggestions based on feedback (topic, tone, engagement, sentiment analytics)
   - Dashboard visualizes KPIs, trends, and topic/tone effectiveness

## Technology Stack Details

- **Frontend**: Streamlit 1.32.0+
- **Data Processing**: Pandas 2.2.0, NumPy 1.26.4
- **Visualization**: Matplotlib 3.8.3
- **AI**: Google Generative AI 0.8.5+
- **Web Scraping**: Trafilatura 1.6.3
- **Database**: MongoDB

## Security Considerations

- API keys and DB URIs are loaded from `.env` and never hardcoded
- Database can run locally or with strict limited network access for privacy
- Error handling prevents sensitive user/key information from exposure

## Performance & Scalability

- Efficient MongoDB queries and indexing strategies (collections auto-created)
- Use of pandas for fast in-memory analysis
- Caching mechanism for expensive operations
- Batched processing for multiple profiles
- Parallel processing where applicable

---

**Note:**  
Ensure your `.env` file defines both `GOOGLE_API_KEY` and `MONGO_URI` for proper application functionality.
