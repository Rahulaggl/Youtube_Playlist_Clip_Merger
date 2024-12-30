import streamlit as st
import re
import os
import moviepy.editor as mp
import yt_dlp as ytdlp
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import dotenv
import random

# Load environment variables
dotenv.load_dotenv()

# Helper function to clean up existing MP4 files
def clean_up_existing_mp4():
    for file in os.listdir('.'):
        if file.endswith('.mp4'):
            os.remove(file)
            print(f"Deleted file: {file}")

# Call cleanup function
clean_up_existing_mp4()

# Extract YouTube video ID from URL
def extract_youtube_video_id(url: str) -> str:
    found = re.search(r"(?:youtu\.be\/|watch\?v=)([\w-]+)", url)
    return found.group(1) if found else None

# Get transcript for a video
def get_video_transcript(video_id: str):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        return transcript
    except TranscriptsDisabled:
        return None
    except Exception as e:
        st.warning(f"Transcript error for video {video_id}: {e}")
        return None

# Fetch video IDs from a playlist
def get_playlist_video_ids(playlist_url: str):
    match = re.search(r"playlist\?list=([a-zA-Z0-9_-]+)", playlist_url)
    if match:
        playlist_id = match.group(1)
        youtube = build('youtube', 'v3', developerKey=os.getenv('YOUTUBE_API_KEY'))
        video_ids = []
        next_page_token = None
        while True:
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            video_ids.extend([item['snippet']['resourceId']['videoId'] for item in response['items']])
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        return video_ids
    else:
        return []

# Download a YouTube video
def download_video(video_id: str):
    url = f'https://www.youtube.com/watch?v={video_id}'
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': f'temp_video_{video_id}.mp4',
        'noplaylist': True,
        'quiet': True,
        'retries': 3,
        'socket_timeout': 30,
    }

    with ytdlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            video_size = info_dict.get('filesize', None)
            if video_size and video_size > 500_000_000:  # Skip videos larger than 500MB
                st.warning(f"Video {video_id} is too large to process.")
                return None
            ydl.download([url])
            return f'temp_video_{video_id}.mp4'
        except ytdlp.utils.DownloadError as e:
            st.warning(f"Failed to download video {video_id}: {e}")
            return None

# Extract a random segment from a video
def extract_random_segment(video_path: str, duration: int = 5):
    video_clip = None
    try:
        video_clip = mp.VideoFileClip(video_path)
        if video_clip.duration < duration:
            segment = video_clip
        else:
            start_time = random.uniform(0, video_clip.duration - duration)
            segment = video_clip.subclip(start_time, start_time + duration)
        segment_path = f"segment_{os.path.basename(video_path)}"
        segment.write_videofile(segment_path, codec='libx264', audio_codec='aac', logger=None)
        return segment_path
    finally:
        if video_clip:
            video_clip.close()

# Merge multiple video segments
def merge_video_segments(segment_paths: list, output_path: str):
    video_clips = []
    try:
        video_clips = [mp.VideoFileClip(segment) for segment in segment_paths]
        final_clip = mp.concatenate_videoclips(video_clips)
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        return output_path
    finally:
        for clip in video_clips:
            clip.close()
        for segment in segment_paths:
            if os.path.exists(segment):
                os.remove(segment)

# Streamlit UI
st.title('YouTube Playlist Video Clip Recap Maker')
st.write("### Instructions:")
st.markdown("1. Paste your YouTube playlist URL below.\n2. The app will fetch video segments and merge them into one video.")

st.warning(
    "**NOTE**: 1. Unsupported YouTube playlists containing YouTube Shorts videos cannot be merged because of significant aspect ratio differences.\n2. Recommended to use playlists containing up to 60 videos."
)

url = st.text_input('Enter YouTube Playlist URL')
submit = st.button('Submit')

if submit and url:
    video_ids = get_playlist_video_ids(url)

    if video_ids:
        st.write("Fetching video segments...")
        segment_paths = []
        skipped_videos = []

        for video_id in video_ids:
            video_path = download_video(video_id)
            if video_path is None:
                skipped_videos.append(video_id)
                continue

            try:
                transcript = get_video_transcript(video_id)
                if not transcript:
                    st.write(f"No transcript found for video {video_id}. Extracting random frame.")
                segment_path = extract_random_segment(video_path, duration=5)
                segment_paths.append(segment_path)
            finally:
                if os.path.exists(video_path):
                    os.remove(video_path)

        if segment_paths:
            output_path = "final_output_video.mp4"
            merged_video_path = merge_video_segments(segment_paths, output_path)
            st.write("Video processing complete!")
            st.video(merged_video_path)
            if skipped_videos:
                st.write("Skipped videos (too large or failed to download):")
                st.write(", ".join(skipped_videos))
        else:
            st.warning("No valid video segments were processed.")
    else:
        st.warning("No videos found in the playlist URL.")
