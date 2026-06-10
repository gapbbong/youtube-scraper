from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI(title="YouTube Channel Scraper")

# Define request model
class ScrapeRequest(BaseModel):
    url: str

def format_duration(seconds):
    if seconds is None:
        return "N/A"
    try:
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        else:
            return f"{m}:{s:02d}"
    except Exception:
        return "N/A"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    template_path = os.path.join("templates", "index.html")
    if not os.path.exists(template_path):
        return HTMLResponse("<h1>Templates folder or index.html missing</h1>", status_code=404)
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/api/scrape")
async def scrape_channel(request: ScrapeRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    # Basic validation for YouTube URL
    if "youtube.com" not in url and "youtu.be" not in url:
        raise HTTPException(status_code=400, detail="Please enter a valid YouTube URL (e.g. youtube.com/@channel)")
    
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise HTTPException(status_code=404, detail="No information could be retrieved from this URL")
            
            # Channel title
            channel_name = info.get('title', 'Unknown Channel')
            channel_url = info.get('webpage_url', url)
            
            videos = []
            entries = info.get('entries', [])
            
            # If the URL is a direct video rather than a channel/playlist
            if not entries and (info.get('webpage_url_basename') == 'watch' or info.get('_type') == 'video'):
                entries = [info]
            
            for idx, entry in enumerate(entries, 1):
                video_id = entry.get('id')
                if not video_id:
                    continue
                
                # Title
                title = entry.get('title') or "Untitled Video"
                
                # Video URL
                video_url = entry.get('url')
                if not video_url or not video_url.startswith('http'):
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                # Duration
                duration_sec = entry.get('duration')
                duration_str = format_duration(duration_sec)
                
                # Thumbnail
                thumbnail = entry.get('thumbnail')
                if not thumbnail:
                    # Fallback thumbnail
                    thumbnail = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
                
                videos.append({
                    "index": idx,
                    "id": video_id,
                    "title": title,
                    "url": video_url,
                    "duration_seconds": duration_sec,
                    "duration_string": duration_str,
                    "thumbnail": thumbnail,
                    "view_count": entry.get('view_count'),
                    "uploader": entry.get('uploader') or channel_name
                })
                
            return {
                "success": True,
                "channel_name": channel_name,
                "channel_url": channel_url,
                "total_count": len(videos),
                "videos": videos
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping channel: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
