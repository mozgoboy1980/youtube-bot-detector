import os
import requests
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
from io import StringIO
import csv

app = Flask(__name__)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

def get_video_id_from_url(url):
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

def get_comments(video_id, published_after):
    comments = []
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": YOUTUBE_API_KEY,
        "maxResults": 100,
        "textFormat": "plainText"
    }

     total = 0
while True:
    response = requests.get(url, params=params)
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
    if request.method == "POST":
        video_url = request.form["video_url"]
        period = request.form["period"]

        days_map = {
            "week": 7,
            "month": 30,
            "halfyear": 180
        }
        days = days_map.get(period, 30)
        published_after = datetime.utcnow() - timedelta(days=days)

        video_id = get_video_id_from_url(video_url)
        if video_id:
            comments = get_comments(video_id, published_after)

    return render_template("index.html", comments=comments)

@app.route("/export", methods=["POST"])
def export_csv():
    comments = request.json.get("comments", [])
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["author", "text", "date", "videoId"])
    writer.writeheader()
    for row in comments:
        writer.writerow(row)

    output.seek(0)
    return output.read(), 200, {
        "Content-Disposition": "attachment; filename=comments.csv",
        "Content-Type": "text/csv"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
