from huggingface_hub import hf_hub_download
import os

def download_all():
    # =========================================================================
    # 1. ONNX Runtime Models from warmshao/FasterLivePortrait (PUBLIC, no auth)
    # =========================================================================
    repo_id = "warmshao/FasterLivePortrait"
    onnx_files = [
        "liveportrait_onnx/appearance_feature_extractor.onnx",
        "liveportrait_onnx/motion_extractor.onnx",
        "liveportrait_onnx/warping_spade-fix.onnx",
        "liveportrait_onnx/stitching.onnx",
        "liveportrait_onnx/stitching_lip.onnx",
        "liveportrait_onnx/stitching_eye.onnx",
        "liveportrait_onnx/landmark.onnx",
        "liveportrait_onnx/face_2dpose_106_static.onnx",
        "liveportrait_onnx/retinaface_det_static.onnx",
    ]

    print("=" * 60)
    print(" Downloading ONNX Models from warmshao/FasterLivePortrait")
    print("=" * 60)
    for f in onnx_files:
        print(f"  Downloading {f}...")
        try:
            hf_hub_download(repo_id=repo_id, filename=f, local_dir="weights")
            print(f"  ✓ Done")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # =========================================================================
    # 2. Windows DLL plugin for grid_sample_3d (required for ONNX on Windows)
    # =========================================================================
    print(f"\n  Downloading grid_sample_3d_plugin.dll...")
    try:
        hf_hub_download(repo_id=repo_id, filename="liveportrait_onnx/grid_sample_3d_plugin.dll", local_dir="weights")
        print(f"  ✓ Done")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    print("\n" + "=" * 60)
    print(" All downloads complete!")
    print("=" * 60)

if __name__ == "__main__":
    download_all()
