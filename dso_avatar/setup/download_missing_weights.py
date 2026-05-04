import os
import urllib.request

base_dir = r"c:\Users\Rayen\Desktop\testforfum\ESPRIT-PI-4DS10-25-26-Co_Win\dso1\src\avatar\LiveTalking\models"
files_to_download = {
    os.path.join(base_dir, "dwpose", "dw-ll_ucoco_384.pth"): "https://huggingface.co/yzd-v/DWPose/resolve/main/dw-ll_ucoco_384.pth",
    os.path.join(base_dir, "face-parse-bisent", "79999_iter.pth"): "https://huggingface.co/ManyOtherFunctions/face-parse-bisent/resolve/main/79999_iter.pth",
    os.path.join(base_dir, "face-parse-bisent", "resnet18-5c106cde.pth"): "https://huggingface.co/ManyOtherFunctions/face-parse-bisent/resolve/main/resnet18-5c106cde.pth",
}

for filepath, url in files_to_download.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if not os.path.exists(filepath):
        print(f"Downloading {os.path.basename(filepath)} from {url}...")
        try:
            urllib.request.urlretrieve(url, filepath)
            print("Done!")
        except Exception as e:
            print(f"Failed to download {os.path.basename(filepath)}: {e}")
    else:
        print(f"{os.path.basename(filepath)} already exists.")

print("Download script finished.")
