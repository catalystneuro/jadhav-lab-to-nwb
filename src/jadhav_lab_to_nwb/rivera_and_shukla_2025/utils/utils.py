"""Utility functions for the Rivera and Shukla 2025 conversion."""


def get_epoch_name(name: str) -> str:
    """Get the epoch name from the file or folder name."""
    epoch_name = name.split("(")[-1].split(")")[0]  # log07-20-2023(5-XFN1-XFN3).1.h264 --> 5-XFN1-XFN3
    return epoch_name
