import sys
import re
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url):
    # Regular expression to extract video ID from URL
    match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL")

def extract_metadata(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, features="html.parser")

    link_title = soup.find_all(name="title")[0]
    title = str(link_title)
    title = title.replace("<title>","")
    title = title.replace("</title>","")

    link_channel = soup.find("link", itemprop="name")
    channel = str(link_channel)

    # Parse the HTML
    soup = BeautifulSoup(channel, 'html.parser')

    # Find the link tag with itemprop="name"
    link_tag = soup.find('link', itemprop='name')

    # Extract the content attribute
    channel = link_tag['content'] if link_tag else None
    
    return title, channel
        
def download_thumbnail(video_id):
    image_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    img_data = requests.get(image_url).content
    with open('thumbnail.jpg', 'wb') as handler:
        handler.write(img_data)     
        
def get_transcript(video_id, include_timestamps=False): 
    from youtube_transcript_api import YouTubeTranscriptApi
    fetched = YouTubeTranscriptApi().fetch(video_id)
    if include_timestamps:
        # Format as [M:SS] text for each segment
        lines = []
        for s in fetched:
            minutes = int(s.start // 60)
            seconds = int(s.start % 60)
            timestamp = f"[{minutes}:{seconds:02d}]"
            lines.append(f"{timestamp} {s.text}")
        return ' '.join(lines)
    else:
        transcript_str_lst = [s.text for s in fetched]
        return ' '.join(transcript_str_lst)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <youtube_url>") # QUOTATION MARKS AROUND URL NEEDED WHEN RUNNING ON TERMINAL
        sys.exit(1)
    
    youtube_url = sys.argv[1]
    video_id = extract_video_id(youtube_url)
    title, channel = extract_metadata(youtube_url)
    transcript = get_transcript(video_id)
    download_thumbnail(video_id)
    print(f"Title: {title}")
    print(f"Channel: {channel}")
    print('=============')
    print(transcript)
