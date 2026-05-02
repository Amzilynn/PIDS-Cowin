from huggingface_hub import HfApi
api = HfApi()
try:
    results = api.search_models(search="audio2exp")
    print("Models matching 'audio2exp':")
    for res in results:
        print(f"{res.id}")
except Exception as e:
    print(f"Error searching for audio2exp: {e}")
