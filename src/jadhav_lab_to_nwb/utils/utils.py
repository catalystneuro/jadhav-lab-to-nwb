"""Utility functions for the Jadhav Lab NWB conversion project.

This module provides helper functions for extracting epoch names from file and folder
names across different datasets in the Jadhav Lab conversion pipeline. These functions
are used to standardize epoch identification and naming conventions for consistent
data organization in the NWB format.
"""


def olson_2024_get_epoch_name(name: str) -> str:
    """Extract epoch name from Olson 2024 dataset file or folder names.

    This function parses file or folder names from the Olson 2024 dataset to extract
    standardized epoch identifiers. The epoch name is constructed by joining specific
    components of the underscore-separated filename, typically corresponding to
    experimental session and epoch information.

    Parameters
    ----------
    name : str
        File or folder name from the Olson 2024 dataset. Expected format includes
        underscore-separated components where positions 2-5 (inclusive) contain
        the epoch identification information.

    Returns
    -------
    str
        Extracted epoch name formed by joining filename components 2-5 with underscores.

    Examples
    --------
    >>> olson_2024_get_epoch_name("SL18_D19_S01_F01_BOX_SLP_20230503_112642")
    'S01_F01_BOX_SLP'

    Notes
    -----
    This function is specifically designed for the Olson 2024 dataset naming convention
    and may not work correctly with other dataset formats.
    """
    split_name = name.split("_")
    epoch_name = "_".join(split_name[2:6])
    return epoch_name


def rivera_and_shukla_2025_get_epoch_name(name: str) -> str:
    """Extract epoch name from Rivera and Shukla 2025 dataset file or folder names.

    This function parses file or folder names from the Rivera and Shukla 2025 dataset
    to extract standardized epoch identifiers.

    Parameters
    ----------
    name : str
        File or folder name from the Rivera and Shukla 2025 dataset.

    Returns
    -------
    str
        Extracted epoch name from within the parentheses of the filename.

    Examples
    --------
    >>> rivera_and_shukla_2025_get_epoch_name("log07-20-2023(5-XFN1-XFN3).1.h264")
    '5-XFN1-XFN3'

    Notes
    -----
    This function is specifically designed for the Rivera and Shukla 2025 dataset
    naming convention and may not work correctly with other dataset formats.
    """
    epoch_name = name.split("(")[-1].split(")")[0]
    return epoch_name
