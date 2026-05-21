# -*- coding: utf-8 -*-
"""
Created on Wed May 21 11:38:49 2025

"""

import os, struct, yaml
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('QtAgg')
import numpy as np
import pandas as pd
#import plotly.graph_objects as go
from enum import Enum, auto

interactive = False

#####################################################################
################## MATRIX ###########################################
#####################################################################

matrix = [62, 61, 63, 58, 56, 59, 60, 53,
          54, 52, 57, 55, 50, 51, 48, 49, 
          45, 47, 43, 46, 41, 44, 39, 42, 
          37, 40, 35, 38, 33, 36, 27, 34, 
          31, 32, 29, 30, 25, 28, 23, 26, 
          21, 24, 19, 22, 10, 20, 13, 18, 
          11, 17,  8, 16, 14, 15,  1,  3,
           5,  2,  0,  6,  4, 12,  7,  9]

def translate (chann : int) -> int :
    assert chann >=  0
    assert chann <= 63
    return matrix[chann]


def translate_str (chann : str) -> int :
    return translate(int(chann))


def translate_inv (chann : int) -> int :
    assert chann >=  0
    assert chann <= 63
    for i in range(0, 64) :
        if matrix[i] == chann :
            return i
    assert False
    return -1


def print_table_normal () -> None :
    print("+-------------------------------------------+")
    print("| Direct table                              |")
    print("+-------------------------------------------+")
    for i in range(0, 16) :
        p0 : str = "|"
        p1 : str = f" {i +  0:2} -> {translate(i +  0):2} |"
        p2 : str = f" {i + 16:2} -> {translate(i + 16):2} |"
        p3 : str = f" {i + 32:2} -> {translate(i + 32):2} |"
        p4 : str = f" {i + 48:2} -> {translate(i + 48):2} |"
        ap : str = p0 + p1 + p2 + p3 + p4
        print(ap)
    print("+-------------------------------------------+")
    return


def print_table_inverse () -> None :
    print("+-------------------------------------------+")
    print("| Inverse table                             |")
    print("+-------------------------------------------+")
    for i in range(0, 16) :
        p0 : str = "|"
        p1 : str = f" {i +  0:2} -> {translate_inv(i +  0):2} |"
        p2 : str = f" {i + 16:2} -> {translate_inv(i + 16):2} |"
        p3 : str = f" {i + 32:2} -> {translate_inv(i + 32):2} |"
        p4 : str = f" {i + 48:2} -> {translate_inv(i + 48):2} |"
        ap : str = p0 + p1 + p2 + p3 + p4
        print(ap)
    print("+-------------------------------------------+")
    return


#####################################################################
################## PLOTTER CLASSES ##################################
#####################################################################

class SaveDataKind (Enum) :
    STAIR = auto()
    RAW   = auto()
    RARE  = auto()
    DEC   = auto()
    COUNT = auto()
    CNT_CH= auto()
    PLOTT = auto()
    

class TimeMeasurement (Enum) :
    TOT = auto()
    TOA = auto()
    

