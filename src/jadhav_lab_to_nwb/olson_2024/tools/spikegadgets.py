"""Useful tools for dealing with spikegadgets data."""
from pydantic import FilePath
import numpy as np
import re


def readTrodesExtractedDataFile(filename: FilePath) -> dict:
    """Read Trodes Extracted Data File (.dat) and return as a dictionary.

    Adapted from https://docs.spikegadgets.com/en/latest/basic/ExportFunctions.html

    Parameters
    ----------
    filename : FilePath
        Path to the .dat file to read.

    Returns
    -------
    dict
        The contents of the .dat file as a dictionary
    """
    with open(filename, "rb") as f:
        # Check if first line is start of settings block
        if f.readline().decode("ascii").strip() != "<Start settings>":
            raise Exception("Settings format not supported")
        fields = True
        fieldsText = {}
        for line in f:
            # Read through block of settings
            if fields:
                line = line.decode("ascii").strip()
                # filling in fields dict
                if line != "<End settings>":
                    vals = line.split(": ")
                    fieldsText.update({vals[0].lower(): vals[1]})
                # End of settings block, signal end of fields
                else:
                    fields = False
                    dt = parseFields(fieldsText["fields"])
                    fieldsText["data"] = np.zeros([1], dtype=dt)
                    break
        # Reads rest of file at once, using dtype format generated by parseFields()
        dt = parseFields(fieldsText["fields"])
        data = np.fromfile(f, dt)
        fieldsText.update({"data": data})
        return fieldsText


def parseFields(fieldstr: str) -> np.dtype:
    """Parse the fields string from a Trodes Extracted Data File and return as a numpy dtype.

    Adapted from https://docs.spikegadgets.com/en/latest/basic/ExportFunctions.html

    Parameters
    ----------
    fieldstr : str
        The fields string from a Trodes Extracted Data File.

    Returns
    -------
    np.dtype
        The fields string as a numpy dtype.
    """
    # Returns np.dtype from field string
    sep = re.split("\s", re.sub(r"\>\<|\>|\<", " ", fieldstr).strip())
    # print(sep)
    typearr = []
    # Every two elmts is fieldname followed by datatype
    for i in range(0, sep.__len__(), 2):
        fieldname = sep[i]
        repeats = 1
        ftype = "uint32"
        # Finds if a <num>* is included in datatype
        if sep[i + 1].__contains__("*"):
            temptypes = re.split("\*", sep[i + 1])
            # Results in the correct assignment, whether str is num*dtype or dtype*num
            ftype = temptypes[temptypes[0].isdigit()]
            repeats = int(temptypes[temptypes[1].isdigit()])
        else:
            ftype = sep[i + 1]
        try:
            fieldtype = getattr(np, ftype)
        except AttributeError:
            print(ftype + " is not a valid field type.\n")
            exit(1)
        else:
            typearr.append((str(fieldname), fieldtype, repeats))
    return np.dtype(typearr)