# jadhav-lab-to-nwb
NWB conversion scripts for Jadhav lab data to the [Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.

## Installation from Github
We recommend installing the package directly from Github. This option has the advantage that the source code can be modified if you need to amend some of the code we originally provided to adapt to future experimental differences. To install the conversion from GitHub you will need to use `git` ([installation instructions](https://github.com/git-guides/install-git)). We also recommend the installation of `conda` ([installation instructions](https://docs.conda.io/en/latest/miniconda.html)) as it contains all the required machinery in a single and simple install.

From a terminal (note that conda should install one in your system) you can do the following:

```bash
git clone https://github.com/catalystneuro/jadhav-lab-to-nwb
cd jadhav-lab-to-nwb
conda env create --file make_env.yml
conda activate jadhav_lab_to_nwb_env
```

This creates a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html) which isolates the conversion code from your system libraries. We recommend that you run all your conversion related tasks and analysis from the created environment in order to minimize issues related to package dependencies.

If you fork this repository and are running code from that fork, instead use
```bash
git clone https://github.com/your_github_username/jadhav-lab-to-nwb
```

Then you can run
```bash
cd jadhav-lab-to-nwb
conda env create --file make_env.yml
conda activate jadhav_lab_to_nwb_env
```

Alternatively, if you want to avoid conda altogether (for example if you use another virtual environment tool) you can install the repository with the following commands using only pip:

```bash
git clone https://github.com/catalystneuro/jadhav-lab-to-nwb
cd jadhav-lab-to-nwb
pip install -e .
```

Note:
both of the methods above install the repository in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs).
The dependencies for this environment are stored in the dependencies section of the `pyproject.toml` file.

All conversion scripts can be run from the single `jadhav_lab_to_nwb_env` environment.

## Spyglass Environment Setup

The Spyglass database insertion scripts require a separate Spyglass environment. To set up Spyglass, follow the detailed installation instructions at:

**[Spyglass Setup Guide](https://lorenfranklab.github.io/spyglass/latest/notebooks/00_Setup/)**

This will guide you through:
- Installing Spyglass and its dependencies
- Setting up the MySQL database
- Configuring database connections
- Setting up the required directory structure

Once Spyglass is installed, you can run the insertion scripts in the Spyglass environment:

```bash
conda activate spyglass
python src/jadhav_lab_to_nwb/olson_2024/olson_2024_insert_session.py
```

## Helpful Definitions

This conversion project is comprised primarily by DataInterfaces, NWBConverters, and conversion scripts.

In neuroconv, a [DataInterface](https://neuroconv.readthedocs.io/en/main/user_guide/datainterfaces.html) is a class that specifies the procedure to convert a single data modality to NWB.
This is usually accomplished with a single read operation from a distinct set of files.
For example, in this conversion, the `Olson2024BehaviorInterface` contains the code that converts all of the behavioral DIO data to NWB from raw SpikeGadgets files.

In neuroconv, a [NWBConverter](https://neuroconv.readthedocs.io/en/main/user_guide/nwbconverter.html) is a class that combines many data interfaces and specifies the relationships between them, such as temporal alignment.
This allows users to combine multiple modalities into a single NWB file in an efficient and modular way.

In this conversion project, the conversion scripts determine which sessions to convert,
instantiate the appropriate NWBConverter object,
and convert all of the specified sessions, saving them to an output directory of .nwb files.

## Repository structure
Each conversion is organized in a directory of its own in the `src` directory:

    jadhav-lab-to-nwb/
    ├── LICENSE
    ├── MANIFEST.in
    ├── README.md
    ├── make_env.yml
    ├── pyproject.toml
    └── src
        └── jadhav_lab_to_nwb
            ├── __init__.py
            ├── datainterfaces/
            │   ├── __init__.py
            │   ├── base_dlc_interface.py
            │   ├── base_epoch_interface.py
            │   └── base_video_interface.py
            ├── olson_2024/
            │   ├── __init__.py
            │   ├── olson_2024_behavior_interface.py
            │   ├── olson_2024_convert_all_sessions.py
            │   ├── olson_2024_convert_session.py
            │   ├── olson_2024_dlc_interface.py
            │   ├── olson_2024_epoch_interface.py
            │   ├── olson_2024_insert_session.py
            │   ├── olson_2024_metadata.yaml
            │   ├── olson_2024_notes.md
            │   ├── olson_2024_nwbconverter.py
            │   ├── olson_2024_sorting_interface.py
            │   ├── olson_2024_spike_gadgets_lfp_interface.py
            │   ├── olson_2024_spike_gadgets_recording_interface.py
            │   └── olson_2024_video_interface.py
            ├── rivera_and_shukla_2025/
            │   ├── __init__.py
            │   ├── rivera_and_shukla_2025_behavior_interface.py
            │   ├── rivera_and_shukla_2025_convert_all_sessions.py
            │   ├── rivera_and_shukla_2025_convert_session.py
            │   ├── rivera_and_shukla_2025_dlc_interface.py
            │   ├── rivera_and_shukla_2025_epoch_interface.py
            │   ├── rivera_and_shukla_2025_insert_all_sessions.py
            │   ├── rivera_and_shukla_2025_insert_session.py
            │   ├── rivera_and_shukla_2025_metadata.yaml
            │   ├── rivera_and_shukla_2025_notes.md
            │   ├── rivera_and_shukla_2025_nwbconverter.py
            │   └── rivera_and_shukla_2025_video_interface.py
            ├── spyglass_extensions/
            │   ├── __init__.py
            │   └── task_leds.py
            ├── tools/
            │   ├── __init__.py
            │   ├── spikegadgets.py
            │   └── spikeinterface.py
            └── utils/
                ├── __init__.py
                └── utils.py

## Data Conversion Pipeline

This project implements a comprehensive pipeline for converting electrophysiology and behavioral data to NWB format and ingesting it into Spyglass databases:

**Source Data → Data Interfaces → NWB Files → Spyglass Database**

### Supported Data Modalities

- **Electrophysiology**: Raw neural recordings from SpikeGadgets systems
- **Local Field Potentials (LFP)**: Processed LFP data from SpikeGadgets
- **Spike Sorting**: Unit spike times and waveform statistics
- **Behavioral Video**: H.264 video files with synchronized timestamps
- **Pose Estimation**: DeepLabCut pose tracking data
- **Digital I/O Events**: Behavioral markers and task events
- **Task Data**: Custom LED-based behavioral paradigms

## Base Interface Classes

The `datainterfaces/` directory contains base classes that provide common functionality:

* `base_dlc_interface.py` : Base class for DeepLabCut pose estimation data conversion with configurable body part filtering and coordinate transformations.
* `base_epoch_interface.py` : Base class for epoch/interval data conversion with automatic epoch detection from video timestamps.
* `base_video_interface.py` : Base class for behavioral video conversion with external file linking and timestamp synchronization.

## Olson 2024 Dataset Conversion

For the conversion `olson_2024` you can find a directory located in `src/jadhav_lab_to_nwb/olson_2024`. This conversion handles electrophysiology data from spatial navigation experiments with the following components:

### Data Interfaces
* `olson_2024_behavior_interface.py` : Converts digital I/O behavioral events from SpikeGadgets DIO files, including reward delivery, LED states, and task markers.
* `olson_2024_dlc_interface.py` : Converts DeepLabCut pose estimation data with body part filtering and coordinate system transformations for spatial tracking.
* `olson_2024_epoch_interface.py` : Creates task epochs from video timestamps with automatic sleep/run/task detection and interval list generation.
* `olson_2024_sorting_interface.py` : Converts spike sorting results including unit spike times, waveform statistics, and tetrode information.
* `olson_2024_spike_gadgets_lfp_interface.py` : Converts local field potential data from SpikeGadgets LFP files with proper electrode mapping.
* `olson_2024_spike_gadgets_recording_interface.py` : Converts raw electrophysiology data from SpikeGadgets .rec files with electrode group configuration.
* `olson_2024_video_interface.py` : Converts behavioral video files with external file references and synchronized timestamps.

### Conversion Scripts
* `olson_2024_convert_session.py` : Converts a single experimental session with all data modalities. Automatically discovers epoch folders and configures all interfaces.
* `olson_2024_convert_all_sessions.py` : Batch conversion script for multiple sessions with parallel processing and error handling.

### NWB Converter
* `olson_2024_nwbconverter.py` : Main converter class that orchestrates all data interfaces and handles temporal alignment between modalities.

### Spyglass Integration
* `olson_2024_insert_session.py` : Inserts converted NWB files into Spyglass database with comprehensive data integrity testing and custom table extensions.

### Configuration Files
* `olson_2024_metadata.yaml` : High-level metadata including subject information, experimental setup, and electrode configurations.
* `olson_2024_notes.md` : Detailed conversion notes, edge cases, and dataset-specific considerations.

## Rivera and Shukla 2025 Dataset Conversion

For the conversion `rivera_and_shukla_2025` you can find a directory located in `src/jadhav_lab_to_nwb/rivera_and_shukla_2025`. This conversion handles a different experimental paradigm with similar data modalities:

### Data Interfaces
* `rivera_and_shukla_2025_behavior_interface.py` : Behavioral event conversion adapted for this dataset's DIO structure.
* `rivera_and_shukla_2025_dlc_interface.py` : DeepLabCut interface customized for this experiment's pose tracking setup.
* `rivera_and_shukla_2025_epoch_interface.py` : Epoch detection tailored to this dataset's experimental structure.
* `rivera_and_shukla_2025_video_interface.py` : Video conversion adapted for this dataset's file organization.

### Conversion Scripts
* `rivera_and_shukla_2025_convert_session.py` : Single session conversion for this dataset.
* `rivera_and_shukla_2025_convert_all_sessions.py` : Batch conversion with dataset-specific session discovery.

### NWB Converter
* `rivera_and_shukla_2025_nwbconverter.py` : Converter class configured for this dataset's data structure.

### Spyglass Integration
* `rivera_and_shukla_2025_insert_session.py` : Database insertion script for individual sessions.
* `rivera_and_shukla_2025_insert_all_sessions.py` : Batch database insertion for the entire dataset.

### Configuration Files
* `rivera_and_shukla_2025_metadata.yaml` : Dataset-specific metadata and experimental parameters.
* `rivera_and_shukla_2025_notes.md` : Conversion notes and dataset-specific considerations.

## Spyglass Extensions and Tools

### Spyglass Extensions
* `spyglass_extensions/task_leds.py` : Custom Spyglass table for task-specific LED behavioral data that extends standard Spyglass functionality.

### Utility Tools
* `tools/spikegadgets.py` : Utilities for reading and processing SpikeGadgets data files including .rec, .LFP, and .DIO formats.
* `tools/spikeinterface.py` : SpikeInterface integration utilities for spike sorting data processing and validation.
* `utils/utils.py` : General utility functions for file handling, data validation, and common conversion operations.

## Running a Conversion

### Converting the Olson 2024 Dataset

To convert a single session:
1. In `src/jadhav_lab_to_nwb/olson_2024/olson_2024_convert_session.py`, update the `data_dir_path` and
    `output_dir_path` to appropriate local paths. `data_dir_path` should be the directory containing session folders
    following the naming convention `{subject_id}_{session_id}`. `output_dir_path` can be any valid path where
    the output NWB files will be stored.
2. Run the conversion:
    ```bash
    python src/jadhav_lab_to_nwb/olson_2024/olson_2024_convert_session.py
    ```

### Converting the Rivera and Shukla 2025 Dataset

To convert a single session:
1. In `src/jadhav_lab_to_nwb/rivera_and_shukla_2025/rivera_and_shukla_2025_convert_session.py`, update the `data_dir_path` and
    `output_dir_path` to appropriate local paths following the same pattern as the Olson 2024 dataset.
2. Run the conversion:
    ```bash
    python src/jadhav_lab_to_nwb/rivera_and_shukla_2025/rivera_and_shukla_2025_convert_session.py
    ```

To convert the entire dataset:
1. Update `data_dir_path` and `output_dir_path` in `src/jadhav_lab_to_nwb/rivera_and_shukla_2025/rivera_and_shukla_2025_convert_all_sessions.py`.
2. Run the batch conversion:
    ```bash
    python src/jadhav_lab_to_nwb/rivera_and_shukla_2025/rivera_and_shukla_2025_convert_all_sessions.py
    ```

### Spyglass Database Insertion

After converting to NWB, insert data into Spyglass. **Note: This requires the Spyglass environment (see Spyglass Environment Setup above):**

```bash
conda activate spyglass
python src/jadhav_lab_to_nwb/olson_2024/olson_2024_insert_session.py
```

This will:
- Insert all standard Spyglass data (ephys, behavior, video, LFP)
- Add spike sorting annotations and unit metadata
- Insert custom task LED data
- Run comprehensive data integrity tests

## Expected Data Structure

### Olson 2024 Dataset Structure
```
data_dir_path/
└── {subject_id}_{session_id}/
    ├── {subject_id}_{session_id}_S{epoch}_F{file}_{timestamp}/
    │   ├── {epoch_name}.rec                    # Raw electrophysiology
    │   ├── {epoch_name}.trodesComments         # Trodes metadata
    │   ├── {epoch_name}.1.h264                 # Behavioral video
    │   └── {epoch_name}.1.videoTimeStamps      # Video timestamps
    ├── {session_name}.SpikesFinal/             # Spike sorting results
    ├── {session_name}.ExportedUnitStats/       # Unit statistics
    ├── {session_name}.LFP/                     # LFP data
    ├── {session_name}.DLC/                     # DeepLabCut pose data
    └── {session_name}.DIO/                     # Digital I/O events
```

## Customizing for New Datasets

To create a new conversion:

1. **Create a new dataset directory** following the naming convention `{experimenter}_{year}`
2. **Implement dataset-specific interfaces** by inheriting from base classes in `datainterfaces/`
3. **Create an NWBConverter class** that combines all interfaces for your dataset
4. **Write conversion scripts** for single sessions and batch processing
5. **Add Spyglass insertion scripts** if database integration is needed
6. **Create metadata files** with dataset-specific experimental parameters

Each conversion should be self-contained within its directory and follow the established patterns for consistency and maintainability.
