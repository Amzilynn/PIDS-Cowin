from huggingface_hub import HfApi
api = HfApi()
try:
    files = api.list_repo_files(repo_id="KwaiVGI/LivePortrait")
    print("Files in KwaiVGI/LivePortrait:")
    for f in files:
        print(f)
except Exception as e:
    print(f"Error listing KwaiVGI/LivePortrait: {e}")

try:
    files = api.list_repo_files(repo_id="KlingTeam/LivePortrait")
    print("\nFiles in KlingTeam/LivePortrait:")
    for f in files:
        print(f)
except Exception as e:
    print(f"Error listing KlingTeam/LivePortrait: {e}")
