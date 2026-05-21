# -*- coding: utf-8 -*-
"""
Created on Fri May 23 09:15:01 2025

"""

import os, sys
import time
import yaml


from .WRP_Functions import *


if __name__ == "__main__":
    interactive = False

    dict_config = {'devices': [{'serial_port': 'COM6', 'ip': '192.168.1.10', 
                                'i2c_defaults': "C:/Users/wateb/USherbrooke/Romain Espagnet - Mesure_partage/PhD_G_Lemaire/Scripts_Radiopico/radiodefault_i2c.csv"}],
                'bin_size': {'bin_toa': 3, 'bin_tot': 49},
                'pamp_gain': [8],
                'list_gain': [],
                'measurement_config': 0,
                'measurement_type': 'DCR',
                'wdir': './',
                'session_name': 'MyMeasurementSession',
                'channels': [48],
                'Vbias': 58,
                'dcr': {'start_threshold': 100, 'stop_threshold': 600, 'step': 3},
                'daq': {'thresholds': [300], 'list_thr': [], 'duration': 60, 'frequency': 100000}
                }

    ##########################################################################

    dict_config['wdir'] = ask_dir() + '/'

    if not os.path.exists(dict_config['devices'][0]['i2c_defaults']):
        temp = ask_i2cfile()
        if len(temp)==0 or temp[-21:] != "radio_default_i2c.csv":
            sys.exit("'radio_default_i2c.csv' file missing")
        else:
            dict_config['devices'][0]['i2c_defaults'] = temp

    dict_config['session_name'] = ask_str("Name of the measurement session")

    if not folder_management(dict_config):
        dict_config['session_name'] = ask_str("Name of the measurement session")
        if not folder_management(dict_config):
            sys.exit("Check your files and come back later")

    type_mesure = ask_str("New measurement : DCR / DAQ / LASER ? ('Cancel' to quit)")
    if type(type_mesure) == str:
        type_mesure = type_mesure.upper()
        

    while (type(type_mesure) == str) and (type_mesure in ['DCR', 'DAQ', 'LASER']):
        
        dict_config['measurement_type'] = type_mesure
        
        temp = ask_str("Bin size TOT = {} ps".format(dict_config['bin_size']['bin_tot']))
        if (type(temp) == str) and (int(temp) in [3, 12, 24, 49, 98, 198]):
            dict_config['bin_size']['bin_tot'] = int(temp)
        elif type(temp) == str:
            while int(temp) not in [3, 12, 24, 49, 98, 198]:
                temp = ask_str("Bin size must be in [3, 12, 24, 49, 98, 198]")
            dict_config['bin_size']['bin_tot'] = int(temp)
        
        temp = ask_str("Bin size TOA = {} ps".format(dict_config['bin_size']['bin_toa']))
        if (type(temp) == str) and (int(temp) in [3, 12, 24, 49, 98, 198]):
            dict_config['bin_size']['bin_toa'] = int(temp)
        elif type(temp) == str:
            while int(temp) not in [3, 12, 24, 49, 98, 198]:
                temp = ask_str("Bin size must be in [3, 12, 24, 49, 98, 198]")
            dict_config['bin_size']['bin_toa'] = int(temp)
            
        temp = ask_str("Preamp gain = {}".format(dict_config['pamp_gain']))
        if type(temp) == str:
            if ',' in temp:
                dict_config['pamp_gain'] = temp.split(',')
            elif ';' in temp:
                dict_config['pamp_gain'] = temp.split(';')
            elif ' ' in temp:
                dict_config['pamp_gain'] = temp.split(' ')
            elif '/' in temp:
                dict_config['pamp_gain'] = temp.split('/')
            elif len(temp)<2:
                dict_config['pamp_gain'] = [temp]
            for e in range(len(dict_config['pamp_gain'])):
                if 1 <= int(dict_config['pamp_gain'][e]) <= 8:
                    dict_config['pamp_gain'][e] = int(dict_config['pamp_gain'][e])
                else:
                    dict_config['pamp_gain'].pop(e)
        elif len(dict_config['list_gain']) > 0:
            dict_config['pamp_gain'] = dict_config['list_gain']
            
        temp = ask_str("Channel's list = {}".format(dict_config['channels']))
        if (type(temp) == str) and (temp.upper() == 'ALL'):
            dict_config['channels'] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 
                                    15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 
                                    27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                    39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 
                                    51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 63]
        elif type(temp) == str:
            if ',' in temp:
                dict_config['channels'] = temp.split(',')
            elif ';' in temp:
                dict_config['channels'] = temp.split(';')
            elif ' ' in temp:
                dict_config['channels'] = temp.split(' ')
            elif '/' in temp:
                dict_config['channels'] = temp.split('/')
            elif len(temp)<3:
                temp = [temp]
            for e in range(len(dict_config['channels'])):
                if (0 <= int(dict_config['channels'][e]) <= 63) and (int(dict_config['channels'][e]) != 62):
                    dict_config['channels'][e] = int(dict_config['channels'][e])
                else:
                    dict_config['channels'].pop(e)
                
        temp = ask_str("V bias = {} V".format(dict_config['Vbias']))
        if type(temp) == str:
            dict_config['Vbias'] = int(temp)
            
            
        if type_mesure == 'DCR':
            
            temp = ask_str("Start threshold = {}".format(dict_config['dcr']['start_threshold']))
            if (type(temp) == str) and (0 < int(temp) < 1024):
                dict_config['dcr']['start_threshold'] = int(temp)
            elif type(temp) == str:
                while not (0 < int(temp) < 1024):
                    temp = ask_str("Start threshold must be between 1 and 1023")
                dict_config['dcr']['start_threshold'] = int(temp)
            
            temp = ask_str("Stop threshold = {}".format(dict_config['dcr']['stop_threshold']))
            if (type(temp) == str) and (dict_config['dcr']['start_threshold'] < int(temp) < 1024):
                dict_config['dcr']['stop_threshold'] = int(temp)
            elif type(temp) == str:
                while not (dict_config['dcr']['start_threshold'] < int(temp) < 1024):
                    temp = ask_str("Stop threshold must be between {} and 1023".format(dict_config['dcr']['start_threshold']))
                dict_config['dcr']['stop_threshold'] = int(temp)
                
            temp = ask_str("Threshold step = {}".format(dict_config['dcr']['step']))
            if (type(temp) == str) and (0 < int(temp) < 1024):
                dict_config['dcr']['step'] = int(temp)
            elif type(temp) == str:
                while not (0 < int(temp) < 1024):
                    temp = ask_str("Threshold step must be between 1 and 1023")
                dict_config['dcr']['step'] = int(temp)
            
            
        elif type_mesure in ['DAQ', 'LASER']:
            
            if type_mesure == 'DAQ':
                temp = ask_str("Laser frequency = {} kHz".format(dict_config['daq']['frequency']))
                if type(temp) == str:
                    dict_config['daq']['frequency'] = int(temp)
                    
            # elif type_mesure == 'LASER':
            #     temp = ask_str("Laser frequency = {} kHz".format(dict_config['daq']['frequency']))
            #     if type(temp) == str:
            #         if ',' in temp:
            #             dict_config['daq']['frequency'] = temp.split(',')
            #         elif ';' in temp:
            #             dict_config['daq']['frequency'] = temp.split(';')
            #         elif ' ' in temp:
            #             dict_config['daq']['frequency'] = temp.split(' ')
            #         elif '/' in temp:
            #             dict_config['daq']['frequency'] = temp.split('/')
            #         for e in range(len(dict_config['daq']['frequency'])):
            #             if 0 < int(dict_config['daq']['frequency'][e]) <= 15000000:
            #                 dict_config['daq']['frequency'][e] = int(dict_config['daq']['frequency'][e])
            #             else:
            #                 dict_config['daq']['frequency'].pop(e)
                            
            
            temp = ask_str("Thresholds = {}".format(dict_config['daq']['thresholds']))
            if type(temp) == str:
                if '|' in temp:
                    dict_config['daq']['thresholds'] = list(range(int(temp.split('|')[0]), int(temp.split('|')[1])+int(temp.split('|')[2]), int(temp.split('|')[2])))
                elif ',' in temp:
                    dict_config['daq']['thresholds'] = temp.split(',')
                elif ';' in temp:
                    dict_config['daq']['thresholds'] = temp.split(';')
                elif ' ' in temp:
                    dict_config['daq']['thresholds'] = temp.split(' ')
                elif '/' in temp:
                    dict_config['daq']['thresholds'] = temp.split('/')
                elif len(temp)<2:
                    dict_config['daq']['thresholds'] = [temp]
                for e in range(len(dict_config['daq']['thresholds'])):
                    if 0 < int(dict_config['daq']['thresholds'][e]) < 1024:
                        dict_config['daq']['thresholds'][e] = int(dict_config['daq']['thresholds'][e])
                    else:
                        dict_config['daq']['thresholds'].pop(e)
            elif len(dict_config['daq']['list_thr']) > 0:
                dict_config['daq']['thresholds'] = dict_config['daq']['list_thr']
            
            temp = ask_str("Measurement time = {} s".format(dict_config['daq']['duration']))
            if type(temp) == str:
                dict_config['daq']['duration'] = int(temp)
                
        ##########################################################        
        dict_config['list_gain'] = list(dict_config['pamp_gain'])
        if type_mesure == 'DAQ':
            dict_config['daq']['list_thr'] = list(dict_config['daq']['thresholds'])
        
        
        verif = [dict_config['session_name'],
                dict_config['measurement_type'],
                dict_config['bin_size']['bin_toa'],
                dict_config['bin_size']['bin_tot'],
                dict_config['Vbias']
                ]
        
        if len(dict_config['channels']) == 63:
            verif.append("all")
        else:
            verif.append(dict_config['channels'])
            
        verif.append(dict_config["list_gain"])
            
        if type_mesure == 'DAQ':
            verif += [dict_config['daq']["list_thr"],
                    dict_config['daq']["duration"],
                    dict_config['daq']["frequency"]
                    ]
        elif type_mesure == 'DCR':
            verif += [dict_config['dcr']["start_threshold"],
                    dict_config['dcr']["stop_threshold"],
                    dict_config['dcr']["step"]
                    ]
            
        recap = "Session: {}\nMeasure: {}\nBin TOA: {} ps\nBin TOT: {} ps\nVbias: {}V\nChannels: {}\nGains: {}\n".format(*verif[:7])    
        if type_mesure == 'DAQ':
            recap += "Thresholds: {}\nDuration: {}s\nFrequency: {}Hz\n".format(*verif[-3:])
        elif type_mesure == 'DCR':
            recap += "Start threshold: {}\nStop threshold: {}\nStep threshold:: {}\n".format(*verif[-3:])
        
        if not UI_message('ask', recap):
            sys.exit()
        
            
        print("="*30)
        print("Measurements start")
        print("="*30)
        if type_mesure == 'DCR':
            print("\nDCR - {} gains | {} channels".format(len(dict_config['list_gain']), len(dict_config['channels'])))
        elif type_mesure == 'DAQ':
            print("\nDAQ - {} gains | {} thresholds".format(len(dict_config['list_gain']), len(dict_config['daq']['list_thr'])))
        
        time0 = time.time()
        flag_first = True
        
        for k, e_gain in enumerate(dict_config['list_gain']):
            kmax = len(dict_config['list_gain'])
            dict_config['pamp_gain'] = e_gain
            
            if type_mesure == 'DAQ':
                for kk, e_thr in enumerate(dict_config['daq']['list_thr']):
                    kkmax = len(dict_config['daq']['list_thr'])
                    timer = time.time() - time0
                    time0 = time.time()
                    if flag_first:
                        print("Measurement {}/{} - ETA ~ {} min".format(1, kmax*kkmax, int(dict_config['daq']['duration']*kmax*kkmax/60)))
                        flag_first = False
                    else:
                        print("Measurement {}/{} - ETA ~ {} min".format(k*kkmax+kk+1, kmax*kkmax, int(timer*(kmax*kkmax-(k*kkmax+kk))/60)))
                    
                    dict_config['daq']['thresholds'] = e_thr
            
                    with open("./config.yaml", 'w') as f:
                        yaml.dump(dict_config, f, default_flow_style=False)
                    
                    manager = MeasurementManager(dict_config)
                    manager.setup_devices()
                
                    for dev_conf in manager.config.get("devices", []):
                        ip = dev_conf["ip"]
                        if not ping_ip_address(ip):
                            if interactive:
                                print(f"Device at {ip} not reachable, skipping.")
                            continue
                    
                    manager.run_measurements()
                    manager.wait_for_completion()
            
            elif type_mesure == 'DCR':
                timer = time.time() - time0
                time0 = time.time()
                if flag_first:
                    print("Measurement {}/{} - ETA ~ ? min".format(1, kmax))
                    flag_first = False
                else:
                    print("Measurement {}/{} - ETA ~ {} min".format(k+1, kmax, int(timer*(kmax-k)/60)))
                with open("./config.yaml", 'w') as f:
                    yaml.dump(dict_config, f, default_flow_style=False)
                
                manager = MeasurementManager(dict_config)
                manager.setup_devices()
            
                for dev_conf in manager.config.get("devices", []):
                    ip = dev_conf["ip"]
                    if not ping_ip_address(ip):
                        if interactive:
                            print(f"Device at {ip} not reachable, skipping.")
                        continue
                
                manager.run_measurements()
                manager.wait_for_completion()
        
        
        
        type_mesure = ask_str("New measurement : DCR / DAQ ? ('Cancel' to quit)")
        if type(type_mesure) == str:
            type_mesure = type_mesure.upper()