def get_save_name(kind, channel):
    try:
        path = os.getcwd()
        with open(path+'/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        if kind == SaveDataKind.STAIR:
            path += '/' + config['session_name'] + "/DCR/data_str_" + str(translate_inv(channel)) + '_Gain' + str(config['pamp_gain']) + ".txt"
        elif kind == SaveDataKind.PLOTT:
            path += '/' + config['session_name'] + "/DCR/data_str_" + str(translate_inv(channel)) + '_Gain' + str(config['pamp_gain']) + ".png"
        elif kind == SaveDataKind.RAW:
            path += "/data_raw_" + str(channel) + ".txt"
        elif kind == SaveDataKind.RARE:
            path += "/data_rar_" + str(channel) + ".txt"
        elif kind == SaveDataKind.DEC:
            path += "/data_dec_" + str(translate_inv(channel)) + ".txt"
        elif kind == SaveDataKind.COUNT:
            path += "/data_cnt.txt"
        elif kind == SaveDataKind.CNT_CH:
            path += "/data_cnt_per_ch.txt"
        else:
            path += "/failure.txt"
            
    except:        
        path = os.getcwd() + "\\data\\"
        
        if kind == SaveDataKind.STAIR:
            path += "/Staircases/data_str_" + str(translate_inv(channel)) + ".txt"
        elif kind == SaveDataKind.RAW:
            path += "data_raw_" + str(channel) + ".txt"
        elif kind == SaveDataKind.RARE:
            path += "data_rar_" + str(channel) + ".txt"
        elif kind == SaveDataKind.DEC:
            path += "data_dec_" + str(translate_inv(channel)) + ".txt"
        elif kind == SaveDataKind.COUNT:
            path += "data_cnt.txt"
        elif kind == SaveDataKind.CNT_CH:
            path += "data_cnt_per_ch.txt"
        else:
            path += "failure.txt"
    
    return path


class ChannelColors :
    def __init__ (self, lower : int, upper : int) -> None :
        assert upper >= lower
        self.lower : int = lower
        self.upper : int = upper
        chan_range : int = upper - lower + 2
        # With the range being [lower; upper] it includes
        # upper - lower + 1 elements. However, the color
        # map is cyclic, which makes it very hard to
        # visually distinguish between lower and upper.
        # So add another element to the range, which will
        # never be used, but avoids this confusion.
        self.colmap = matplotlib.colormaps["hsv"].resampled(chan_range)
        return
    
    def get_color(self, channel : int) :
        assert channel >= self.lower
        assert channel <= self.upper
        rchan : int = channel - self.lower
        return self.colmap(rchan)


class StaircaseCount :
    def __init__ (self) -> None :
        # This would be better with a set or dictionary
        self.thresh = []
        self.counts = []
        return
    
    def clear (self) -> None :
        self.thresh = []
        self.counts = []
        return
    
    def add (self, thres : int, count : int) -> None :
        # check that the value does not already exist
        for t in self.thresh :
            assert thres != t
        # now add the value
        self.thresh.append(thres)
        self.counts.append(count)
        return
    
    def save (self, channel : int) -> None :
        file_path : str = get_save_name(SaveDataKind.STAIR, channel)
        try:
            f = open(file_path, "w")
        except:
            os.mkdir("./data/Staircases")
            f = open(file_path, "w")
        for i in range(0, len(self.thresh)) :
            f.write(str(self.thresh[i]) + " " + str(self.counts[i]) + "\n")
            pass
        f.close()
        return
    
    def has_data (self, channel : int) -> bool :
        file_path : str = get_save_name(SaveDataKind.STAIR, channel)
        try :
            with open(file_path, 'r') as file :
                return True
        except FileNotFoundError:
            return False
        
    def load (self, channel : int) -> None :
        self.clear()
        file_path : str = get_save_name(SaveDataKind.STAIR, channel)
        try :
            with open(file_path, 'r') as file :
                line = file.readline()
                while line != "" :
                    sline = line.split(" ")
                    thres : int = int(sline[0])
                    count : int = int(sline[1])
                    self.add(thres, count)
                    line = file.readline()
                    pass
                pass
        except FileNotFoundError:
            if interactive:
                print("Skipped " + file_path)
        return
    
    def plot (self, channel : int, color, canvas) -> None :
        plt.cla()
        assert len(self.thresh) == len(self.counts)
        if len(self.thresh) == 0 :
            return
        label = "channel " + str(translate_inv(channel))
        if interactive:
            print(f"the channel for the first SC {label}")
        plt.plot(self.thresh,
                 self.counts, 
                 '-',
                 label=label)
        plt.legend()
        #canvas.draw()
        return
    
    def plot_grid (self, canvas) -> None :
        #canvas.axes.cla()
        #canvas.axes.grid(True)
        #canvas.axes.set_yscale("log")
        #canvas.draw()
        plt.grid(True)
        plt.yscale("log")
        #plt.show()
        #canvas.draw()
        return
    
    def plot_save (self, channel : int, canvas) -> None :
        file_path : str = get_save_name(SaveDataKind.PLOTT, channel)
        try:
            plt.savefig(file_path)
        except FileNotFoundError:
            # doesn’t exist
            if interactive:
                print("[INFO] Folder not found to save staircase.")
            os.mkdir("data/Staircases/")
            plt.savefig("data/Staircases/data_str_" + str(translate_inv(channel)) + ".png")
        return
    

class StaircaseSuperposition :
    def __init__ (self, lower : int, upper : int) -> None :
        assert lower <= upper
        assert lower >= 0
        assert upper <= 63
        self.chosen = []
        for i in range(lower, upper + 1) :
            self.chosen.append(i)
        self.stair = StaircaseCount()
        return
    
    def exclude (self, channel : int) -> None :
        try :
            self.chosen.remove(channel)
        except ValueError :
            # It is not an error to exclude a channel that
            # had not been included in the first place (but
            # it is a nop).
            return
        return
    
    def load_and_plot (self) -> None :
        exist = []
        # Find how many staircases really exist
        for i in self.chosen :
            if self.stair.has_data(i) :
                exist.append(i)
                pass
            pass
        cc : ChannelColors = ChannelColors(0, len(exist))
        for i in range(0, len(exist)) :
            self.stair.clear()
            self.stair.load(exist[i])
            self.stair.plot(exist[i], cc.get_color(i))
            pass
        self.stair.plot_grid()
        return
    

class ChannelCount :
    def __init__ (self) -> None :
        self.values     = []
        self.tot_counts = []
        self.toa_counts = []
        return
    
    def clear (self) -> None :
        self.values     = []
        self.tot_counts = []
        self.toa_counts = []
        return
    
    def add (self, trg, ntrg, value : int, count : int) -> None :
        vlen : int = len(self.values)
        assert vlen == len(trg)
        assert vlen == len(ntrg)
        for i in range(0, vlen) :
            if value == self.values[i] :
                # The value has already been found
                trg[i] += count
                return
            pass
        # The value has not been found
        self.values.append(value)
        trg.append(count)
        ntrg.append(0)
        return
    
    def add_tot (self, value : int, count=1) -> None :
        self.add(self.tot_counts, self.toa_counts, value, count)
        return
    
    def add_toa (self, value : int, count=1) -> None :
        self.add(self.toa_counts, self.tot_counts, value, count)
        return
    
    def load (self, channel : int) -> bool:
        self.clear()
        file_path = get_save_name(SaveDataKind.DEC, channel)
        try :
            with open(file_path, 'r') as file :
                line = file.readline()
                while line != "" :
                    sline = line.split(" ")
                    value : int = int(sline[0])
                    totcn : int = int(sline[1])
                    toacn : int = int(sline[2])
                    self.add_tot(value, totcn)
                    self.add_toa(value, toacn)
                    line = file.readline()
                    pass
                pass
        except FileNotFoundError:
            return False
        return True
    
    def save (self, channel : int) :
        if not self.has_data() :
            return
        merged_data = ChannelCount()
        merged_data.load(channel)
        for i in range(0, len(self.values)) :
            merged_data.add_tot(self.values[i], self.tot_counts[i])
            merged_data.add_toa(self.values[i], self.toa_counts[i])
            pass
        file_path = get_save_name(SaveDataKind.DEC, channel)
        f = open(file_path, "w")
        for i in range(0, len(merged_data.values)) :
            f.write(str(merged_data.values[i]) + " " + str(merged_data.tot_counts[i]) + " " + str(merged_data.toa_counts[i]) + "\n")
            pass
        f.close()
        return
    
    def has_data (self) -> bool :
        return len(self.values) != 0
    
    def plot (self, counts, channel : int, binning : int, color, canvas, is_tot: bool) -> None :
        self.load(channel)
        if not self.has_data() :
            return
        fvalues = []
        fcounts = []
        svalues = 0
        scounts = 0
        for i in range(0, len(self.values)) :
            if counts[i] != 0 :
                fvalues.append(self.values[i] * binning)
                fcounts.append(counts[i])
                svalues += 1
                scounts += counts[i]
                pass
            pass
        stats : str = "{0:.2e}/{1:}".format(scounts, svalues)
        label : str = "channel " + str(translate_inv(channel)) + " " + stats
        #canvas.axes.bar
        canvas.axes.bar(fvalues,
                fcounts,
                label=label,
                color=color,
                align="edge",
                width=binning,
                alpha=0.5)
        if(is_tot):
            canvas.axes.set_title("TOT")
        else:   
            canvas.axes.set_title("TOA")
        return
    
    def plot_tot (self, channel : int, binning : int, color, canvas) -> None :
        self.plot(self.tot_counts, channel, binning, color, canvas, True)
        return
    
    def plot_toa (self, channel : int, binning : int, color, canvas) -> None :
        self.plot(self.toa_counts, channel, binning, color, canvas, False)
        return
    

class AsicCount :
    def __init__ (self) -> None :
        self.colors   = ChannelColors(0, 63)
        self.channels = []
        for i in range(0, 64) :
            ch = ChannelCount()
            self.channels.append(ch)
        return
    
    def clear (self) -> None :
        for c in self.channels :
            c.clear()
        return
    
    def add_tot (self, channel : int, value) -> None :
        assert channel >= 0
        assert channel < 64
        self.channels[channel].add_tot(value)
        return
    def add_toa (self, channel : int, value) -> None :
        assert channel >= 0
        assert channel < 64
        self.channels[channel].add_toa(value)
        return
    
    def load (self) -> None :
        bmap = 0
        for i in range(0, 64) :
            res : bool = self.channels[i].load(i)
            if res :
                bmap = bmap | (1 << i)
                pass
            pass
        q3 : str = "{0:04x}".format(((bmap >> 48) & 0xffff))
        q2 : str = "{0:04x}".format(((bmap >> 32) & 0xffff))
        q1 : str = "{0:04x}".format(((bmap >> 16) & 0xffff))
        q0 : str = "{0:04x}".format(((bmap >> 00) & 0xffff))
        if interactive:
            print("+------------------------+")
            print("|63|" + q3 + "|" + q2 + "|" + q1 + "|" + q0 + "|0|")
            print("+------------------------+")
        return
    
    def save (self) -> None :
        for i in range(0, 64) :
            self.channels[i].save(i)
        return
    
    def plot (self, msr : TimeMeasurement, binning : int, canvas) -> None :
        canvas.axes.cla()
        canvas.axes.set_aspect('auto')
        exist = []
        for i in range(0, 64) :
            self.channels[i].load(i)
            if self.channels[i].has_data() :
                exist.append(i)
                pass
            pass
        if len(exist) == 0 :
            if interactive:
                print("No channel has data.")
            return
        self.colors = ChannelColors(0, len(exist))
        for i in range(0, len(exist)):
            chan = exist[i]
            if msr == TimeMeasurement.TOT:
                self.channels[chan].plot_tot(chan, binning, self.colors.get_color(i), canvas)
            elif msr == TimeMeasurement.TOA:
                self.channels[chan].plot_toa(chan, binning, self.colors.get_color(i), canvas)
            else:
                if interactive:
                    print("Invalid plot type.")
        ax = canvas.axes
        ax.axes.legend()
        ax.axes.set_xlabel("Values (ps)")
        ax.axes.set_ylabel("count")
        ax.axes.grid(True)
        canvas.draw()
        return
    
    def plot_tot (self, binning : int, canvas) -> None :
        self.plot(TimeMeasurement.TOT, binning, canvas)
        return
    
    def plot_toa (self, binning : int, canvas) -> None :
        self.plot(TimeMeasurement.TOA, binning, canvas)
        return
    
    def clear_port (self, port_number : int) -> None :
        assert port_number >= 0
        assert port_number <  4
        bound_lower : int = (port_number    ) * 16
        bound_upper : int = (port_number + 1) * 16
        for i in range(bound_lower, bound_upper) :
            self.channels[i].clear()
        return
    
    def save_port (self, port_number : int) -> None :
        assert port_number >= 0
        assert port_number <  4
        bound_lower : int = (port_number    ) * 16
        bound_upper : int = (port_number + 1) * 16
        for i in range(bound_lower, bound_upper) :
            self.channels[i].save(i)
        return
    
    def counts_plotter(canvas):
        canvas.axes.cla()
        canvas.axes.set_aspect('auto')
        # Lire les données depuis le fichier
        file_name = './data/data_cnt.txt'
        data = []
        try:
            with open(file_name, 'r') as file:
                for line in file:
                    line = line.strip().split(', ')
                    # Ignorer la quatrième colonne contenant les valeurs entre crochets
                    data.append(line[:3])
        except:
            if interactive:
                print("File Not Found !")
            return
        # Convertir les chaînes de caractères en entiers
        data = [[int(entry[0]), int(entry[1]), int(entry[2])] for entry in data]

        # Création d'un dictionnaire pour regrouper les troisièmes éléments par les deuxièmes éléments identiques
        grouped_data = {}
        for entry in data:
            key = entry[1]
            value = [entry[0], entry[2]]
            if key in grouped_data:
                grouped_data[key].append(value)
            else:
                grouped_data[key] = [value]

        # Création du plot
        for key, values in grouped_data.items():
            #x = [val[0] for val in values]
            y = [val[1] for val in values]
            x = range(len(values))
            #canvas.axes.plot(x, y, marker='o', label=f"PORT {key}")  # Utilisation de markers pour les points
            canvas.axes.plot(x, y, linestyle='--')  # Utilisation de linestyle pour les tirets


        canvas.axes.set_xlabel('Hit_count')
        canvas.axes.set_ylabel('Events')
        canvas.axes.set_title('Counting Per Port')
        canvas.axes.legend()
        canvas.axes.grid(True)
        canvas.draw()

    def counting_per_channel(canvas):
        canvas.axes.cla()
        canvas.axes.set_aspect('auto')

        file_name = get_save_name(SaveDataKind.CNT_CH, 0)
        sum_line = np.zeros((8, 8), dtype=int)  # Création d'une matrice de sommes initiale
        try:
            with open(file_name, 'r') as file:
                for idx, line in enumerate(file):
                    #line = line.strip()
                    #start_index = line.find('[')
                    #end_index = line.find(']')
                    #list_part = line[start_index:end_index + 1]
                    #data_list = eval(list_part)
                    data_list = eval(line)
                    if len(data_list) == 64:
                        sum_line += np.array(data_list).reshape((8, 8))

                    else:
                        if interactive:
                            print(f"Line {idx + 1} does not contain 64 elements and will be ignored.")

            #canvas.axes.imshow(sum_line, cmap='Blues', interpolation='nearest')
            canvas.axes.imshow(sum_line, interpolation='nearest')
            # Ajout des bordures entre les cellules
            #canvas.colorbar(sum_line)
            for i in range(8):
                for j in range(8):
                    canvas.axes.text(j, i, f'ch: {i*8+j}', ha='center', va='bottom', color='white', fontsize=8)
                    canvas.axes.text(j, i, str(sum_line[i, j]), ha='center', va='top', color='black')

            canvas.axes.set_xlabel('X')
            canvas.axes.set_ylabel('Y')
            canvas.axes.set_title('Count Per Channel')
            canvas.draw()
        except:
            if interactive:
                print("Error counting file not found \n")
            

#####################################################################
################## PLOTTER ##########################################
#####################################################################            
                     
class PicoTrailer :
    def __init__ (self, eid : int, hit : int, ovr : bool) -> None :
        self.event_id  = eid
        self.hit_count = hit
        self.overflow  = ovr
        return
    
class TotSum:
    def __init__ (self) -> None :
        self.values = [0]*64
    def add_totsum(self, index, val_incr):
        if 0 <= index < 64:
            self.values[index] += val_incr
        else:
            if interactive:
                print("Error Sum TOT Channel not Found")
    def get_totsum(self):
        return self.values
    
    def clear_totsum(self):
        self.values = [0]*64
        
class PicoTdc0 :
    def __init__ (self, channel : int, leading : int, tot : int) -> None :
        self.channel = channel
        self.leading = leading
        self.tot     = tot
        return

def tot_frame0(value):
    channel =  value >> 27
    # todo debug to deal with broken (?) msb
    #leading = (value >> 11) & 0xffff
    #TOT = value & 0x7ff
    leading = (value >> 11) & 0xffff
    TOT = value & 0x7ff
    return [channel, leading, TOT]


def tot_frame1(value):
    channel =  value >> 27
    leading = (value >> 8) & 0x7ffff
    TOT = value & 0xff
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

def extract_pico_trailer (value : int) -> PicoTrailer :
    ovf : int  = (value >> 1) & 0x1
    ovr : bool = (ovf == 1)
    hit : int  = (value >>  2) & 0x1fff
    eid : int  = (value >> 15) & 0x1fff
    return PicoTrailer(eid, hit, ovr)

def extract_pico_tdc_0 (value : int) -> PicoTdc0 :
    tot     : int = (value >>  0) & 0x7ff
    leading : int = (value >> 11) & 0xffff
    channel : int = (value >> 27) & 0xf
    return PicoTdc0(channel, leading, tot)

def extract_pico_coarse_count(value: int):
    return (value >> 2) & 0x1FFF

def save_raw(data, ports) -> None:
   file_paths = {i: get_save_name(SaveDataKind.RAW, i) for i in range(4)}
   files = {key: open(file_paths[key], "a") for key in file_paths.keys()}
   try:
    port_nmbr = ports[0]
   except:
       if interactive:
           print("Need To Enable At Least One Port.")
   for i in range(0, len(data)):
        if (data[i] >> 8) == 0xf0f0f0:
            port_nmbr = data[i] & 0xFF
        else:
            files[port_nmbr].write("0x{:08x}\n".format(data[i]))


   for file in files.values():
       file.close()
   return

def save_rare (data, ports, bin_tot, bin_toa) -> None :
    # not quite raw
    #port_nmbr = channel // 16
    port_nmbr = ports[0]
    file_paths = {i: get_save_name(SaveDataKind.RARE, i) for i in range(4)}
    f = {key: open(file_paths[key], "a") for key in file_paths.keys()}
    for i in range(0, len(data)):
        if (data[i] >> 8) == 0xf0f0f0:
           port_nmbr = data[i] & 0xFF
        else:
            value_raw = data[i]
            extracted_all = tot_frame0(value_raw)
            extracted_chn = extracted_all[0] + (port_nmbr * 16)
            extracted_toa = extracted_all[1]
            extracted_tot = extracted_all[2]
            sline0 = str(i) + " "
            sline1 = str(extracted_chn) + " "
            sline2 = str(extracted_tot * bin_tot) + " "
            sline3 = str(extracted_toa * bin_toa) + "\n"
            f[port_nmbr].write(sline0 + sline1 + sline2 + sline3)
        pass
    for file in f.values():
       file.close()
    return

def ethernet_data_remove_sentinels (data) :
    clean_data = []
    for unclean_value in data :
        if unclean_value == 0xFFFFFFFF or unclean_value == 0xd0d0d0d0:
            # get rid of this
            pass
        else :
            # this is clean
            clean_data.append(unclean_value)
            pass
    return clean_data

class FrameCount :
    def __init__ (self) -> None :
        self.counts = []
        for i in range(0, 64) :
            self.counts.append(0)
            pass
        return
    def clear (self) -> None :
        for i in range(0, 64) :
            self.counts[i] = 0
            pass
        return
    def add (self, chan : int) -> None :
        assert chan >= 0
        assert chan <= 63
        self.counts[chan] += 1
        return
    def __repr__ (self) -> None :
        ret = self.counts  
        #for i in range(0, 4) :
        #    ret += "|"
        #    ret += " {0:2d} : {1:3d} |".format(i +  0, self.counts[i +  0])
        #    ret += " {0:2d} : {1:3d} |".format(i +  4, self.counts[i +  4])
        #    ret += " {0:2d} : {1:3d} |".format(i +  8, self.counts[i +  8])
        #    ret += " {0:2d} : {1:3d} |".format(i + 12, self.counts[i + 12])
        #    ret += "\n"
        #    pass
        return ret

def ethernet_data_count_frames (data, window : int) :
    clean_data      = []
    frame_data      = []
    sum_TOT = TotSum()
    leading_raw_data= []
    coarse_count    = 0
    file_path = get_save_name(SaveDataKind.COUNT, 0)
    fp_count_channel = get_save_name(SaveDataKind.CNT_CH, 0)
    f = open(file_path, "a")
    f_cnt_ch = open(fp_count_channel, "a")
    prev_separator = 0
    #if(os.stat(file_path).st_size == 0):
    #    f.write(f"event_id, port_numb, hit_count, coarse_counter, tot_sum, first_toa")
    port_numbr = 0
    for raw_data in data :
        if is_pico_header(raw_data) == True :
            if(raw_data >>28 !=  0xf):
                coarse_count = extract_pico_coarse_count(raw_data)
                leading_raw_data = []
                sum_TOT.clear_totsum()
            else:
                break
        elif is_pico_trailer(raw_data):
            counts = FrameCount()
            for datum in frame_data :
                if(datum >> 28 !=  0xf):
                    tdc0 = extract_pico_tdc_0(datum)
                    channel_ = translate_inv(tdc0.channel + (port_nmbr * 16))
                    counts.add(channel_)
                    leading_raw_data.append(tdc0.leading)
                    #sum_TOT = sum_TOT + tdc0.tot
                    sum_TOT.add_totsum(channel_, tdc0.tot)
                else:
                    break
            trail = extract_pico_trailer(raw_data)
            if(len(leading_raw_data)):
                f.write(f"[{trail.event_id}, {port_nmbr}, {trail.hit_count}, {coarse_count}, {sum_TOT.get_totsum()}, {leading_raw_data[0]}]\n")            
            else:
                f.write(f"[{trail.event_id}, {port_nmbr}, {trail.hit_count}, {coarse_count}, {sum_TOT.get_totsum()}, 0]\n")
            
            f_cnt_ch.write(f"{counts.counts}\n")         
            # print(str(counts))
            # Concatenate new frame on old data
            clean_data += frame_data
            frame_data.clear()
        else :
            if ((raw_data >> 8) == 0xf0f0f0):
                port_nmbr = raw_data & 0xFF
                frame_data = []
                frame_data.append(raw_data)
            else:
                frame_data.append(raw_data)
    if len(frame_data) != 0 :
        # Partial frame, keep it in the data,
        # but it will not be properly counted.
        if interactive:
            print("And a partial frame.")
        # Concatenate new frame on old data
        clean_data += frame_data
        pass
    f.close()
    f_cnt_ch.close()
    return clean_data


def sort_channels(data, ports):
    count : AsicCount = AsicCount()
    port_nmbr = ports[0]
    for port in ports:
        for i in range(0, len(data)):
            if (data[i] >> 8) == 0xf0f0f0:
                port_nmbr = data[i] & 0xFF
            elif port_nmbr == port:
                port_base   : int = port_nmbr * 16
                extracted_all = tot_frame0(data[i])
                extracted_chn = extracted_all[0]
                extracted_toa = extracted_all[1]
                extracted_tot = extracted_all[2]
                #print("Data : " + hex(value_raw) + " -> " + str(extracted_chn))
                channel_ = port_base + extracted_chn
                count.add_tot(channel_, extracted_tot)
                count.add_toa(channel_, extracted_toa)
        if interactive:
            print("save port ", port)
        count.save_port(port)

def filter_ethernet_data (data, ports : int, bin_tot: int, bin_toa: int, window: int) :
    save_raw(data, ports=ports)
    #port_number : int = channel // 16
    #port_base   : int = port_number * 16
    # filter 1 : remove dummy data
    clean_data = ethernet_data_remove_sentinels(data)
    if interactive:
        print("Clean data : " + str(len(clean_data)) + "/" + str(len(data)))
    len_raw = len(data)
    len_clean = len(clean_data)
    # filter 2 : count frames, remove headers and trailers
    clean_data = ethernet_data_count_frames(clean_data, window)
    save_rare(clean_data, ports, bin_tot, bin_toa)
    # filter 2 : sort channels
    sort_channels(clean_data, ports=ports)
    return [len_clean,len_raw]

def plot_staircase (buffer, channel : int, canvas) -> None :
    count = StaircaseCount()
    nlen : int = len(buffer) - 1
    assert nlen > 2
    # Every once in a while, the response to the staircase
    # request is a bit slow, and as a result, it is inside
    # the buffer containing the read data.
    # If that is the case, skip the first datum.
    print(buffer[0])
    bidx : int = 0
    if (buffer[0] == "0") or (buffer[0] == "1") :
        bidx = 1
    assert buffer[bidx] == "Start Staircase acquisition"
    assert buffer[nlen] == "End Staircase acquisition"
    nbuffer = buffer[bidx + 1:nlen]
    for data in nbuffer :
        th : int = int(data.split(",")[0])
        cn : int = int(data.split(",")[1])
        count.add(th, cn)
        pass
    cc : ChannelColors = ChannelColors(channel, channel)
    count.save(channel)
    #count.plot(channel, cc.get_color(channel), canvas)
    #count.plot_grid(canvas)
    #count.plot_save(channel, canvas)
    return

def plot_tot (binning : int, canvas) -> None :
    count = AsicCount()
    count.load()
    count.plot_tot(binning, canvas)
    return

def plot_toa (binning : int, canvas) -> None :
    count = AsicCount()
    count.load()
    count.plot_toa(binning, canvas)
    return

def plot_counts(canvas):
   #AsicCount.counts_plotter(canvas)
    AsicCount.counting_per_channel(canvas=canvas)
    
def plot_tot_sum(canvas, binning):
    canvas.axes.cla()
    canvas.axes.set_aspect('auto')
    file_path = get_save_name(SaveDataKind.COUNT, 0)
    non_zero_values = [[] for _ in range(64)]  
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            row = eval(line)
            for col_index, value in enumerate(row[4]):
                if value != 0:
                    non_zero_values[col_index].append(value * binning)

    for col_index, values in enumerate(non_zero_values):
        if len(values) > 0:
            canvas.axes.hist(values, bins=100, edgecolor='black', alpha=0.7, label=f'channel {col_index}')
    canvas.axes.set_xlabel('Values  (ps)')
    canvas.axes.set_ylabel('Count')
    canvas.axes.set_title('Sum Of TOT')
    canvas.axes.legend()
    canvas.axes.grid(True)
    canvas.draw()

def read_in_chunks(file_object, chunk_size=1024):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

def read_in_chunks(file_object, chunk_size=1024):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data

def read_bin_and_save_rare(port_readout, bin_tot, bin_toa):
    ports_to_process = []
    for port in port_readout:
        ports_to_process.append(port)

    bin_files = {indx: f"./data/data_section_{indx}.bin" for indx in ports_to_process}
    file_paths = {indx: f"./data/data_rar_{indx}.txt" for indx in ports_to_process}
    files = {indx: open(file_paths[indx], "w") for indx in ports_to_process}
    for port_nmbr in ports_to_process:
        index = 0
        if interactive:
            print(f"Processing port {port_nmbr}")
            print(f"Opening file: {bin_files[port_nmbr]}")
        
        with open(bin_files[port_nmbr], 'rb') as f:
            for chunk in read_in_chunks(f):
                #print(f"Read chunk of size: {len(chunk)}")
                for i in range(0, len(chunk), 4):
                    octets = chunk[i:i+4]
                    if len(octets) == 4:
                        value = struct.unpack('<I', octets)[0]
                        if not is_pico_header(value) and not is_pico_trailer(value) and value != 0xFFFFFFFF:
                            extracted = tot_frame0(value)    
                            channel = matrix.translate_inv(extracted[0] + (port_nmbr * 16))
                            toa = extracted[1] 
                            tot = extracted[2]
                            line = str(f"{index} {channel} {tot * bin_tot} {toa * bin_toa}\n")
                            files[port_nmbr].write(line)
                            index += 1
    
    for f in files.values():
        f.close()

def plot_multi(port_readout : list, bin_tot : int, bin_toa : int):   #binning of picoTDC in ps
    read_bin_and_save_rare(port_readout, bin_tot, bin_toa)
    data = []
    try: 
        for port in port_readout:
            data.append(pd.read_csv(f'.//data//data_rar_{port}.txt', skipfooter=0, delim_whitespace=True, names=['ID', 'Channel', 'TOT', 'TOA']))  # Update delimiter as needed
        data = pd.concat(data)
    except:
        if interactive:
            print("Files not Found !")
        return
    
    # Create two figures
    fig_tot = go.Figure()
    fig_toa = go.Figure()

    # Get a list of unique channels
    channels = data['Channel'].unique()


    # Add histograms for each channel to each plot
    for channel in channels:
        filtered_data = data[data['Channel'] == channel]
        
        # Add TOT histogram
        fig_tot.add_trace(
            go.Histogram(x=filtered_data['TOT'], 
                         name=f'Channel {channel}')
        )
        
        # Add TOA histogram
        fig_toa.add_trace(
            go.Histogram(x=filtered_data['TOA'], 
                         name=f'Channel {channel}',
                         xbins=dict( start=data['TOA'].min(),
                            end=data['TOA'].max(), 
                            size=80
                        ))
        )

    # Update layouts
    fig_tot.update_layout(
        title="TOT Histograms for All Channels",
        xaxis_title="TOT(Ps)",
        yaxis_title="Frequency",
        barmode='overlay'  # Set bar mode to overlay for better visualization
    )
    fig_tot.update_traces(opacity=0.75)  # Set opacity to see overlapping bars

    fig_toa.update_layout(
        title="TOA Histograms for All Channels",
        xaxis_title="TOA(Ps)",
        yaxis_title="Frequency",
        barmode='overlay'  # Set bar mode to overlay for better visualization
    )
    fig_toa.update_traces(opacity=0.75)  # Set opacity to see overlapping bars

    # Enable legend interaction to toggle traces
    fig_tot.update_layout(showlegend=True)
    fig_toa.update_layout(showlegend=True)

    # Show the figures
    fig_tot.show()
    fig_toa.show()
    
if __name__ == "__main__":
    
    ports_to_process = [2]
    bin_tot = 49
    bin_toa = 12
    interactive = True

    bin_files = ["E:/amaury/dataWeeroc/data_25_sept/measurment1/MatriceMeasurements_Hamamatsu_58.5/data_section_2_Btot49_Btoa12_Gain8_Thr290_58.5V_1min.bin"]
    file_paths = ["E:/amaury/dataWeeroc/data_25_sept/measurment1/MatriceMeasurements_Hamamatsu_58.5/data_section_2_Btot49_Btoa12_Gain8_Thr290_58.5V_1min.txt"]
    
    files = {idx: open(file, "w") for idx, file in enumerate(file_paths)}
    for index, port_nmbr in enumerate(ports_to_process):
        if interactive:
            print(f"Processing port {port_nmbr}")
            print(f"Opening file: {bin_files[index]}")
        
        with open(bin_files[index], 'rb') as f:
            for chunk in read_in_chunks(f):
                #print(f"Read chunk of size: {len(chunk)}")
                for i in range(0, len(chunk), 4):
                    octets = chunk[i:i+4]
                    if len(octets) == 4:
                        value = struct.unpack('<I', octets)[0]
                        if not is_pico_header(value) and not is_pico_trailer(value) and value != 0xFFFFFFFF:
                            extracted = tot_frame0(value)    
                            channel = matrix.translate_inv(extracted[0] + (port_nmbr * 16))
                            toa = extracted[1] 
                            tot = extracted[2]
                            line = str(f"{index} {channel} {tot * bin_tot} {toa * bin_toa}\n")
                            files[index].write(line)
    
    for f in files.values():
        print(f"Wrote in file : {f.name}")
        f.close()