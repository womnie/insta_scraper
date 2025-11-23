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
        # Removed invalid 'api_version' argument
    )

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
                sleeptime = random.randint(5, 12)
                time.sleep(sleeptime) 
                
            except Exception as p_err:
                print(f"   ⚠️ Skipped post: {p_err}")
                continue
    except Exception as e:
        print(f"⚠️ Error during iteration: {e}")
        raise e

    return data_rows

def main_scraper(target_profile, amount):
    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    print(f"🔄 Setting up Anonymous Profile Scraper...")
    L = get_instaloader_instance(agent)
    
    print(f"🚀 Attempting Anonymous Scrape of Profile: @{target_profile}...")
    
    try:
        posts = instaloader.Profile.from_username(L.context, target_profile).get_posts()
        
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
        print(f"❌ Scrape failed: {e}")
        if "401" in str(e):
             print("💡 Tip: 401 means Instagram blocked the request. Try waiting a few hours.")
        sys.exit(1)

if __name__ == "__main__":
    t_profile = os.environ.get("INPUT_PROFILE", "kaelakovalskia") 
    t_amount = int(os.environ.get("INPUT_AMOUNT", 5))

    main_scraper(t_profile, t_amount)