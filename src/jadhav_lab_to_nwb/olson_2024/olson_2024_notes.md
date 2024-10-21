# Notes concerning the olson_2024 conversion

## File Structure

- Lots of folders w/ SpikeGadgets output: What does the folder naming convention mean? Different sessions?
    - each session(?) folder contains
        - a SpikeGadgets .rec file (can open w/ existing Neuroconv interface)
        - video timestamps (can open with readCameraModuleTimeStamps from Trodes docs)
        - synced(?) video timestamps (can open with readCameraModuleTimeStamps from Trodes docs)
        - .h264 video file (can open with VLC)
        - .trackgeometry is just a text file with a list of object names -- probably not useful?
        - .trodesComments file contains start and stop timestamps
        - .stateScriptLog is some kind of script -- used to run the trodes software?

- Missing DLC data

- SL18_D19.DIO has a bunch of .dat files -- also SpikeGadgets?
    - Apparently DIO stands for digital input/output: https://docs.spikegadgets.com/en/latest/basic/Workspace.html
- SL18_D19.ExportedUnitStats has a bunch of .txt files with unit properties
- SL18_D19.SpikesFinal has plexon files (.plx) -- from spike sorting?
- SL18_D19.yml has a bunch of useful neuroconv-style metadata

In JLab-Analysis-Suite/SpikeGadgets_Export_Pipeline/PipelineNotes.txt,
    - Jacob mentions that neuroconv's interface only converts the raw .rec file but nothing else --> will need to extend the interface to cover the rest of the data.
