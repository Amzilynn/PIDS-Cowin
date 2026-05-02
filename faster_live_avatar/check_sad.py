from huggingface_hub import HfApi
api = HfApi()
try:
    files = api.list_repo_files(repo_id="Winfredy/SadTalker")
    print("Files in Winfredy/SadTalker:")
    for f in files:
        print(f)
except Exception as e:
    print(f"Error listing Winfredy/SadTalker: {e}")
