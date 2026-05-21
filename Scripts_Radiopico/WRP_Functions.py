# -*- coding: utf-8 -*-
"""
Created on Thu May 22 09:26:22 2025

"""

import time, os
import argparse
import pandas as pd
import subprocess
import yaml
from tkinter import Tk, filedialog, simpledialog, messagebox

from .WRP_Classes import PicoTDC 
from .WRP_Classes import Measurements 
from . import WRP_Device as WRP_Device
from . import WRP_I2C as radio_i2c
from .WRP_Device import *


CONFIG_PATH = "./config.yaml"
I2C_DEFAULT_PATH = "./radio_default_i2c.csv"

interactive = False


#####################################################################
################## Base #############################################
#####################################################################


def check_data_folder():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("data/Staircases"):
        os.makedirs("data/Staircases")


def ping_ip_address(ip_address):
    try:
        command = ['ping', ip_address]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        if interactive:
            print(f"Ping to {ip_address} successful!")
            print(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        if interactive:
            print(f"Ping to {ip_address} failed!")
            print(e.stderr)
        return False
    except FileNotFoundError:
        if interactive:
            print("Error: 'ping' command not found.")
        return False
    

def load_i2c_defaults(path):
    return pd.read_csv(path, index_col=None, dtype={"add": int, "subadd": int, "data": str})


def startup_sequence(pico_tdc, i2c_module):
    i2c_module.update_from_dataframe(i2c_module.df_i2c)
    radio_set_val_evnt(True)
    radio_set_threshold(400)
    radio_set_patgain(8)
    pico_tdc.set_bin_tot(12)
    pico_tdc.set_bin_toa(12)
    

class MeasurementManager:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.devices = []
        self.measurements = []

    def load_config(self, path):
        if type(path) == dict:
            return path
        else:
            with open(path, 'r') as f:
                return yaml.safe_load(f)

    def setup_devices(self):
        for dev_conf in self.config.get("devices", []):
            serial_dev = WRP_Device.connect(dev_conf["serial_port"], dev_conf["ip"])
            pico_tdc = PicoTDC(WRP_Device.dev)
            if(os.path.exists(self.config['devices'][0]['i2c_defaults'])):
                radio_i2c.df_i2c = load_i2c_defaults(self.config['devices'][0]['i2c_defaults'])
            else:
                print(f"Warning: I2C defaults file not found at {os.path.abspath(self.config['devices'][0]['i2c_defaults'])}.")
                exit(1)

            setup_sequence(self.config, pico_tdc, radio_i2c)
            self.devices.append({"serial": serial_dev, "tdc": pico_tdc})

    def run_measurements(self):
        for dev in self.devices:
            if self.config["measurement_config"]:
                meas = Measurements(dev["serial"], dev["tdc"])
                meas.load_config(self.config.get("measurement_config", CONFIG_PATH))
            else:
                meas = Measurements(dev["serial"], dev["tdc"], self.config)
            meas.start_measure()
            self.measurements.append(meas)

    def wait_for_completion(self, timeout=6000):
        start = time.time()
        try:
            while any(m.daq_running for m in self.measurements):
                if time.time() - start > timeout:
                    if interactive:
                        print("Timeout d'attente des mesures dépassé.")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            if interactive:
                print("Stopping all measurements...")
            for m in self.measurements:
                m.stop_measurement()
                

def main():
    parser = argparse.ArgumentParser(description='Run PicoTDC measurements using YAML configuration')
    parser.add_argument('--config', default=CONFIG_PATH, help='YAML configuration file')
    args = parser.parse_args()

    check_data_folder()

    manager = MeasurementManager(args.config)
    manager.setup_devices()

    for dev_conf in manager.config.get("devices", []):
        ip = dev_conf["ip"]
        if not ping_ip_address(ip):
            if interactive:
                print(f"Device at {ip} not reachable, skipping.")
            continue

    manager.run_measurements()
    manager.wait_for_completion()

    #plot tot toa from the binary files
    #WRP_Plotter.plot_multi([0,1,2,3], bin_toa=12, bin_tot=12)
    
    
#####################################################################
################## Custom ###########################################
#####################################################################

def setup_sequence(dict_config, pico_tdc, i2c_module):
    i2c_module.update_from_dataframe(i2c_module.df_i2c)
    radio_set_val_evnt(True)
    if dict_config['measurement_type'] == 'DAQ':
        pico_tdc.config_control_trigger_mode(True, 325, 300)
        pico_tdc.config_control_trigger_clock(dict_config['daq']['frequency'], 0, 300)
        radio_set_threshold(dict_config['daq']['thresholds'])
    radio_set_patgain(dict_config['pamp_gain'])
    pico_tdc.set_bin_tot(dict_config['bin_size']['bin_tot'])
    pico_tdc.set_bin_toa(dict_config['bin_size']['bin_toa'])
    
    
def folder_management(dict_config):
    if (dict_config['wdir'] != '') and (dict_config['wdir'] != os.getcwd()):
        os.chdir(dict_config['wdir'])
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(dict_config, f, default_flow_style=False)
        
    if (dict_config['session_name'] != '') and not os.path.exists(dict_config['session_name']):
        os.makedirs(dict_config['session_name'])
        if not os.path.exists(dict_config['session_name'] + "/DCR"):
            os.makedirs(dict_config['session_name'] + "/DCR")
        return True
    elif os.path.exists(dict_config['session_name']):
        if UI_message('ask', "Already existing session name, continue ?"):
            return True
        else:
            return False
    

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

    f_paths = filedialog.askdirectory(title='Please select working directory')
    
    root.destroy()
    return f_paths    


def ask_i2cfile():
    root = Tk()
    root.withdraw()  # Removes TK root window
    # Prompt window to front
    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.lift()
    root.focus_set()
    root.focus_force()
    root.attributes("-topmost", True)

    f_path = filedialog.askopenfilename(title="Please select 'radio_default_i2c.csv'", filetypes=[("csv config file",".csv")])
    
    root.destroy()
    return f_path   

    
def ask_str(titre):
    root = Tk()
    root.withdraw()  # Removes TK root window
    # Prompt window to front
    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.lift()
    root.focus_set()
    root.focus_force()
    root.attributes("-topmost", True)

    f_string = simpledialog.askstring(titre, titre)
    
    root.destroy()
    return f_string


def UI_message(titre, message):
    root = Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.lift()
    root.focus_set()
    root.focus_force()
    root.attributes("-topmost", True)
    
    if titre == 'error':
        temp = messagebox.showwarning(titre, message)
        root.destroy()
    elif titre == 'info':
        temp = messagebox.showinfo(titre, message)
        root.destroy()
    elif titre == 'ask':
        ask = messagebox.askokcancel(titre, message)
        root.destroy()
        return ask