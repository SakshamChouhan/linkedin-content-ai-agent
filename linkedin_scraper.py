import argparse
import re
import time
import random
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import json
import os
from pymongo import MongoClient, UpdateOne
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import concurrent.futures

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB connection string from the .env file
MONGO_URI = os.getenv("MONGO_URI")

# --- Helper Functions ---

def clean_text(text):
    """Basic text cleaning."""
    if not text: return ""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def parse_url(url):
    """Extracts a potential username/identifier from a LinkedIn profile URL."""
    match = re.search(r'linkedin\.com/in/([^/?]+)', url)
    if match: return match.group(1)
    parts = url.strip('/').split('/')
    username = parts[-1] if parts else "unknown-profile"
    return username.split('?')[0]

def parse_connections_followers(text_list):
    """Parses connection/follower counts from a list of strings."""
    connections, followers = None, None
    if not text_list: return connections, followers
    for text in text_list:
        text_lower = text.lower()
        count_match = re.search(r'([\d,]+)\+?', text)
        count_str = count_match.group(1).replace(',', '') + ('+' if '+' in text else '') if count_match else None
        if 'connection' in text_lower: connections = count_str if count_str else text
        elif 'follower' in text_lower: followers = count_str if count_str else text
    return connections, followers


def parse_iso_datetime(iso_str):
    """Parses ISO 8601 timestamp string (handling 'Z') into datetime."""
    if not iso_str: return None
    try:
        
        if iso_str.endswith('Z'):
            iso_str = iso_str[:-1] + '+00:00'
        dt_object = datetime.fromisoformat(iso_str)
        
        return dt_object
    except ValueError as e:
        print(f"  Warning: Could not parse ISO datetime string '{iso_str}': {e}")
        return None
    except Exception as e:
        print(f"  Error parsing ISO datetime string '{iso_str}': {e}")
        return None


def extract_reactions_count(soup):
     """Extracts visible reaction count from single post page (fallback)."""
     try:
         reaction_button = soup.select_one('a[data-test-id="social-actions__reactions"], button span.social-details-social-counts__reactions-count') 
         if reaction_button:
             count_span = reaction_button.select_one('span[aria-hidden="true"], span.artdeco-button__text')
             if count_span:
                 count_text = clean_text(count_span.get_text())
                 count_match = re.search(r'([\d,]+)', count_text) # Extract digits
                 if count_match:
                     num_str = count_match.group(1).replace(',', '')
                     if 'k' in count_text.lower(): return int(float(num_str) * 1000)
                     if 'm' in count_text.lower(): return int(float(num_str) * 1000000)
                     return int(num_str)
     except Exception as e:
         print(f"  Warning: Could not extract visible reactions count: {e}")
     return 0

# --- Scraping Functions ---

