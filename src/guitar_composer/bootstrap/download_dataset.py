#!/usr/bin/env python3
"""
Download GuitarComposer data from Hugging Face Hub.
Public dataset — no authentication required.
"""

import os
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

HF_REPO_ID = "CoderGuitarist/guitar-composer-data"
LOCAL_DATA_DIR = Path(os.environ['HOME']+os.sep+".guitar-composer"+os.sep+"data")

def download_data(force: bool = False) -> str:
    """
    Download dataset from Hugging Face Hub to local ./data directory.
    
    Args:
        force: If True, re-download even if data already exists.
    
    Returns:
        Path to the downloaded data directory.
    """
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

    
    # Check if data already exists (simple heuristic)
    if not force and any(LOCAL_DATA_DIR.iterdir()):
        print(f"Data already exists at {LOCAL_DATA_DIR}")
        print("Use --force to re-download.")
        return str(LOCAL_DATA_DIR)
    
    print(f"Downloading dataset from {HF_REPO_ID}...")
    print(f"This may take a few minutes (~80 MB)...")
    
    downloaded_path = snapshot_download(
        repo_id=HF_REPO_ID,
        repo_type="dataset",
        local_dir=str(LOCAL_DATA_DIR),
        local_dir_use_symlinks=False,  # copy files, don't symlink
    )
    
    print(f"Dataset downloaded to: {downloaded_path}")
    return downloaded_path


def main():
    force = "--force" in sys.argv
    download_data(force=force)


if __name__ == "__main__":
    main()