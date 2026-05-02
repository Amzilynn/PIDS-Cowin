import os
import urllib.request
import zipfile
import shutil

FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip"
TARGET_DIR = os.getcwd()
ZIP_PATH = os.path.join(TARGET_DIR, "ffmpeg.zip")

def download_ffmpeg():
    print(f"Downloading FFmpeg from {FFMPEG_URL}...")
    try:
        urllib.request.urlretrieve(FFMPEG_URL, ZIP_PATH)
        print("Download complete. Extracting...")
        
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(TARGET_DIR)
        
        # Find the bin folder and move ffmpeg.exe to root
        for root, dirs, files in os.walk(TARGET_DIR):
            if "ffmpeg.exe" in files:
                shutil.copy(os.path.join(root, "ffmpeg.exe"), os.path.join(TARGET_DIR, "ffmpeg.exe"))
                shutil.copy(os.path.join(root, "ffprobe.exe"), os.path.join(TARGET_DIR, "ffprobe.exe"))
                print("FFmpeg is now ready in the project root!")
                return True
    except Exception as e:
        print(f"Failed: {e}")
        return False
    finally:
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)

if __name__ == "__main__":
    download_ffmpeg()
