"""Primary script to run to convert all sessions in a dataset using session_to_nwb."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from pprint import pformat
import traceback
from tqdm import tqdm
import warnings

from jadhav_lab_to_nwb.rivera_and_shukla_2025.rivera_and_shukla_2025_convert_session import session_to_nwb


def dataset_to_nwb(
    *,
    data_dir_path: str | Path,
    output_dir_path: str | Path,
    max_workers: int = 1,
    verbose: bool = True,
):
    """Convert the entire dataset to NWB.

    Parameters
    ----------
    data_dir_path : str | Path
        The path to the directory containing the raw data.
    output_dir_path : str | Path
        The path to the directory where the NWB files will be saved.
    max_workers : int, optional
        The number of workers to use for parallel processing, by default 1
    verbose : bool, optional
        Whether to print verbose output, by default True
    """
    data_dir_path = Path(data_dir_path)
    session_to_nwb_kwargs_per_session = get_session_to_nwb_kwargs_per_session(
        data_dir_path=data_dir_path,
        output_dir_path=Path(output_dir_path),
        verbose=verbose,
    )

    exception_folder_path = Path(output_dir_path) / "exceptions"
    exception_folder_path.mkdir(parents=True, exist_ok=True)
    warnings_folder_path = Path(output_dir_path) / "warnings"
    warnings_folder_path.mkdir(parents=True, exist_ok=True)

    futures = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for session_to_nwb_kwargs in session_to_nwb_kwargs_per_session:
            session_to_nwb_kwargs["output_dir_path"] = output_dir_path
            session_to_nwb_kwargs["verbose"] = verbose
            subject_id = session_to_nwb_kwargs["subject_id"]
            session_id = session_to_nwb_kwargs["session_folder_path"].name
            nwbfile_name = f"sub-{subject_id}_ses-{session_id}.nwb"
            exception_file_path = exception_folder_path / f"ERROR_{nwbfile_name}.txt"
            warnings_file_path = warnings_folder_path / f"WARNINGS_{nwbfile_name}.txt"
            futures.append(
                executor.submit(
                    safe_session_to_nwb,
                    session_to_nwb_kwargs=session_to_nwb_kwargs,
                    exception_file_path=exception_file_path,
                    warnings_file_path=warnings_file_path,
                )
            )
        for _ in tqdm(as_completed(futures), total=len(futures)):
            pass


def safe_session_to_nwb(
    *, session_to_nwb_kwargs: dict, exception_file_path: str | Path, warnings_file_path: str | Path
):
    """Convert a session to NWB while handling any errors by recording error messages to the exception_file_path.

    Parameters
    ----------
    session_to_nwb_kwargs : dict
        The arguments for session_to_nwb.
    exception_file_path : Path
        The path to the file where the exception messages will be saved.
    warnings_file_path : Path
        The path to the file where warnings will be saved.
    """
    exception_file_path = Path(exception_file_path)
    warnings_file_path = Path(warnings_file_path)

    # Capture warnings
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        try:
            session_to_nwb(**session_to_nwb_kwargs)
        except Exception as e:
            with open(exception_file_path, mode="w") as f:
                f.write(f"session_to_nwb_kwargs: \n {pformat(session_to_nwb_kwargs)}\n\n")
                f.write(traceback.format_exc())

    # Write warnings to file if any occurred
    if warning_list:
        with open(warnings_file_path, mode="w") as f:
            f.write(f"session_to_nwb_kwargs: \n {pformat(session_to_nwb_kwargs)}\n\n")
            for warning in warning_list:
                f.write(f"{warning.category.__name__}: {warning.message}\n")
                f.write(f"File: {warning.filename}, Line: {warning.lineno}\n\n")


def get_session_to_nwb_kwargs_per_session(
    *,
    data_dir_path: Path,
    output_dir_path: Path,
    verbose: bool = False,
):
    """Get the kwargs for session_to_nwb for each session in the dataset.

    Parameters
    ----------
    data_dir_path : str | Path
        The path to the directory containing the raw data.
    output_dir_path : str | Path
        The path to the directory where the NWB files will be saved.
    verbose : bool, optional
        Whether to print verbose output, by default False

    Returns
    -------
    list[dict[str, Any]]
        A list of dictionaries containing the kwargs for session_to_nwb for each session.
    """
    experimental_conditions = ["100%", "50%", "Opaque"]
    session_to_nwb_kwargs_per_session = []
    for condition in experimental_conditions:
        condition_folder_path = data_dir_path / "CohortAS1" / "Social W" / condition
        for subject_pair_folder in condition_folder_path.iterdir():
            subject_id1, subject_id2 = subject_pair_folder.name.split("-")
            for session_folder_path in subject_pair_folder.iterdir():
                sub1_session_to_nwb_kwargs = dict(
                    session_folder_path=session_folder_path,
                    subject_id=subject_id1,
                    output_dir_path=output_dir_path,
                    experimental_condition=condition,
                    stub_test=False,
                    verbose=verbose,
                )
                sub2_session_to_nwb_kwargs = dict(
                    session_folder_path=session_folder_path,
                    subject_id=subject_id2,
                    output_dir_path=output_dir_path,
                    experimental_condition=condition,
                    stub_test=False,
                    verbose=verbose,
                )
                session_to_nwb_kwargs_per_session.append(sub1_session_to_nwb_kwargs)
                session_to_nwb_kwargs_per_session.append(sub2_session_to_nwb_kwargs)
    return session_to_nwb_kwargs_per_session


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("/Volumes/T7/CatalystNeuro/Jadhav/CoopLearnProject")
    output_dir_path = Path("/Volumes/T7/CatalystNeuro/Spyglass/raw")
    max_workers = 4
    verbose = False

    dataset_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        max_workers=max_workers,
        verbose=False,
    )
