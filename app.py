import os
import requests
from flask import Flask, request, render_template
from datetime import datetime, timedelta

app = Flask(__name__)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

def get_comments_from_video(video_id, published_after):
    comments = []
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": YOUTUBE_API_KEY,
        "maxResults": 100,
        "textFormat": "plainText"
    }
    while True:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            break
        data = response.json()
        for item in data.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comment_time = comment["publishedAt"]
            comment_datetime = datetime.strptime(comment_time, "%Y-%m-%dT%H:%M:%SZ")
            if comment_datetime >= published_after:
                comments.append({
                    "author": comment["authorDisplayName"],
                    "text": comment["textDisplay"],
                    "date": comment_datetime.strftime("%Y-%m-%d %H:%M"),
                    "videoId": video_id
                })
        if "nextPageToken" in data:
            params["pageToken"] = data["nextPageToken"]
        else:
            break
    return comments

@app.route("/", methods=["GET", "POST"])
def index():
    comments = []
    error = None
    if request.method == "POST":
        link = request.form["video_url"]  # ✅ исправлено: 'video_url' вместо 'link'
        period = request.form["period"]
        if "v=" in link:
            video_id = link.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in link:
            video_id = link.split("youtu.be/")[-1].split("?")[0]
        else:
            error = "Неверная ссылка на видео"
            return render_template("index.html", error=error)

        days_ago = {
            "day": 1,
            "week": 7,
            "month": 30
        }.get(period, 30)
        published_after = datetime.utcnow() - timedelta(days=days_ago)
        comments = get_comments_from_video(video_id, published_after)
    return render_template("index.html", comments=comments, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
