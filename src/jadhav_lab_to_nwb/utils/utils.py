"""Utility functions for the Jadhav Lab Conversion."""


def olson_2024_get_epoch_name(name: str) -> str:
    """Get the epoch name from the file or folder name."""
    split_name = name.split("_")
    epoch_name = "_".join(split_name[2:6])
    return epoch_name


def rivera_and_shukla_2025_get_epoch_name(name: str) -> str:
    """Get the epoch name from the file or folder name."""
    epoch_name = name.split("(")[-1].split(")")[0]  # log07-20-2023(5-XFN1-XFN3).1.h264 --> 5-XFN1-XFN3
    return epoch_name
