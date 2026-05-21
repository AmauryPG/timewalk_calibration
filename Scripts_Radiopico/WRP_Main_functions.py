# -*- coding: utf-8 -*-
"""
Created on Fri May 23 09:15:01 2025

"""

import os, sys
import time
import yaml
import re

from .WRP_Functions import *
from .WRP_Device import *
from .ReadBinaryWeeroc import *

interactive = False

dict_config = {'devices': [{'serial_port': 'COM6', 'ip': '192.168.1.10', 
                            'i2c_defaults': "../../src/boardHandler/board/weeroc/Scripts_Radiopico/radio_default_i2c.csv"}],
               'bin_size': {'bin_toa': 3, 'bin_tot': 49},
               'pamp_gain': [],
               'list_gain': [8],
               'measurement_config': 0,
               'measurement_type': 'DCR',
               'wdir': './',
               'session_name': 'MyMeasurementSession',
               'channels': [42],
               'Vbias': 58,
               'dcr': {'start_threshold': 100, 'stop_threshold': 600, 'step': 3},
               'daq': {'thresholds': [300], 'list_thr': [], 'duration': 60, 'frequency': 100000}
               }

##########################################################################

validMeasureType = ['DCR', 'DAQ', 'LASER']
validBinToT=[3, 12, 24, 49, 98, 198]
validBinToF=[3, 12, 24, 49, 98, 198]
validChannels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 
                                   15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 
                                   27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                   39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 
                                   51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 63]
lowerThresholdBound = 0
upperThresholdBound = 1024

def buildDictForOneMeasurement(relativePathToWorkDirectory, sessionName, binToT, binToF, preampGain, selectedChannel, vBias):
    # Get global variables
    global validBinToT, validBinToF, validChannels, lowerThresholdBound, upperThresholdBound

    # Set Bias 
    dict_config['Vbias'] = vBias

    # Get working folder
    dict_config['wdir'] = relativePathToWorkDirectory

    # Check if working folder exist, else create it
    if not os.path.exists(dict_config['wdir']):
        # If it doesn't exist, create it
        os.makedirs(dict_config['wdir'])
        print(f"Folder '{dict_config['wdir']}' created successfully.")
    else:
        print(f"Using folder relative : '{dict_config['wdir']}'")
        print(f"Using folder absolute : '{os.path.abspath(dict_config['wdir'])}'")

    # Check if the session is valid
    if(not sessionName):
        # Empty session name
        sys.exit("Must have a session name")
    else:
        dict_config['session_name'] = sessionName

    if(not folder_management(dict_config)):
        sys.exit("Invalid session name. Check your inputs")
        
    # Check if the bins value are valid
    if(binToT not in validBinToT):
        sys.exit(f"Invalid bin ToT value. Valid values are : {validBinToT}")

    # Set bin TOT
    dict_config['bin_size']['bin_tot'] = binToT
    
    # Check if the bins value are valid
    if(binToF not in validBinToF):
        sys.exit(f"Invalid bin ToF value. Valid values are : {validBinToF}")

    # Set bin TOA / TOF
    dict_config['bin_size']['bin_toa'] = binToF
    
    # Select the list gain
    dict_config['list_gain'] = [preampGain]

    # Check for the all selected
    if(type(selectedChannel) == str and selectedChannel.upper() == "ALL"):
        selectedChannel = validChannels

    # Select the channel
    if(selectedChannel not in validChannels):
        sys.exit(f"Invalid bin ToF value. Valid values are : {validChannels}")

    dict_config["channels"] = [selectedChannel]

    dict_config['daq']['thresholds'].clear()

    return dict_config

def takeOneMeasurementDCR(relativePathToWorkDirectory, sessionName, binToT, binToF, preampGain, selectedChannel, startThreshold, stopThreshold, stepThreshold, Vbias):
    
    # Stop the program in case of a problem
    # So if it continue, everything work alright
    dict_config = buildDictForOneMeasurement(relativePathToWorkDirectory, sessionName, binToT, binToF, preampGain, selectedChannel, Vbias)

    dict_config['measurement_type'] = 'DCR'

    # Check if the start and stop are inverted
    if(startThreshold > stopThreshold):
            # Inverted bound
            startThreshold, stopThreshold = stopThreshold, startThreshold

    # Dummy check so step is positive
    stepThreshold = abs(stepThreshold)

    # Check bound values
    if(not (lowerThresholdBound < startThreshold < upperThresholdBound)):
        sys.exit(f"Invalid start threshold value. Valid values must be between : {lowerThresholdBound} and {upperThresholdBound} exclusive. Got : {startThreshold}")

    if(not (lowerThresholdBound < stopThreshold < upperThresholdBound)):
        sys.exit(f"Invalid stop threshold value. Valid values must be between : {lowerThresholdBound} and {upperThresholdBound} exclusive. Got : {stopThreshold}")

    if(not (lowerThresholdBound < stepThreshold < upperThresholdBound)):
        sys.exit(f"Invalid stop threshold value. Valid values must be between : {lowerThresholdBound} and {upperThresholdBound} exclusive. Got : {stepThreshold}")

    # Store valid values for the threshold loop
    dict_config['dcr']['start_threshold'] = int(startThreshold)
    dict_config['dcr']['stop_threshold'] = int(stopThreshold)
    dict_config['dcr']['step'] = int(stepThreshold) 

    infoDump = [dict_config['session_name'],
                dict_config['measurement_type'],
                dict_config['bin_size']['bin_toa'],
                dict_config['bin_size']['bin_tot'],
                dict_config['Vbias']
                ]
    
    if len(dict_config['channels']) == 63:
        infoDump.append("all")
    else:
        infoDump.append(dict_config['channels'])
        
    infoDump.append(dict_config["list_gain"])
        
    infoDump += [dict_config['dcr']["start_threshold"],
                dict_config['dcr']["stop_threshold"],
                dict_config['dcr']["step"]
                ]
        
    recap = "Session: {}\nMeasure: {}\nBin TOA: {} ps\nBin TOT: {} ps\nVbias: {}V\nChannels: {}\nGains: {}\n".format(*infoDump[:7])    
    recap += "Start threshold: {}\nStop threshold: {}\nStep threshold:: {}\n".format(*infoDump[-3:])
    
    print(recap)
    
    print("="*30)
    print("Measurements start")
    print("="*30)
    print("\nDCR - {} gains | {} channels".format(len(dict_config['list_gain']), len(dict_config['channels'])))
    
    time0 = time.time()
    flag_first = True
    
    for k, e_gain in enumerate(dict_config['list_gain']):
        kmax = len(dict_config['list_gain'])
        dict_config['pamp_gain'] = e_gain
        
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

