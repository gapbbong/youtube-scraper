import sys
import os
import json
import csv
import yt_dlp

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

def scrape_to_files(url):
    print(f"[정보] 유튜브 스크래핑 시작: {url}")
    print("[정보] 데이터를 수집하고 있습니다. 채널 크기에 따라 시간이 걸릴 수 있습니다...")

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
                print("[오류] URL에서 정보를 가져올 수 없습니다.")
                return

            channel_name = (
                info.get('channel')
                or info.get('uploader')
                or info.get('title')
                or 'Unknown_Channel'
            )
            
            # Remove unsafe characters for file names
            safe_channel_name = "".join(c for c in channel_name if c not in '\\/:*?"<>|').strip()
            
            entries = info.get('entries', [])
            if not entries and (info.get('webpage_url_basename') == 'watch' or info.get('_type') == 'video'):
                entries = [info]

            videos = []
            for idx, entry in enumerate(entries, 1):
                video_id = entry.get('id')
                if not video_id:
                    continue
                
                title = entry.get('title') or "Untitled Video"
                
                video_url = entry.get('url')
                if not video_url or not video_url.startswith('http'):
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                duration_sec = entry.get('duration')
                duration_str = format_duration(duration_sec)
                
                videos.append({
                    "번호": idx,
                    "제목": title,
                    "링크": video_url,
                    "재생시간": duration_str
                })

            if not videos:
                print("[경고] 수집된 동영상이 없습니다.")
                return

            # Save CSV
            csv_filename = f"{safe_channel_name} 영상 링크와 재생시간.csv"
            with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["채널명", "영상 링크", "재생시간"])
                for v in videos:
                    writer.writerow([channel_name, v["링크"], v["재생시간"]])
            
            # Save JSON
            json_filename = f"{safe_channel_name} 영상 링크와 재생시간.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(videos, f, indent=2, ensure_ascii=False)

            print("=" * 50)
            print(f"[성공] 총 {len(videos)}개의 영상을 추출했습니다.")
            print(f"[저장] CSV 파일: {os.path.abspath(csv_filename)}")
            print(f"[저장] JSON 파일: {os.path.abspath(json_filename)}")
            print("=" * 50)

    except Exception as e:
        print(f"[오류] 스크래핑 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python cli.py <유튜브_채널_또는_재생목록_URL>")
        print("예시: python cli.py https://www.youtube.com/@mental_TC/videos")
        
        # Interactive mode fallback
        url = input("\n스크래핑할 유튜브 URL을 입력하세요: ").strip()
        if url:
            scrape_to_files(url)
        else:
            print("[종료] URL이 입력되지 않았습니다.")
    else:
        scrape_to_files(sys.argv[1])
