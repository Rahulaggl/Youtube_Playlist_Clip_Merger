import streamlit as st
import re
import os
import moviepy.editor as mp
import yt_dlp as ytdlp
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import dotenv
import random

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
    match = re.search(r"playlist\?list=([a-zA-Z0-9_-]+)", playlist_url)
    if match:
        playlist_id = match.group(1)
        youtube = build('youtube', 'v3', developerKey=st.secrets['YOUTUBE_API_KEY'])
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

def download_video(video_id: str) -> str | None:
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
                return None
            ydl.download([url])
            video_path = f'temp_video_{video_id}.mp4'

            # Check the aspect ratio of the downloaded video
            video_clip = mp.VideoFileClip(video_path)
            width, height = video_clip.size
            video_clip.close()

            # Skip YouTube Shorts (9:16 aspect ratio)
            if height > width:  # If height is greater than width, it's likely a 9:16 video
                os.remove(video_path)  # Delete the Shorts video
                return None
            return video_path
        except ytdlp.utils.DownloadError as e:
            st.warning(f"Failed to download video {video_id}: {e}")
            return None

def extract_random_segment(video_path: str, duration: int = 5) -> str:
    video_clip = None
    try:
        video_clip = mp.VideoFileClip(video_path)
        if video_clip.duration < duration:
            segment = video_clip  # Use the entire video if shorter than the desired segment
        else:
            start_time = random.uniform(0, video_clip.duration - duration)
            segment = video_clip.subclip(start_time, start_time + duration)
        segment_path = f"segment_{os.path.basename(video_path)}"
        segment.write_videofile(segment_path, codec='libx264', audio_codec='aac', logger=None)
        return segment_path
    finally:
        if video_clip:
            video_clip.close()  # Explicitly close the video clip

def merge_video_segments(segment_paths: list, output_path: str) -> str:
    video_clips = []
    try:
        # Validate each segment file before loading it
        for segment in segment_paths:
            if os.path.exists(segment) and segment.endswith('.mp4'):
                try:
                    video_clips.append(mp.VideoFileClip(segment))
                except IOError as e:
                    st.warning(f"Error loading video segment {segment}: {e}")
            else:
                st.warning(f"Invalid or missing video file: {segment}")
        
        if video_clips:
            final_clip = mp.concatenate_videoclips(video_clips)
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            return output_path
        else:
            st.warning("No valid video clips to merge.")
            return None
    except Exception as e:
        st.warning(f"Error merging video segments: {e}")
        return None
    finally:
        # Ensure all clips are closed after processing
        for clip in video_clips:
            clip.close()  # Close the video clips to free up memory
        for segment in segment_paths:
            if os.path.exists(segment):
                os.remove(segment)  # Clean up temporary segment files

# Clean up old video files
for file in os.listdir():
    if file.endswith('.mp4'):
        try:
            os.remove(file)  # Deleting old MP4 files to free up space
        except Exception as e:
            st.warning(f"Error removing file {file}: {e}")

# Streamlit UI and Logic
st.title('YouTube Playlist Video Clip Recap Maker')

# Adding the user guide link as a clickable URL
st.markdown("### User Guide:")
st.markdown(f"You can use sample YT playlist Link below:\n\nhttps://www.youtube.com/playlist?list=PLhiP3P44ul3Y8LDbhXJmhVsVWcpe-7O4O")

st.write("### Instructions:")
st.markdown("1. Paste your YouTube playlist URL below.\n2. The app will fetch video segments and merge them into one video.")

# Add warning for unsupported videos
st.warning(
    "**NOTE** :- Ignore the warning messages and scroll down for the result (warning messages due to the inability to access a few videos because of YouTube guidelines). "
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
                segment_path = extract_random_segment(video_path, duration=5)
                segment_paths.append(segment_path)
            finally:
                if os.path.exists(video_path):
                    os.remove(video_path)  # Clean up the downloaded video file
        
        if segment_paths:
            output_path = "final_output_video.mp4"
            merged_video_path = merge_video_segments(segment_paths, output_path)
            st.write("Video processing complete!")
            st.video(merged_video_path)
            if skipped_videos:
                st.write("Skipped videos (too large, 9:16 aspect ratio, or failed to download):")
                st.write(", ".join(skipped_videos))
        else:
            st.warning("No valid segments were processed.")
    else:
        st.warning("No videos found in the playlist URL.")
