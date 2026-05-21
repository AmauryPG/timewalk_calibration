# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 10:48:44 2025

@author: Wateb
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys, glob, struct, time
from tkinter import Tk, filedialog
from scipy.signal import find_peaks


#################################################################################################################
############# FONCTIONS #########################################################################################
#################################################################################################################
def check_packages():
    ''' Check if numpy, pandas and matplotlib are installed, install them if possible, return import status and failed import list '''
    import os, sys
    fail = []
    
    try:
        import numpy
    except:
        try:
            os.system("python -m pip install numpy")
        except:
            fail.append('numpy')
            
    try:
        import scipy
    except:
        try:
            os.system("python -m pip install scipy")
        except:
            fail.append('scipy')
            
    try:
        import pandas
    except:
        try:
            os.system("python -m pip install pandas")
        except:
            fail.append('pandas')
            
    try:
        import matplotlib.pyplot
    except:
        try:
            os.system("python -m pip install matplotlib")
        except:
            fail.append('matplotlib')
    
    return (len(fail)==0), fail


def ask_dir():
    root = Tk()
    root.withdraw()  # Removes TK root window
    # Prompt window to front
    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.lift()
    root.focus_set()
    root.focus_force()
    root.attributes("-topmost", True)

    f_paths = filedialog.askdirectory(title='Please select directory')
    
    root.destroy()
    return f_paths


def ask_files():
    root = Tk()
    root.withdraw()  # Removes TK root window
    # Prompt window to front
    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.lift()
    root.focus_set()
    root.focus_force()
    root.attributes("-topmost", True)

    f_paths = filedialog.askopenfilenames(title='Please select file(s)')
    
    root.destroy()
    return f_paths


def split_path(path):
    return path.split('/')[-1][:-4], path.split('/')[-1][-3:], '/'.join(path.split('/')[:-1])+'/'

      ##########################################

def translate_inv (chann : int) -> int :
    # RadioRoc => PicoTDC channel_matrix
    matrix = [62, 61, 63, 58, 56, 59, 60, 53,
              54, 52, 57, 55, 50, 51, 48, 49, 
              45, 47, 43, 46, 41, 44, 39, 42, 
              37, 40, 35, 38, 33, 36, 27, 34, 
              31, 32, 29, 30, 25, 28, 23, 26, 
              21, 24, 19, 22, 10, 20, 13, 18, 
              11, 17,  8, 16, 14, 15,  1,  3,
               5,  2,  0,  6,  4, 12,  7,  9]
    
    assert chann >=  0
    assert chann <= 63
    for i in range(0, 64) :
        if matrix[i] == chann :
            return i
    assert False
    return -1    


def tot_frame0(value):
    channel =  value >> 27
    leading = (value >> 11) & 0xffff
    TOT = value & 0x7ff
    return [channel, leading, TOT]


def is_pico_header (value : int) -> bool :
    footer_2_bits = (value >>  0) & 0x3
    header_4_bits = (value >> 28) & 0xf
    footer_ok = footer_2_bits == 0
    header_ok = (header_4_bits == 0x8) or (header_4_bits == 0x9)
    return footer_ok and header_ok


def is_pico_trailer (value : int) -> bool :
    footer = (value >>  0) & 0x1
    header = (value >> 28) & 0xf
    return (footer == 0) and (header == 0xa)


def read_in_chunks(file_object, chunk_size=1024):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

      ##########################################

def FWaP(x, y, P, positif=True, filtered=False):
    ''' Return full width at P for positive or negative pulses
        w/o median filtering |!| Linear interpolation |!| '''
    import numpy as np
    from scipy.signal import medfilt
    
    temp_x = x
    if positif:
        temp_y = y
    else:
        temp_y = -y
        P = -P
    
    if filtered:
        temp_y = medfilt(temp_y, kernel_size=15)
        
    list_i_max = np.where(temp_y>P)[0]
        
    if len(list_i_max)==0:
        return 0
        
    i_max = list_i_max[0]
    i_min = i_max - 1
        
    if i_min < 0:
        return 0
        
    i_min = i_max - 1
    y_max = temp_y[i_max]
    y_min = temp_y[i_min]
    x_max = temp_x[i_max]
    x_min = temp_x[i_min]
    
    if y_max == y_min:
        x_l = 0.5*(x_min + x_max)
    else:
        x_l = (P-y_min)*(x_max-x_min)/(y_max-y_min) + x_min
        
    i_min = list_i_max[-1]
    i_max = i_min + 1
    
    if i_max >= len(temp_y):
        return 0
    
    y_max = temp_y[i_max]
    y_min = temp_y[i_min]
    x_max = temp_x[i_max]
    x_min = temp_x[i_min]
    
    if y_max == y_min:
        x_r = 0.5*(x_min + x_max)
    else:
        x_r = (P-y_min)*(x_max-x_min)/(y_max-y_min) + x_min
    
    return x_r - x_l


