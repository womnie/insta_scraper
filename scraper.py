import csv
import datetime
import os
import sys
import time
import random

# Try to import instaloader
try:
    import instaloader
except ImportError:
    print("❌ Error: 'instaloader' library is not installed.")
    sys.exit(1)

def get_instaloader_instance(user_agent):
    # Standard User Agent (Desktop)
    return instaloader.Instaloader(
        sleep=True,
        user_agent=user_agent,
        request_timeout=60,
        max_connection_attempts=3
       
    )

# --- ADAPTED BACKOFF LOGIC ---
def get_profile_with_backoff(L, username, max_retries=5):
    """
    Adapts the exponential backoff logic from the user snippet.
    Instead of 'requests.get', we wrap the Instaloader profile fetch.
    """
    retries = 0
    backoff = 60  # Start with 1 minute, as per snippet

    while retries < max_retries:
        try:
            print(f"🔍 Fetching profile metadata for @{username} (Attempt {retries+1}/{max_retries})...")
            # This is the Instaloader equivalent of the request in the snippet
            profile = instaloader.Profile.from_username(L.context, username)
            return profile
            
        except Exception as e:
            # Check for 401 Unauthorized (which Instaloader wraps in generic exceptions sometimes)
            error_msg = str(e)
            if "401" in error_msg or "login_required" in error_msg or "ConnectionException" in error_msg:
                print(f"⚠️ Received 401/Connection Error; sleeping {backoff}s before retrying...")
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff (60 -> 120 -> 240...)
                retries += 1
            else:
                # If it's a "Profile Not Found" or other fatal error, raise immediately
                raise e
                
    raise Exception(f"❌ Exceeded maximum retries ({max_retries}) due to 401 Unauthorized.")


def save_to_csv(data_rows, prefix="scrape"):
    if not data_rows:
        print("⚠️ No data to save.")
        return

    # Define the output directory
    output_dir = os.path.join("data", "raw")
    
    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Combine directory and filename
    filename = os.path.join(output_dir, f"{prefix}_{current_time}.csv")
    
    headers = ["Media ID", "URL Code", "Link", "User", "Likes", "Comments", "Date", "Caption"]
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data_rows)
    print(f"📁 Saved to {filename}")

def perform_scrape(L, iterator, amount, label):
    data_rows = []
    count = 0

    #adding loop backoff time for 401 handling
    loop_backoff = 60  # 1 minute/s
    
    print(f"⬇️  Downloading {amount} posts from {label}...")

    try:
        for post in iterator:
            if count >= amount:
                break
            
            print(f"   [{count+1}/{amount}] Post {post.shortcode}...")
            
            try:
                row = {
                    "Media ID": post.mediaid,
                    "URL Code": post.shortcode,
                    "Link": f"https://www.instagram.com/p/{post.shortcode}/",
                    "User": post.owner_username,
                    "Likes": post.likes,
                    "Comments": post.comments,
                    "Date": post.date_local.strftime('%Y-%m-%d %H:%M:%S'),
                    "Caption": (post.caption or "").replace('\n', ' ').strip()
                }
                data_rows.append(row)
                count += 1
                
                # Random sleep
                sleeptime = random.randint(15, 30)
                time.sleep(sleeptime) 
                
                if count % 10 == 0:
                    print("      ☕ Taking a 60s break...") # avoiding 401 errors
                    time.sleep(60)

            except Exception as p_err:
                print(f"   ⚠️ Skipped post: {p_err}")
                continue

    except Exception as e:
        print(f"⚠️ Error during iteration: {e}")

        # If the loop crashes with 401, apply the backoff logic BEFORE exiting.
        if "401" in str(e) or "429" in str(e):
            print(f"🛑 Rate limit hit (401). Executing backoff sleep of {loop_backoff}s before saving...")
            time.sleep(loop_backoff)
            print("💾 Saving collected data now...")
            return data_rows
        raise e

    return data_rows

def main_scraper(target_profile, amount):
    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    print(f"🔄 Setting up Anonymous Profile Scraper...")
    L = get_instaloader_instance(agent)
    
    print(f"🚀 Attempting Anonymous Scrape of Profile: @{target_profile}...")
    
    try:
        # UPDATED: Use the new backoff-enabled profile fetcher
        profile = get_profile_with_backoff(L, target_profile)

        # If we get here, the profile metadata was fetched successfully
        posts = profile.get_posts()
        # Alternative direct method (without backoff) - commented out
        # posts = instaloader.Profile.from_username(L.context, target_profile).get_posts()
        
        data = perform_scrape(L, posts, amount, f"Profile @{target_profile}")
        
        if data:
            save_to_csv(data, f"profile_{target_profile}")
            print("🎉 Success!")
        else:
            print("⚠️ No posts found. The profile might be empty.")
            
    except instaloader.ProfileNotExistsException:
        print(f"❌ Error: Profile @{target_profile} does not exist.")
    except instaloader.LoginRequiredException:
        print(f"❌ Error: Profile @{target_profile} is Private. Anonymous scraping only works on Public profiles.")
    except Exception as e:
        print(f"❌ Scrape failed after retries: {e}")
        if "401" in str(e):
             print("💡 Tip: 401 means Instagram blocked the request. Try waiting a few hours.")
        sys.exit(1)

if __name__ == "__main__":
    t_profile = os.environ.get("INPUT_PROFILE", "instagram") 
    t_amount = int(os.environ.get("INPUT_AMOUNT", 5))

    main_scraper(t_profile, t_amount)