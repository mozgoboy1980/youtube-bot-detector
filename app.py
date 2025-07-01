from flask import Flask, render_template, request, send_file
import yt_dlp
import pandas as pd
from datetime import datetime, timedelta
from youtube_comment_downloader import YoutubeCommentDownloader

app = Flask(__name__)

def get_video_list(channel_url, days):
    date_after = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "skip_download": True,
        "force_generic_extractor": True,
        "dateafter": date_after,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"{channel_url}/videos", download=False)
        entries = info.get("entries", [])
    return [f"https://www.youtube.com/watch?v={e['id']}" for e in entries if 'id' in e]

def download_comments(video_url):
    downloader = YoutubeCommentDownloader()
    try:
        comments = downloader.get_comments_from_url(video_url)
        data = []
        for c in comments:
            data.append({
                "video_url": video_url,
                "author": c.get("author"),
                "text": c.get("text"),
                "time": c.get("time"),
                "likes": c.get("votes")
            })
        return data
    except Exception:
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["channel_url"]
        period = request.form["period"]
        days_map = {"week": 7, "month": 30, "halfyear": 180}
        days = days_map.get(period, 30)

        videos = get_video_list(url, days)
        all_comments = []
        for v in videos:
            all_comments.extend(download_comments(v))

        df = pd.DataFrame(all_comments)
        df = df.head(100)
        table_html = df.to_html(classes='table table-striped', index=False)
        return render_template("index.html", table=table_html)
    return render_template("index.html", table=None)

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=10000)