def shaver(hist, bins):
    offset = len(hist)//5
    
    p_ref = np.where(hist[offset:]==np.max(hist[offset:]))[0][0] + offset
    
    p_init = p_ref
    while p_init>=0:
        p_init -= 780.8/bins
    p_init += 780.8/bins
    
    p_list = np.arange(p_init, len(hist)-1, 780.8/bins, dtype=np.int32)
    
    for p in p_list:
        hist[p] = (hist[p-1]+hist[p+1])/2
    
    return hist


def correct_bin(bins):
    if bins < 5:
        return 3.05
    elif bins < 10:
        return 6.1
    elif bins < 15:
        return 12.2
    elif bins < 30:
        return 24.4
    elif bins < 60:
        return 48.8
    elif bins < 120:
        return 97.6

#################################################################################################################
############# MAIN ##############################################################################################
#################################################################################################################  

PLOT_ON = False
MULTIDIR = False
SHAVING = True
ZOOM_ON_TOA = True
ZOOM_ON_TOT = True
FILT_ON = True
FULL_ON = False
LOG_TOT = True
TOF_ON = True
ERASE_ON = False
ADD_ON = False


if __name__ == '__main__':
    
    if MULTIDIR:
        wdir = 'None'
        paths = []
        while len(wdir) != 0:
            wdir = ask_dir()
            paths += glob.glob(wdir+'/*.bin')
    else:
        paths = ask_files()
    
    if '/$Recycle.Bin' in paths:
        paths.remove('/$Recycle.Bin')
    
    time0 = time.time()
    flag_first = True
    for N, f_path in enumerate(paths):
        
        (TOT, TOF) = (True, True)
        
        f_path = f_path.replace('\\', '/')
        
        f_name, f_type, f_dir = split_path(f_path)
        f_port = int(f_name.split('_')[2])
        
        if len(f_name) < 35:
            print(f_name+' '*(35-len(f_name)))
        
        f_name = '_'.join(f_name.split('_')[3:])
        
        timer = time.time() - time0

        if flag_first:
            print("File {} / {}".format(N+1, len(paths)), end='\r')
            flag_first = False
        elif N < len(paths)-1:
            print("File {} / {} - ETA ~ {} min       ".format(N+1, len(paths), int(timer*(len(paths)-N)/60)), end='\r')
        else:
            print("File {} / {} - ETA ~ {} min       ".format(N+1, len(paths), int(timer*(len(paths)-N)/60)))
        
        time0 = time.time()
        
        for var in f_name.split('_'):
            
            if var[:4] in ['Btot', 'btot', 'tot']:
                f_tot_bin = correct_bin(int(var[4:]))
                
            elif var[:4] in ['Btoa', 'btoa', 'toa']:
                f_toa_bin = correct_bin(int(var[4:]))
                
            elif var[-3:] == 'min':
                f_time = int(var[:-3])
            
            elif var[:3] in ['Thr', 'thr']:
                f_thr = float(var[3:])
                
            elif var[-1] in ['V', 'v']:
                f_bias = float(var[:-1])
            
            elif var == 'X' and TOF_ON:
                TOF = True
                
        
        if f_type == 'bin':            
            data_chans = []
            data_tot = [] 
            data_toa = []
            
            # Optimisation : lecture de tout le fichier en mémoire, puis traitement vectorisé
            with open(f_path, 'rb') as f:
                file_content = f.read()
                n_values = len(file_content) // 4
                # Conversion en tableau numpy d'entiers non signés 32 bits
                values = np.frombuffer(file_content, dtype='<u4', count=n_values)
                # Filtrage des headers, trailers et valeurs invalides
                mask_valid = (~np.vectorize(is_pico_header)(values)) & \
                             (~np.vectorize(is_pico_trailer)(values)) & \
                             (values != 0xFFFFFFFF)
                valid_values = values[mask_valid]
                # Extraction vectorisée des champs
                channels = (valid_values >> 27)
                leading = (valid_values >> 11) & 0xffff
                tot = valid_values & 0x7ff
                # Application du port
                channels = channels + (f_port * 16)
                # Conversion des canaux avec translate_inv (non vectorisable facilement)
                # Création d'une table de correspondance inverse pour translate_inv
                matrix = [62, 61, 63, 58, 56, 59, 60, 53,
                          54, 52, 57, 55, 50, 51, 48, 49, 
                          45, 47, 43, 46, 41, 44, 39, 42, 
                          37, 40, 35, 38, 33, 36, 27, 34, 
                          31, 32, 29, 30, 25, 28, 23, 26, 
                          21, 24, 19, 22, 10, 20, 13, 18, 
                          11, 17,  8, 16, 14, 15,  1,  3,
                           5,  2,  0,  6,  4, 12,  7,  9]

                # Construction du lookup inverse : pour chaque valeur de 0 à 63, donne l'indice dans matrix
                translate_inv_lut = np.zeros(64, dtype=np.uint8)
                for i, val in enumerate(matrix):
                    translate_inv_lut[val] = i

                # Application vectorisée
                data_chans = translate_inv_lut[channels]

                if TOF:
                    data_toa = leading * f_toa_bin
                data_tot = tot * f_tot_bin

                data_chans = np.asarray(data_chans)
                data_tot = np.asarray(data_tot)
                if TOF:
                    data_toa = np.asarray(data_toa)
                else:
                    data_toa = np.zeros_like(data_chans, dtype=np.float64)
                                    
                if len(data_tot) == 0:
                    data_tot = np.zeros(len(data_toa))        
                                
            data = pd.DataFrame(data={'Channel':data_chans,
                                      'TOT':data_tot,
                                      'TOF':data_toa})
            
            del data_chans, data_tot, data_toa
            
            for chan in set(data['Channel']):
                
                temp_data = data.where(data['Channel']==chan)[['TOT', 'TOF']].dropna().reset_index().drop(columns='index')
                
                temp_paths = glob.glob(f_dir+"*.npz")
                
                if len(temp_paths) != 0:
                    for k, p in enumerate(temp_paths):
                        temp_paths[k] = split_path(p.replace('\\', '/'))[0]
                        
                if 'chan{}'.format(chan) in temp_paths:
                    data_chan = np.load(f_dir+'chan{}'.format(chan)+'.npz')
                    temp_npz = []
                    for n in range(len(data_chan.files)-1):
                        temp_npz.append(data_chan[data_chan.files[n+1]])
                        
                    if (f_name in data_chan['name_list']) and ERASE_ON:
                        temp_npz[np.where(data_chan['name_list']==f_name)[0][0]] = temp_data
                        np.savez(f_dir+'chan{}'.format(chan), *temp_npz, name_list=list(data_chan['name_list']))
                    
                    elif (f_name in data_chan['name_list']) and ADD_ON:
                        while f_name in data_chan['name_list']:
                            try:
                                ind = int(f_name.split('_')[-1])
                                f_name = '_'.join(f_name.split('_')[:-1])+str(ind+1)
                            except:
                                f_name = f_name+'_1'
                        np.savez(f_dir+'chan{}'.format(chan), *temp_npz, temp_data, name_list=list(data_chan['name_list'])+[f_name])
                   
                    elif not(f_name in data_chan['name_list']):
                        np.savez(f_dir+'chan{}'.format(chan), *temp_npz, temp_data, name_list=list(data_chan['name_list'])+[f_name])
                    
                    del temp_npz, data_chan
                    
                else:
                    np.savez(f_dir+'chan{}'.format(chan), temp_data, name_list=[f_name])
                
                del temp_data