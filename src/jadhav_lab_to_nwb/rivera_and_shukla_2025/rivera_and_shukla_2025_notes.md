# Notes concerning the rivera_and_shukla_2025 conversion

## File Structure
- In Ashutosh's poster, there are 2 reward contingencies (50% and 100%) + an opaque control
- ratsamples doesn't follow the normal file structure, but just has a bunch of .csv files. What's going on there?
    - Looks like those .csvs are the only files that tabulate individual trials and their outcomes (matched or not, etc.)
    - hiswell?
- In Ashutosh's poster, head orientation angle relative to partner's COM are calculated, but I don't see that anywhere in the data.
    - Head angle is considered a more advanced processed data stream --> not included
- Detailed subject info is present in Edward's Poster
- DIO folders have video and timestamps, but no .dat files like in Jacob's project
- Some dates have DLC data, but some just have DIO --> bc some DLC sessions were so bad they were omitted
- DIO folders have sequential (in time) numbered files ex. 1, 3, 5, 7
    - --> what about 2, 4, 6? --> those are the other animal pair (XFN2-XFN4)
- Some of the files are named XFN1-XFN3 and others are named XFN3-XFN1. Does this correspond to left vs right W Maze?
    - yes

## DLC
- *_full.mp4 video is labeled, other one is identical to .h264 video
- Need config.yaml(s)
- resnet50 vs dlcrnetms5? --> use resnet50
