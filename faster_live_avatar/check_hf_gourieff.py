from huggingface_hub import HfApi
api = HfApi()
try:
    files = api.list_repo_files(repo_id="Gourieff/LivePortrait")
    print("Files in Gourieff/LivePortrait:")
    for f in files:
        print(f)
except Exception as e:
    print(f"Error listing Gourieff/LivePortrait: {e}")
