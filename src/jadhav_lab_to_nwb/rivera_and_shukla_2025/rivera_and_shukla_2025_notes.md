# Notes concerning the rivera_and_shukla_2025 conversion

## File Structure
- In Ashutosh's poster, there are 2 reward contingencies (50% and 100%) + an opaque control
- ratsamples doesn't follow the normal file structure, but just has a bunch of .csv files. What's going on there?
    - Looks like those .csvs are the only files that tabulate individual trials and their outcomes (matched or not, etc.)
    - hiswell?
- In Ashutosh's poster, head orientation angle relative to partner's COM are calculated, but I don't see that anywhere in the data.
    - Head angle is considered a more advanced processed data stream --> not included
- Detailed subject info is present in Edward's Poster
- DIO folders have video and timestamps, but no .dat files like in Jacob's project --> use stateScriptLog files instead
- Some dates have DLC data, but some just have DIO --> bc some DLC sessions were so bad they were omitted
- DIO folders have sequential (in time) numbered files ex. 1, 3, 5, 7
    - --> what about 2, 4, 6? --> those are the other animal pair (XFN2-XFN4)
- Some of the files are named XFN1-XFN3 and others are named XFN3-XFN1. Does this correspond to left vs right W Maze?
    - yes

## DLC
- *_full.mp4 video is labeled, other one is identical to .h264 video
- Need config.yaml(s)
- resnet50 vs dlcrnetms5? --> use resnet50

## Behavior

- stateScriptLog files have some kind of custom script output
- output script files are different for 50% and 100% conditions
- nose pokes are recorded for each well "Poke in wellB", "Poke in well1", etc.
- matched pokes are recorded and delivered rewards "Matched pokes in position B2" unless it is followed by "but, no reward" in the next line
- Some of the sessions in the 50% folder (ex. CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/08-03-2023) uses a deterministic stateScriptLog where every matched poke results in a reward. How to classify this session?

## Edge cases
- Some of the sessions (ex. CoopLearnProject/CohortAS1/Social W/100%/XFN2-XFN4/07-14-2023) has a different number of timestamps for video and DLC
    - Full List
        CoopLearnProject/CohortAS1/Social W/100%/XFN1-XFN3/07-14-2023
        CoopLearnProject/CohortAS1/Social W/100%/XFN1-XFN3/07-21-2023
        CoopLearnProject/CohortAS1/Social W/100%/XFN2-XFN4/07-14-2023
        CoopLearnProject/CohortAS1/Social W/100%/XFN2-XFN4/07-31-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/08-24-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/08-30-2023
- Some of the sessions (ex. CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/08-16-2023) are missing DLC epochs
    - Full List
        CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/08-16-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/09-06-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/09-13-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/09-14-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/09-15-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/09-18-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/09-20-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/09-21-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/09-22-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/08-03-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/08-17-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/08-18-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/08-28-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/08-29-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/09-01-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/09-06-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/09-13-2023
        CoopLearnProject/CohortAS1/Social W/50%/XFN2-XFN4/09-14-2023
- One of the sessions (ex. CoopLearnProject/CohortAS1/Social W/100%/XFN1-XFN3/07-15-2023) have incomplete epochs
    - This is just a video of the mazes without behavior --> skipping
- 2 of the sessions (ex. CoopLearnProject/CohortAS1/Social W/100%/XFN1-XFN3/07-27-2023) have corrupted hdf5 (and csv) files
    - Skipping corrupted DLC
    - Full List
        CoopLearnProject/CohortAS1/Social W/100%/XFN1-XFN3/07-27-2023
        CoopLearnProject/CohortAS1/Social W/100%/XFN2-XFN4/07-27-2023
- Some of the sessions (ex. CoopLearnProject/CohortAS1/Social W/50%/XFN1-XFN3/08-07-2023) have multiple videos/epoch
    - Added support for multi-segment epochs
- The XFN1-XFN3/07-17-2023 folder has 07-15-2023 data in it --> skipping
- One session (CohortAS1/Social W/50%/XFN2-XFN4/08-03-2023) has a missing DLC segment
- One session (CohortAS1/Social W/50%/XFN2-XFN4/09-21-2023) has ~~~ at the end of the behavior file