def scrape_linkedin_profile_for_links(html_content, profile_url):
    """
    Parses the main profile HTML (public view) to extract basic info and POST URLs.
    (No changes needed here from previous version)
    """
    print("Parsing profile HTML for basic info and post links...")
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        profile_data = {"url": profile_url}
        post_urls = []

        # --- Username ---
        username = parse_url(profile_url)
        profile_data['username'] = username

        # --- Name ---
        try:
            name_tag = soup.find('h1', class_='top-card-layout__title')
            profile_data['name'] = clean_text(name_tag.get_text()) if name_tag else username.replace('-', ' ').title()
        except Exception:
            profile_data['name'] = username.replace('-', ' ').title()

        # --- Headline ---
        try:
            meta_desc = soup.find('meta', {'name': 'description'})
            og_desc = soup.find('meta', {'property': 'og:description'})
            headline_text = None
            if meta_desc and meta_desc.get('content'):
                headline_match = re.match(r'^(.*?)\s*·\s*Experience:', meta_desc['content'])
                if headline_match:
                    headline_text = clean_text(headline_match.group(1))
            elif og_desc and og_desc.get('content'):
                headline_match = re.match(r'^(.*?)\s*·\s*Experience:', og_desc['content'])
                if headline_match:
                    headline_text = clean_text(headline_match.group(1))
            profile_data['headline'] = headline_text if headline_text else f"Profile of {profile_data['name']}"
        except Exception:
            profile_data['headline'] = f"Profile of {profile_data['name']}"

        # --- Location ---
        try:
            subline_tag = soup.find('h3', class_='top-card-layout__first-subline')
            location_span = subline_tag.find('span', class_=lambda x: x is None or 'top-card__subline-item' in x) if subline_tag else None
            profile_data['location'] = clean_text(location_span.get_text()) if location_span else None
        except Exception:
            profile_data['location'] = None

        # --- Followers + Connections (count only) ---
        try:
            connections_followers_div = soup.find('div', class_='not-first-middot')
            if connections_followers_div:
                spans = connections_followers_div.find_all('span')
                raw_texts = [clean_text(s.get_text()) for s in spans]
                connections, followers = parse_connections_followers(raw_texts)
                profile_data['connections_count'] = connections
                profile_data['followers_count'] = followers
            else:
                profile_data['connections_count'], profile_data['followers_count'] = None, None
        except Exception:
            profile_data['connections_count'], profile_data['followers_count'] = None, None

        # --- Followers + Connections (raw list version as extra field) ---
        try:
            connections_followers_div = soup.find('div', class_='not-first-middot')
            if connections_followers_div:
                spans = connections_followers_div.find_all('span')
                profile_data['followers_connections'] = [clean_text(s.get_text()) for s in spans]
            else:
                profile_data['followers_connections'] = []
        except Exception as e:
            print(f"Error extracting followers/connections: {e}")
            profile_data['followers_connections'] = []

        # --- About Section ---
        try:
            about_section = soup.find('section', attrs={'data-section': 'summary'})
            if about_section:
                about_content_div = about_section.find('div', class_='core-section-container__content')
                if about_content_div:
                    about_text_div = about_content_div.find('div')
                    if about_text_div:
                        full_text = about_text_div.get_text(separator=' ', strip=True)
                        see_more_button = about_text_div.find('button', class_='sign-in-modal__outlet-btn')
                        if see_more_button:
                            see_more_text = see_more_button.get_text(strip=True)
                            if full_text.endswith(see_more_text):
                                full_text = full_text[:-len(see_more_text)].strip()
                        profile_data['about'] = full_text
                    else:
                        profile_data['about'] = None
                else:
                    profile_data['about'] = None
            else:
                profile_data['about'] = None
        except Exception as e:
            print(f"Error extracting about section: {e}")
        profile_data['about'] = None


        # Extract Post URLs
        activity_sections = soup.find_all('section', attrs={'data-section': 'posts'})
        print(f"Found {len(activity_sections)} activity sections for post links.")
        for section in activity_sections:
            activity_list = section.find('ul', attrs={'data-test-id': 'activities__list'})
            if activity_list:
                post_elements = activity_list.find_all('li', recursive=False)
                for post_el in post_elements:
                    link_tag = post_el.find('a', class_='base-card__full-link')
                    if link_tag and link_tag.has_attr('href'):
                        post_url = link_tag['href']
                        if post_url.startswith('http'):
                            post_urls.append(post_url)
                        elif post_url.startswith('/'):
                             post_urls.append(f"https://www.linkedin.com{post_url}")

        print(f"Found {len(post_urls)} potential post URLs.")

        print(profile_data)
        return profile_data, post_urls

    except Exception as e:
        print(f"Error parsing profile HTML for links: {e}")
        return None, []


