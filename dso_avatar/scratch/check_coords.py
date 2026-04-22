import pickle
import os

path = r'data/avatars/sarah_static/coords.pkl'
if os.path.exists(path):
    with open(path, 'rb') as f:
        coords = pickle.load(f)
        print(f"Coords count: {len(coords)}")
        print(f"First coord: {coords[0]}")
else:
    print("File not found")
