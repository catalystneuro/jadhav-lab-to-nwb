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

- SL18_D19.DLC has the DLC output files for each session
    - .csv files contain all the standard DLC outputs
    - .mp4 files appear identical with the corresponding .h264 video file

- SL18_D19.msortOut has mountainsort output for nt1 and nt15

- SL18_D19.DIO has a bunch of .dat files
    - Apparently DIO stands for digital input/output: https://docs.spikegadgets.com/en/latest/basic/Workspace.html
    - Each file corresponds to a different digital channel (ex. SL18_D19.dio_ECU_Din1.dat = digital input channel 1)
    - Can read the data using readTrodesExtractedDataFile
    - 'data' field contains timestamps for each onset (0) and offset (1)
    - metadata yaml contains descriptions of each dio -- they correspond to behavioral events: Reward well 1-8 and Reward Pump 1-8
- SL18_D19.LFP has LFP data in .dat files
    - each .dat file has lfp data from 1 channel
    - there is a separate timestamps file
- SL18_D19.ExportedUnitStats has a bunch of .txt files with unit properties
- SL18_D19.SpikesFinal has plexon files (.plx) -- from spike sorting?
- SL18_D19.timestampoffset has a .txt file per session with a single number (usually 0) -- probably some kind of temporal alignment?
- SL18_D19.yml has a bunch of useful neuroconv-style metadata

In JLab-Analysis-Suite/SpikeGadgets_Export_Pipeline/PipelineNotes.txt,
    - Jacob mentions that neuroconv's interface only converts the raw .rec file but nothing else --> will need to extend the interface to cover the rest of the data.
