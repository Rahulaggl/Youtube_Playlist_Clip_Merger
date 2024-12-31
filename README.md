### **YouTube Playlist Video Clip Recap Maker**

**Access the Project:**

1. **Offline Access**:  
   To run the project locally, follow the setup instructions below.
   
2. **Online Access**:  
   You can access the project online via the following [link](https://youtubeplaylistclipmerger-ipszpkcedglkhzrkfnhrvb.streamlit.app/).

## Demo Video

Here is the demo video: [link](https://youtu.be/REU3zSqUGLs).

---

This repository implements a **YouTube Playlist Video Clip Recap Maker** that allows users to create concise video summaries from a YouTube playlist. The system extracts key clips from the playlist and generates an optimized video recap, perfect for quick consumption and sharing.

### Features

- **Playlist Video Clip Extraction**  
  Extracts video clips from a YouTube playlist by specifying time intervals for each clip.

- **Video Recap Generation**  
  Combines selected clips into a cohesive summary video.

- **Optimized for Social Media Sharing**  
  The recap videos are formatted for quick sharing on platforms like Instagram, Facebook, and Twitter.

- **User-friendly Interface**  
  Allows users to input YouTube playlist URLs and select clips for summarization.

### Workflow

1. **Input Playlist URL**  
   Paste the YouTube playlist URL into the application.

2. **Clip Selection**  
   Select which video clips to include in the recap from the playlist.

3. **Recap Creation**  
   Automatically generates a video recap by combining the selected clips.

4. **Output**  
   Recap video formatted for social media sharing.

**Sample Outputs**

- **Video Recap:**  
  A short video featuring the highlights from a playlist, optimized for social media platforms.

### Setup Instructions

To run the project locally:

1. **Clone the Repository**

   ```bash
   git clone https://github.com/<your-username>/youtube-playlist-recap-maker.git  
   cd youtube-playlist-recap-maker  
   ```

2. **Use Python 3.10.0**  
   Make sure to use Python version 3.10.0. You can check your Python version by running:

   ```bash
   python --version  
   ```

   If you need to install or upgrade to Python 3.10.0, follow the instructions on the official Python website: [Download Python 3.10.0](https://www.python.org/downloads/release/python-3100/).

3. **Install Dependencies**  
   Install required Python libraries:

   ```bash
   pip install -r requirements.txt  
   ```

4. **Run the Application**  
   Start the application:

   ```bash
   python app.py  
   ```

5. **Input the Playlist URL**  
   Paste the YouTube playlist link and select the clips you want to include in the recap.

### Project Structure

- **app.py**: The main application that allows users to interact with the system.
- **clip_extraction.py**: Extracts video clips from YouTube playlist.
- **recap_generation.py**: Combines clips into a cohesive recap video.
- **requirements.txt**: Lists project dependencies.

### Technologies Used

- **Python**: Main programming language for the backend.
- **MoviePy**: Library for video processing.
- **YouTube API**: To fetch video data from YouTube playlists.
- **FFmpeg**: For video manipulation and editing.

### Future Enhancements

- Integration with social media platforms for auto-posting recap videos.
- Support for other video platforms (e.g., Vimeo).
- AI-powered clip selection based on content analysis.

---
