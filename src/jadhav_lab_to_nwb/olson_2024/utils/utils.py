"""Utility functions for the Olson 2024 dataset."""


def get_epoch_name(name: str) -> str:
    """Get the epoch name from the file or folder name."""
    split_name = name.split("_")
    epoch_name = "_".join(split_name[2:6])
    return epoch_name
