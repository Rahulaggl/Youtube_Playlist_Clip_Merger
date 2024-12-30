import streamlit as st
import re
import os
import moviepy.editor as mp
import yt_dlp as ytdlp
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import dotenv

dotenv.load_dotenv()

# Helper functions
def extract_youtube_video_id(url: str) -> str:
    found = re.search(r"(?:youtu\.be\/|watch\?v=)([\w-]+)", url)
    return found.group(1) if found else None

def get_video_transcript(video_id: str) -> list | None:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        return transcript
    except TranscriptsDisabled:
        return None
    except Exception:
        return None

def get_playlist_video_ids(playlist_url: str) -> list:
    match = re.search(r"playlist\?list=([a-zAZ0-9_-]+)", playlist_url)
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
        return []  # Return an empty list if the playlist ID is not found

def get_group_video_ids(group_url: str) -> list:
    match = re.search(r"channel\/([a-zA-Z0-9_-]+)", group_url)
    if match:
        channel_id = match.group(1)
        youtube = build('youtube', 'v3', developerKey=os.getenv('YOUTUBE_API_KEY'))
        video_ids = []
        next_page_token = None
        while True:
            request = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            video_ids.extend([item['id']['videoId'] for item in response['items'] if item['id']['kind'] == 'youtube#video'])
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        return video_ids
    else:
        return []  # Return an empty list if the channel ID is not found

def download_video(video_id: str) -> str:
    url = f'https://www.youtube.com/watch?v={video_id}'
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': f'temp_video_{video_id}.mp4',
        'noplaylist': True,
        'quiet': True,
        'retries': 3,  # Number of retries
        'socket_timeout': 30,  # Increase timeout in seconds
    }
    
    with ytdlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Check video size before downloading
            info_dict = ydl.extract_info(url, download=False)
            video_size = info_dict.get('filesize', None)
            if video_size and video_size > 500000000:  # Skip videos larger than 500MB
                return None
            
            # Proceed with downloading if video is not too large
            ydl.download([url])
            return f'temp_video_{video_id}.mp4'
        except ytdlp.utils.DownloadError as e:
            st.warning(f"Failed to download video {video_id} due to: {str(e)}")
            return None

def merge_video_segments(segment_paths: list, output_path: str) -> str:
    video_clips = [mp.VideoFileClip(segment) for segment in segment_paths]
    
    final_clip = mp.concatenate_videoclips(video_clips)
    final_clip.write_videofile(output_path, codec='libx264')
    return output_path

# Streamlit UI and Logic
st.title('YouTube Playlist Video Cutter and Merger')
st.write("### Instructions:")
st.markdown("1. Paste your YouTube playlist or group URL below.\n2. The app will fetch videos and merge them into one video.")
url = st.text_input('Enter YouTube Playlist or Group URL')
submit = st.button('Submit')

if submit and url:
    video_ids = []
    if "playlist?list=" in url:
        video_ids = get_playlist_video_ids(url)
    elif "channel/" in url:
        video_ids = get_group_video_ids(url)
    else:
        st.error("Invalid URL. Please provide a valid YouTube playlist or group URL.")
    
    if video_ids:
        st.write("Fetching video segments...")
        segment_paths = []
        skipped_videos = []  # To track skipped videos
        for video_id in video_ids:
            # Simply download the full video
            video_path = download_video(video_id)
            if video_path is None:
                skipped_videos.append(video_id)
                continue
            
            segment_paths.append(video_path)
            
        if segment_paths:
            output_path = "final_output_video.mp4"
            merged_video_path = merge_video_segments(segment_paths, output_path)
            st.write("Video processing complete!")
            st.video(merged_video_path)
            
            if skipped_videos:
                st.write("Skipped videos (too large or failed to download):")
                st.write(", ".join(skipped_videos))
        else:
            st.warning("No videos processed. Please check the playlist/group for valid videos.")
    else:
        st.warning("No videos found in the provided URL.")
