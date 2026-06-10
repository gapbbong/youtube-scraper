from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
import io
import urllib.parse
import json
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
            
            # Channel title - prefer channel/uploader over playlist title
            channel_name = (
                info.get('channel')
                or info.get('uploader')
                or info.get('title')
                or 'Unknown Channel'
            )
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

@app.post("/api/export-csv")
async def export_csv(videos: str = Form(...), channel_name: str = Form(...)):
    try:
        video_list = json.loads(videos)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid videos data")
        
    output = io.StringIO()
    output.write("\uFEFF") # UTF-8 BOM
    output.write("채널명,영상 링크,재생시간\n")
    
    for v in video_list:
        escaped_channel = channel_name.replace('"', '""')
        video_url = v.get('url', '')
        duration = v.get('duration_string', 'N/A')
        output.write(f"\"{escaped_channel}\",\"{video_url}\",\"{duration}\"\n")
        
    csv_data = output.getvalue()
    output.close()
    
    safe_channel_name = "".join(c for c in channel_name if c not in '\\/:*?"<>|')
    filename = f"{safe_channel_name} 영상 링크와 재생시간.csv"
    encoded_filename = urllib.parse.quote(filename)
    
    headers = {
        'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    }
    
    return StreamingResponse(
        io.BytesIO(csv_data.encode('utf-8')),
        media_type='text/csv;charset=utf-8',
        headers=headers
    )

@app.post("/api/export-json")
async def export_json(videos: str = Form(...), channel_name: str = Form(...)):
    try:
        video_list = json.loads(videos)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid videos data")
        
    json_data = json.dumps(video_list, indent=2, ensure_ascii=False)
    
    safe_channel_name = "".join(c for c in channel_name if c not in '\\/:*?"<>|')
    filename = f"{safe_channel_name} 영상 링크와 재생시간.json"
    encoded_filename = urllib.parse.quote(filename)
    
    headers = {
        'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    }
    
    return StreamingResponse(
        io.BytesIO(json_data.encode('utf-8')),
        media_type='application/json;charset=utf-8',
        headers=headers
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