def scrape_single_post_page(post_url):
    """
    Scrapes detailed data from a single LinkedIn post page using Selenium,
    prioritizing JSON-LD data and handling different types like VideoObject.
    """
    print(f"  Scraping single post: {post_url[:60]}...")
    options = Options()
    # ... (Selenium options setup) ...
    options.add_argument("--headless") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1024,768")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--incognito")

    service = Service(ChromeDriverManager().install())
    driver = None
    post_data = {'post_url': post_url}

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)
        wait = WebDriverWait(driver, 15)

        driver.get(post_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main, body")))
        time.sleep(random.uniform(1.5, 3))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # --- Attempt to Extract Data from JSON-LD (Revised Logic) ---
        json_data_root = None
        main_post_object = None # This will hold the relevant object (Posting, Video, etc.)
        try:
            script_tag = soup.find('script', type='application/ld+json')
            if script_tag and script_tag.string:
                json_data_root = json.loads(script_tag.string)

                # Check if the main object is nested within @graph
                if isinstance(json_data_root, dict) and '@graph' in json_data_root and isinstance(json_data_root['@graph'], list):
                    # Find the most relevant object within the graph
                    potential_types = ['DiscussionForumPosting', 'VideoObject', 'Article', 'ImageObject'] # Add more if needed
                    for item in json_data_root['@graph']:
                        if isinstance(item, dict) and item.get('@type') in potential_types:
                            main_post_object = item
                            print(f"  Found main object of type '{item.get('@type')}' in @graph for {post_url[:60]}...")
                            break # Take the first relevant one
                    if not main_post_object:
                         print(f"  Warning: Relevant object not found within @graph for {post_url[:60]}...")

                # Check if the main object is the top-level object
                elif isinstance(json_data_root, dict) and json_data_root.get('@type') in ['DiscussionForumPosting', 'VideoObject', 'Article', 'ImageObject']:
                     main_post_object = json_data_root
                     print(f"  Found main object of type '{main_post_object.get('@type')}' at top level for {post_url[:60]}...")

                else:
                    print(f"  Warning: JSON-LD structure not recognized or missing relevant @type for {post_url[:60]}...")

            else:
                print(f"  Warning: JSON-LD script tag not found or empty for {post_url[:60]}...")

        except json.JSONDecodeError as e:
            print(f"  Warning: Failed to decode JSON-LD for {post_url[:60]}... Error: {e}")
        except Exception as e:
            print(f"  Error processing JSON-LD for {post_url[:60]}...: {e}")

        # --- Populate post_data, prioritizing the found main_post_object ---

        # Timestamp
        iso_timestamp_str = main_post_object.get('datePublished') if main_post_object else None
        post_datetime = parse_iso_datetime(iso_timestamp_str)
        post_data['date'] = post_datetime.strftime('%Y-%m-%d') if post_datetime else None
        post_data['time'] = post_datetime.strftime('%H:%M') if post_datetime else None

        # Fallback for timestamp ONLY if JSON-LD method failed completely
        if not post_datetime:
             print(f"  JSON-LD timestamp failed, attempting fallback visual scrape for {post_url[:60]}...")
             try:
                 time_tag = soup.select_one('.main-feed-activity-card__entity-lockup time, span.feed-shared-actor__sub-description span[aria-hidden="true"]')
                 if time_tag:
                     relative_time_str = clean_text(time_tag.get_text())
                     print(f"  Fallback found relative time text: '{relative_time_str}' (parsing not implemented)") # Placeholder
                 else:
                     print(f"  Fallback timestamp tag not found.")
             except Exception as e_fb:
                 print(f"  Error during fallback timestamp extraction: {e_fb}")


        # Full Content
        post_data['content'] = None
        if main_post_object:
            # Check common keys for content based on object type
            post_data['content'] = clean_text(
                main_post_object.get('text') or \
                main_post_object.get('articleBody') or \
                main_post_object.get('description') # VideoObject often uses 'description'
            )
        if not post_data['content']: # Fallback to scraping visual element
             print(f"  Content not found in JSON-LD, attempting visual scrape for {post_url[:60]}...")
             try:
                 content_element = soup.select_one('p[data-test-id="main-feed-activity-card__commentary"], div.feed-shared-update-v2__description-wrapper .update-components-text')
                 if content_element:
                     post_data['content'] = clean_text(content_element.get_text(separator=' ', strip=True))
                 else:
                     print(f"  Warning: Fallback content element not found.")
             except Exception as e_fb:
                 print(f"  Warning: Error during fallback content extraction: {e_fb}")


        # Post Type (Inference - visual check is still good)
        post_data['type'] = 'unknown'
        try:
            json_type = main_post_object.get('@type') if main_post_object else None
            if json_type == 'VideoObject': post_data['type'] = 'video'
            elif json_type == 'Article': post_data['type'] = 'article'
            elif json_type == 'ImageObject': post_data['type'] = 'image'
            elif json_type == 'DiscussionForumPosting':
                 # Further refine based on visual cues if it's just a posting
                 if soup.select_one('ul.feed-images-content, div.update-components-image'): post_data['type'] = 'image'
                 elif soup.select_one('div.feed-shared-update-v2__content--includes-video, div.update-components-video'): post_data['type'] = 'video'
                 elif soup.select_one('div.feed-shared-poll, div.update-components-poll'): post_data['type'] = 'poll'
                 elif soup.select_one('div.feed-shared-document, div.update-components-document'): post_data['type'] = 'document'
                 elif post_data.get('content'): post_data['type'] = 'text'
            else: # Fallback to purely visual inference if JSON type is unhelpful/missing
                 if soup.select_one('ul.feed-images-content, div.update-components-image'): post_data['type'] = 'image'
                 elif soup.select_one('div.feed-shared-update-v2__content--includes-video, div.update-components-video'): post_data['type'] = 'video'
                 elif soup.select_one('div.feed-shared-article, div.update-components-article'): post_data['type'] = 'article'
                 elif soup.select_one('div.feed-shared-poll, div.update-components-poll'): post_data['type'] = 'poll'
                 elif soup.select_one('div.feed-shared-document, div.update-components-document'): post_data['type'] = 'document'
                 elif post_data.get('content'): post_data['type'] = 'text'
        except Exception as e: print(f"  Warning: Error inferring post type: {e}")

        # Engagement Metrics
        post_data['likes'] = extract_reactions_count(soup) # Keep visual scrape for likes
        # Comments: Use JSON-LD count if available
        post_data['comments'] = 0
        if main_post_object:
             # Check for commentCount or length of comment list
             if 'commentCount' in main_post_object:
                 post_data['comments'] = int(main_post_object['commentCount'])
             elif 'comment' in main_post_object and isinstance(main_post_object['comment'], list):
                 post_data['comments'] = len(main_post_object['comment'])

        post_data['shares'] = 0 # Still hard to get publicly
        post_data['engagement'] = post_data['likes'] + (post_data['comments'] * 3) + (post_data['shares'] * 5)

        # Other derived fields
        content = post_data.get('content', '')
        post_data['content_length'] = len(content)
        if post_data['content_length'] <= 200: post_data['content_length_type'] = 'short'
        elif post_data['content_length'] <= 500: post_data['content_length_type'] = 'medium'
        else: post_data['content_length_type'] = 'long'

        # Extract Hashtags
        post_data['has_hashtags'] = '#' in content
        if post_data['has_hashtags']:
            hashtags_found = re.findall(r"#(\w+)", content, re.IGNORECASE)
            post_data['hashtags_list'] = sorted(list(set([tag.lower() for tag in hashtags_found])))
        else:
            post_data['hashtags_list'] = []

        post_data['has_links'] = 'http' in content or 'https://' in content
        post_data['has_questions'] = '?' in content
        post_data['has_mentions'] = '@' in content
        post_data['theme'] = None

        print(f"  Successfully processed post: {post_url[:60]}... (Date: {post_data['date']}, Time: {post_data['time']}, Likes: {post_data['likes']}, Comments: {post_data['comments']}, Hashtags: {len(post_data.get('hashtags_list', []))})")
        return post_data

    except TimeoutException:
        print(f"  ERROR: Timeout scraping post page: {post_url[:60]}...")
        return None
    except WebDriverException as e:
         print(f"  ERROR: WebDriverException scraping post {post_url[:60]}...: {e}")
         return None
    except Exception as e:
        print(f"  ERROR: Unexpected error scraping post {post_url[:60]}...: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as quit_error:
                print(f"  Warning: Error quitting driver for {post_url[:60]}: {quit_error}")

def scrape_profile_and_posts(profile_url, max_workers=5, max_posts_to_scrape=20, **kwargs):
    """
    Orchestrates scraping profile info, getting post links, and scraping posts concurrently.
    (No changes needed here from previous version)
    """
    print(f"Starting scrape for profile: {profile_url}")

    # Step 1: Scrape main profile page
    print("Fetching main profile page...")
    options = Options()
    options.add_argument("--headless") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,800")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")

    service = Service(ChromeDriverManager().install())
    driver = None
    profile_info = None
    post_urls = []

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(8)
        wait = WebDriverWait(driver, 20)
        driver.get(profile_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.top-card-layout__title, section.profile h1")))
        time.sleep(random.uniform(2, 4))
        html_content = driver.page_source
        profile_info, post_urls = scrape_linkedin_profile_for_links(html_content, profile_url)
    except Exception as e:
        print(f"Error fetching main profile page {profile_url}: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as quit_error:
                 print(f"  Warning: Error quitting main profile driver for {profile_url}: {quit_error}")


    if not profile_info or not post_urls:
        print(f"Could not retrieve profile info or post URLs for {profile_url}. Aborting detailed post scrape.")
        return profile_info, []

    urls_to_scrape = post_urls[:max_posts_to_scrape]
    print(f"Found {len(post_urls)} post URLs. Will scrape details for {len(urls_to_scrape)}.")

    # Step 2: Scrape individual post pages concurrently
    detailed_post_data = []
    actual_workers = min(max_workers, len(urls_to_scrape))
    if actual_workers <= 0:
         print("No posts to scrape details for.")
         return profile_info, []

    print(f"Starting concurrent scrape for {len(urls_to_scrape)} posts using {actual_workers} workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=actual_workers) as executor:
        future_to_url = {executor.submit(scrape_single_post_page, url): url for url in urls_to_scrape}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    result['profile_url'] = profile_url
                    result['profile_name'] = profile_info.get('name', 'N/A')
                    detailed_post_data.append(result)
                else:
                    print(f"  Skipping result for post (likely failed): {url[:60]}...")
            except Exception as exc:
                print(f'  Post {url[:60]}... generated an exception during result processing: {exc}')

    print(f"Finished scraping details for {len(detailed_post_data)} posts.")
    return profile_info, detailed_post_data


def scrape_single_profile_and_posts(profile_url, max_posts_to_scrape=15):
    all_posts_data = []
    profile_summary = {}

    print(f"\n--- Scraping Profile & Posts: {profile_url} ---")
    try:
        profile_info, posts = scrape_profile_and_posts(profile_url, max_posts_to_scrape=max_posts_to_scrape)

        if profile_info:
            profile_name = profile_info.get('name', 'N/A')
            posts_found = len(posts)
            print(f"✅ Scraped profile: {profile_name} ({posts_found} posts)")

            profile_summary = {
                'profile_url': profile_url,
                'name': profile_name,
                'headline': profile_info.get('headline'),
                'location': profile_info.get('location'),
                'connections': profile_info.get('connections_count'),
                'followers': profile_info.get('followers_count'),
                'posts_scraped': posts_found,
                'avg_engagement': (sum(p.get('engagement', 0) for p in posts) / posts_found) if posts_found > 0 else 0
            }

            if posts:
                for post in posts:
                    post['profile_url'] = profile_url  # Add profile_url to each post

                all_posts_data.extend(posts)
        else:
            print(f"❌ Failed to scrape profile info for: {profile_url}")
            profile_summary = {'url': profile_url, 'name': 'SCRAPE FAILED', 'posts_scraped': 0}

    except Exception as e:
        print(f"🔥 CRITICAL ERROR processing profile {profile_url}: {str(e)}")
        profile_summary = {'url': profile_url, 'name': 'CRITICAL ERROR', 'posts_scraped': 0}

    print("\n--- Scraping Summary ---")
    print(profile_summary)
    print("-------------------------\n")

    if all_posts_data:
        cols_order = [
            'profile_url', 'profile_name', 'date', 'time', 'content', 'type', 'content_length', 'content_length_type',
            'likes', 'comments', 'shares', 'engagement', 'has_hashtags', 'hashtags_list',
            'has_links', 'has_questions', 'has_mentions', 'post_url'
        ]
        posts_df = pd.DataFrame(all_posts_data)
        posts_df = posts_df.reindex(columns=cols_order)
        print(f"✅ Returning DataFrame with {len(posts_df)} detailed posts.\n")
        return posts_df, profile_summary
    else:
        print("⚠️ No post data collected.\n")
        return pd.DataFrame(), profile_summary

def save_to_mongodb(posts_dataframe, profile_summary, db_name='linkedin_data', posts_collection='posts', profiles_collection='profiles'):
    load_dotenv()
    connection_string = os.getenv("MONGO_URI")
    client = MongoClient(connection_string)
    db = client[db_name]

    # Save profile info to Profiles collection
    profile_collection = db[profiles_collection]
    try:
        profile_collection.update_one(
            {'profile_url': profile_summary['profile_url']},
            {'$set': profile_summary},
            upsert=True  # Insert if not exists, or update if exists
        )
        print(f"✅ Profile info saved to MongoDB (Profiles collection).")
    except Exception as e:
        print(f"❌ Error saving profile info to MongoDB: {e}")

    # Save post data to Posts collection
    post_collection = db[posts_collection]
    records = posts_dataframe.to_dict(orient='records')
    operations = []

    for record in records:
        if 'post_url' not in record:
            continue
        operations.append(
            UpdateOne(
                {'post_url': record['post_url']},  # match condition
                {'$set': record},                  # update with full new record
                upsert=True                        # insert if not found
            )
        )

    try:
        if operations:
            result = post_collection.bulk_write(operations)
            print(f"✅ MongoDB upsert complete: {result.bulk_api_result}")
    except Exception as e:
        print(f"❌ Error during MongoDB upsert: {e}")

def main(profile_url):
    posts_df, profile_summary = scrape_single_profile_and_posts(profile_url)

    if not posts_df.empty:
        print("\n--- Final Scraped Data Preview ---")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(posts_df.head())
        print(f"\nDataFrame shape: {posts_df.shape}")
        print("\nColumns:", posts_df.columns.tolist())

        save_to_mongodb(posts_df, profile_summary)

    else:
        print("❌ No detailed post data was scraped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape a single LinkedIn profile and its posts")
    parser.add_argument('url', type=str, help="LinkedIn profile URL to scrape")
    args = parser.parse_args()
    main(args.url)
