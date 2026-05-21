# -*- coding: utf-8 -*-
"""
Binary file reader - simplified function version
"""

import pandas as pd
import numpy as np
from pathlib import Path
import struct
import os

absolutePathToCurrentFolder = Path(__file__).resolve().parent

# -------------------------------
# Helpers
# -------------------------------
_matrix = [
    62, 61, 63, 58, 56, 59, 60, 53, 54, 52, 57, 55, 50, 51, 48, 49,
    45, 47, 43, 46, 41, 44, 39, 42, 37, 40, 35, 38, 33, 36, 27, 34,
    31, 32, 29, 30, 25, 28, 23, 26, 21, 24, 19, 22, 10, 20, 13, 18,
    11, 17, 8, 16, 14, 15, 1, 3, 5, 2, 0, 6, 4, 12, 7, 9
]
_translate_inv = {v: i for i, v in enumerate(_matrix)}

def translate_inv(ch):
    return _translate_inv[ch]

def tot_frame0(v):
    return [(v >> 27), (v >> 11) & 0xFFFF, v & 0x7FF]

def is_pico_header(v):
    return ((v & 0x3) == 0) and ((v >> 28) in (0x8, 0x9))

def is_pico_trailer(v):
    return ((v & 0x1) == 0) and ((v >> 28) == 0xA)

def correct_bin(b):
    thresholds = [5, 10, 15, 30, 60, 120]
    values =    [3.05, 6.1, 12.2, 24.4, 48.8, 97.6]
    for t, v in zip(thresholds, values):
        if b < t:
            return v
    return values[-1]

def read_chunks(f, size=1024):
    while chunk := f.read(size):
        yield chunk

def split_path(p):
    p = Path(p)
    return p.stem, p.suffix[1:], str(p.parent) + '/'

def readBinaryWeerocFileGetSize(path):
    count = 0

    with open(path, "rb") as f:
        for chunk in read_chunks(f):
            for i in range(0, len(chunk), 4):
                w = chunk[i:i + 4]
                if len(w) < 4:
                    continue

                val = int.from_bytes(w, "little")

                if val == 0xFFFFFFFF or is_pico_header(val) or is_pico_trailer(val):
                    continue

                count += 1

    return count

def readBinaryWeerocFile(path, TOF_ON=True):
    """
    Reads a binary file and returns:
    - ToT array (numpy)
    - ToF array (numpy)
    - size (int)
    """
    path = Path(path)
    fname, ftype, fdir = split_path(path)

    # Extract metadata
    parts = fname.split("_")
    f_port = int(parts[2])
    tag = "_".join(parts[3:])

    # Default parameters
    f_tot, f_toa = 1, 1

    for token in tag.split("_"):
        t = token.lower()
        if t.startswith("btot") or t.startswith("tot"):
            f_tot = correct_bin(int(t[4:]))
        elif t.startswith("btoa") or t.startswith("toa"):
            f_toa = correct_bin(int(t[4:]))

    # Use Python lists first (fast append)
    data_tot = []
    data_toa = []

    with open(path, "rb") as f:
        for chunk in read_chunks(f):
            for i in range(0, len(chunk), 4):
                w = chunk[i:i + 4]
                if len(w) < 4:
                    continue

                val = struct.unpack("<I", w)[0]

                if val == 0xFFFFFFFF or is_pico_header(val) or is_pico_trailer(val):
                    continue

                chan, toa_raw, tot_raw = tot_frame0(val)

                data_tot.append(tot_raw * f_tot)
                data_toa.append(toa_raw * f_toa if TOF_ON else 0)

    # Convert to NumPy arrays
    tot_array = np.asarray(data_tot, dtype=np.float64)
    tof_array = np.asarray(data_toa, dtype=np.float64)

    size = tot_array.size

    return tot_array, tof_array, size

def calib_TDC(tof_data):
    pathToTDC = os.path.join(absolutePathToCurrentFolder, "TDC_calib.npy")

    print(f"Loading TDC calibration from {pathToTDC}")

    DT = np.load(pathToTDC)
    DT_cum = np.concatenate(([0.0], np.cumsum(DT)[:-1]))

    rng = np.random.default_rng(1234)
    raw_data_i = np.round(tof_data / float(12.2)).astype(int)

    print(max(raw_data_i))

    return DT_cum[raw_data_i] + rng.random(raw_data_i.size) * DT[raw_data_i]

def readBinaryWeerocFileWithPicoCalibrated(pathToBinaryFile):
    tot_array, tof_array, size = readBinaryWeerocFile(pathToBinaryFile)

    # Apply TDC calibration to the ToF data
    return tot_array, calib_TDC(tof_array), size

# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":
    FILE_LIST = [
        "/home/daniel/Documents/data/dataWeeroc/data_25_sept/measurment1/MatriceMeasurements_Hamamatsu_58.5/data_section_0_Btot49_Btoa12_Gain8_Thr370_58.5V_1min.bin"
    ]

    for path in FILE_LIST:
        df, out_dir, tag = readBinaryWeerocFile(path)
        print(f"Read file: {path}")
        print(df.head())