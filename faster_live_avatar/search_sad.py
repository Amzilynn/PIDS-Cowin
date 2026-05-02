from huggingface_hub import HfApi
api = HfApi()
try:
    models = api.list_models(search="SadTalker")
    print("Models matching 'SadTalker':")
    for m in models:
        print(f"{m.id}")
except Exception as e:
    print(f"Error searching for SadTalker: {e}")