def buildOutputFilename(relativePathToWorkDirectory, binToT, binToF, preampGain, selectedChannel, threshold, biais, laserFrequency, durationTimeSeconds):
    # Build filename
    if not relativePathToWorkDirectory.endswith("/"):
        relativePathToWorkDirectory += "/"

    return f"{relativePathToWorkDirectory}data_section_{selectedChannel}_Btot{binToT}_Btoa{binToF}_Gain{preampGain}_Thr{threshold}_{biais}V_Freq{laserFrequency}_{durationTimeSeconds}s.bin"


def takeOneMeasurementDAQ(relativePathToWorkDirectory, sessionName, binToT, binToF, preampGain, selectedChannel, thresholds, vBias, laserFrequency, durationTimeSeconds):
    # Stop the program in case of a problem
    # So if it continue, everything work alright
    dict_config = buildDictForOneMeasurement(relativePathToWorkDirectory, sessionName, binToT, binToF, preampGain, selectedChannel, vBias)

    dict_config['measurement_type'] = 'DAQ'

    # Check if laser is valid
    if(laserFrequency < 0):
        sys.exit(f"Laser frequency must be strictly positive. Got : {laserFrequency}")

    if 0 < thresholds < 1024:
        dict_config['daq']['thresholds'].append(int(thresholds))
    else:
        sys.exit(f"Invalid threshold value. Valid values must be between : {lowerThresholdBound} and {upperThresholdBound} exclusive. Got : {thresholds}")

    # Store data after checking validity
    dict_config['daq']['frequency'] = int(laserFrequency)

    dict_config['daq']['list_thr'] = list(dict_config['daq']['thresholds'])

    dict_config['daq']['duration'] = int(durationTimeSeconds)
    
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
        
    verif += [dict_config['daq']["list_thr"],
                dict_config['daq']["duration"],
                dict_config['daq']["frequency"]
                ]
        
    recap = "Session: {}\nMeasure: {}\nBin TOA: {} ps\nBin TOT: {} ps\nVbias: {}V\nThreshold: {}\nChannels: {}\nGains: {}\n".format(*verif[:7])    
    recap += "Duration: {}s\nFrequency: {}Hz\n".format(*verif[-3:])

    print(recap)

    print("="*30)
    print("Measurements start")
    print("="*30)
    print("\nDAQ - {} gains | {} thresholds".format(len(dict_config['list_gain']), len(dict_config['daq']['list_thr'])))

    time0 = time.time()
    flag_first = True

    print("Set biais to {}V".format(dict_config['Vbias']))

    while True:
        userInput = input(f"Is the bias set to {dict_config['Vbias']}? (y/n) : ")
        if userInput.lower() == "y":
            break
    
    dict_config['pamp_gain'] = preampGain
    dict_config['daq']['thresholds'] = thresholds

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
    
    startTimeMeasurement = time.ctime()
        
    # Run the measurement
    manager.run_measurements()
    manager.wait_for_completion()

    realDurationTimeInSeconds = startTimeMeasurement - time.ctime()

    # Build filename
    filename = buildOutputFilename(relativePathToWorkDirectory, binToT, binToF, preampGain, selectedChannel, thresholds, vBias, laserFrequency, realDurationTimeInSeconds)

    return startTimeMeasurement, realDurationTimeInSeconds, filename


def extractBiaisThreshold(s: str):
    # Match: ThrXXX_YY-YV
    m = re.search(r"Thr(\d+)_([\d\-]+)V", s)
    if not m:
        return None

    xxx = m.group(1)                # XXX
    yy_y = m.group(2).replace('-', '.')  # YY-Y -> YY.Y

    return xxx, yy_y
