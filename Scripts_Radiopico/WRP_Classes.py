# -*- coding: utf-8 -*-
"""
Created on Wed May 21 11:39:13 2025

"""
from . import WRP_I2C as i2c
from . import WRP_Device as WRP_Device
from . import WRP_Plotter as WRP_Plotter

import time, struct, yaml, threading
import pandas as pd
import numpy as np
from enum import Enum
from matplotlib.figure import Figure

interactive = False

#####################################################################
################## PicoTDC ##########################################
#####################################################################

class PicoTDC():
    def __init__(self, link) -> None:
        self.link = link
        self.CONFIG_DEFAULT =  0
        self.I2C_PICO_WRITE =  1
        self.I2C_PICO_READ  =  2
        self.STAIRCASE      =  8
        self.CHANNEL_EN     = 13
        self.TRIGGER_CLOCK  = 16
        self.MUX_OUTING     = 17
        self.CMD_COMM_VAL   = 18

        self.clean_data     = 0 
        self.raw_data       = 0
        self.COMM_VAL       = False
        self.started_daq    = False
        df = {"addr": [], "data": []}
        self.df_i2c = pd.DataFrame(df)

        #daq
        self.values_per_section = 32
        self.total_values = 128
        
        pass

    def updateLink(self, device):
        self.link = device
        return
    
    def sending_function(self, cmd, args, read_all=False):
        data_to = f"!{cmd}!"
        if(isinstance(args, int) ==  False):
            for arg in args:
                data_to +=  f"{arg}!"
        else:
            data_to += f"{args}!"
        data_to += "$"
        if interactive:
            print(data_to)
        if(cmd == self.I2C_PICO_WRITE):
            if(len(self.df_i2c[self.df_i2c["addr"].isin([args[0]])]) > 0):
                self.df_i2c.data[self.df_i2c.addr == args[0]] = args[1]    #Update the dataframe 
            else:
                self.df_i2c.loc[len(self.df_i2c)] = args
        try:
            self.link.write(data_to.encode())
            if(read_all == True):
                while self.link.inWaiting():
                    print(self.link.read_all())
        except:
            if interactive:
                print("ERROR", "An Error raised when trying to send data, check the connection to the board.")
        return
    
    def set_comm_val(self):
        self.COMM_VAL = True
        self.sending_function(self.CMD_COMM_VAL, [int(self.COMM_VAL)])

    def reset_comm_val(self):
        self.COMM_VAL = False
        self.sending_function(self.CMD_COMM_VAL, [int(self.COMM_VAL)])

    def set_reset_comm_val(self, btn):
        self.COMM_VAL = not self.COMM_VAL
        if (self.COMM_VAL == False):
            self.started_daq = False
        self.sending_function(self.CMD_COMM_VAL, [int(self.COMM_VAL)])
        btn.setText("STOP") if(self.COMM_VAL) else btn.setText("START")
        if interactive:
            print(f"COMM_VAL :{self.COMM_VAL}")

    def configBoard(self, window):
        self.sending_function(self.CONFIG_DEFAULT, [])
        try:
            ret = self.link.readline().decode()
        except:
            if interactive:
                print("ERROR", "Board Not Configured.")
        elapsed_time = 0
        start_time = time.time()
        while ret != '[Pico-Conf]1\r\n' and elapsed_time <= 3:
            ret = self.link.readline().decode()
            if interactive:
                print(ret)
            current_time = time.time()
            elapsed_time = current_time - start_time
        i2c.update_from_dataframe(i2c.df_i2c, window)
        if interactive:
            print("INFO", "Board Configure Successfully.")

    def i2c_write(self, address: int, data: int) -> None:
        self.link.read_all()
        self.sending_function(self.I2C_PICO_WRITE, [address, data])
        self.sending_function(self.I2C_PICO_READ, [address, data])
        ret = int(self.link.readline().decode(), 16)
        if(ret == data):
            if interactive:
                print("INFO", "Value was Written Successfully.")
              
        else:
            if interactive:
                print("ERROR", "ERROR Writing value")
            

    def i2c_read(self, address: int, result_reg_pico) -> int:
        self.link.read_all()
        self.sending_function(self.I2C_PICO_READ, address)
        ret = self.link.readline().decode()
        if interactive:
            print(ret)
        result_reg_pico.setText(ret)
        return
  
    def set_bin_tot(self, bin : int) :
        assert bin in [3, 12, 24, 49, 98, 198], f"try to select a bin inside this list [3, 12, 24, 49, 98, 198]"
        list_bins = [3, 6, 12, 24, 49, 98, 198]
        bin = (list_bins.index(bin) << 2 ) + 1
        if interactive:
            print(bin)
        self.sending_function(self.I2C_PICO_WRITE, [22, bin])
        return True
    
    def set_bin_toa(self, bin : int):
        assert bin in [3, 12, 24, 49, 98, 198], f"try to select a bin inside this list [3, 12, 24, 49, 98, 198]"
        list_bins = [3, 6, 12, 24, 49, 98, 198]
        bin = list_bins.index(bin)
        if interactive:
            print(bin)
        self.sending_function(self.I2C_PICO_WRITE, [23, bin])
        return
    
    def coarse_mode(self):
        if interactive:
            print("Configuring picoTDC for coarse mode...")

        self.sending_function(self.I2C_PICO_WRITE, [0x012B, 0x05])

        self.sending_function(self.I2C_PICO_WRITE, [0x0008, 0x02])
        
        for channel in range(64):
            addr = 0x0023 + (channel * 4) + 3
            self.sending_function(self.I2C_PICO_WRITE, [addr, 0x01])
            time.sleep(0.005)
        
        if interactive:
            print("picoTDC configured for coarse mode (12.2ps resolution)")
        
    def tdc_mode(self):
        """Configure picoTDC for standard TDC mode (disable TOT/paired mode)"""
        if interactive:
            print("Configuring picoTDC for standard TDC mode...")
        
        # Disable TOT mode by writing 0 to register 0x0016 (tot bit)
        self.sending_function(self.I2C_PICO_WRITE, [0x0016, 0x14])
        
        # Enable only leading edge detection (optional, in case it was in paired mode)
        # Write to register 0x000C to ensure untriggered=0
        self.sending_function(self.I2C_PICO_WRITE, [0x000C, 0x00])
        
        if interactive:
            print("picoTDC configured for standard TDC mode (TOT mode disabled)")
        pass
    
    def config_control_trigger_mode (self, trig_mode : bool, trig_lat : int, trig_win:int) :
        
        if int(trig_mode) :
            if(trig_lat < trig_win):
                trig_mode = False
                if interactive:
                    print("ERROR", "Trigger Latency must be Larger than Trigger Window.")
                return
            try:
                trig_lat = int(int(trig_lat) / 25)
                lower_8_bits = trig_lat & 0xFF
                upper_8_bits = (trig_lat>> 8) & 0xFF
                
                self.sending_function(self.I2C_PICO_WRITE, [16, lower_8_bits], True)
                if interactive:
                    print(self.link.read_all())
                self.sending_function(self.I2C_PICO_WRITE, [17, upper_8_bits], True)
                trig_win = int(int(trig_win) / 25)
                lower_8_bits = trig_win & 0xFF
                upper_8_bits = (trig_win >> 8) & 0xFF
                self.sending_function(self.I2C_PICO_WRITE, [18, lower_8_bits], True)
                self.sending_function(self.I2C_PICO_WRITE, [19, upper_8_bits], True)
                self.sending_function(self.I2C_PICO_WRITE, [10, 34], True)    #enable trig extern
                self.sending_function(self.I2C_PICO_WRITE, [13, 0x32], True)  #header
                self.sending_function(self.I2C_PICO_WRITE, [12, 4], True)     #Relativ Trigger
                return
            except:
                trig_mode = False
                if interactive:
                    print("ERROR", "An Error Occured Mode Trigger Not set.")
                return
        else :
            self.sending_function(self.I2C_PICO_WRITE, [10, 2], True)  #enable trig extern 
            self.sending_function(self.I2C_PICO_WRITE, [12, 1], True)  #disable header for SC
            pass
        
        return
    
    def config_control_trigger_clock (self, clk_trig : int, clk_trig_start : int, clk_trig_stop : int) :
        div_frquency_clk = int(20_000_000 / int(clk_trig)) - 1  
        valevnt_start = int(int(clk_trig_start) / 25)
        valevnt_stop = int(int(clk_trig_stop) / 25)
        
        self.sending_function(self.TRIGGER_CLOCK, [div_frquency_clk, valevnt_start, valevnt_stop])
        return

    def SC(self, step, start, stop, window, channel, canvas, pltres=False) :
        try:
            self.link.read_all()
        except:
            if interactive:
                print("error no device !")
            return
        
        step = step
        start = start
        stop = stop
        window = window
        
        channel_ = WRP_Plotter.translate(int(channel))
        buffer = []
        count = int(start)
        #if int(channel.text()) == 62:
        #    self.sending_function(7, [channel_, step, start, stop, window])
        #else:
        # enable valevnt 

        self.sending_function(self.STAIRCASE, [channel_, step, start, stop, window])
        
        ret = ''
        while(ret != 'End Staircase acquisition'):
            ret = self.link.readline().decode()[:-2]
            if(ret != ''): 
                if((ret != "Start Staircase acquisition" ) and (ret != "End Staircase acquisition")):
                    freq = int(ret.split(", ")[1]) / (int(window) * 10**-3)
                    if interactive:
                        print(f"{ret}, {freq}")
                    buffer.append(ret + "," +str(freq))
                    count += int(step)
                else:
                    buffer.append(ret)
        if interactive:
            print("done")
        if pltres:
            if interactive:
                print("[debug] reset me")
            #canvas.axes.cla()
        WRP_Plotter.plot_staircase(buffer, channel_, canvas)

    def channel_mask_one (self, btn_mskch, ch_edit) :
        try:
            self.link.read_all()
            channel_int = WRP_Plotter.translate_str(ch_edit)
            channel = str(channel_int)
        except:
            if interactive:
                print("Error Masking|Unmasking channel")
            return
        if btn_mskch == "Enable" :
            self.sending_function(self.CHANNEL_EN, [0, 1, channel])
            pass
        elif btn_mskch == "Disable" :
            self.sending_function(self.CHANNEL_EN, [0, 0, channel])
            pass
        else :
            if interactive:
                print("Button text is wrong.")
            pass
        ret = self.link.readline().decode()
        if interactive:
            print(ret)
        ret_val : int = 0
        try :
            ret_val = int(ret)
        except ValueError :
            if interactive:
                print("ERROR", "Return value can not be parsed. Is the UART working ?")
            return
        if ret_val == 1 :
            return "Disable"
        elif ret_val == 0 :
            return "Enable"
        else :
            if interactive:
                print("ERROR", "Return value is wrong.")
            pass
        return
    
    def channel_mask_all (self, btn_mskall) :
        self.link.read_all()
        #channel_int = matrix.translate_str(self.ch_edit.text())
        #channel = str(channel_int)
        if btn_mskall == "Mask All" :
            self.sending_function(self.CHANNEL_EN, [1, 0])
            self.link.read_all()
            return "Demask All"
            pass
        elif btn_mskall == "Demask All" :
            self.sending_function(self.CHANNEL_EN, [1, 1])
            return "Mask All"
            pass
        else :
            if interactive:
                print("An Error occured.")
            pass
        return

    def ethData (self, config) :
        if(self.COMM_VAL) :
            self.started_daq = True
            
            argums = [config['bin_size']['bin_tot'], 
                      config['bin_size']['bin_toa'],
                      config['pamp_gain'], 
                      config['daq']['thresholds'],
                      config['Vbias'],
                      config['daq']['duration']//60]
            
            files = [open("./{}/data_section_{}_Btot{}_Btoa{}_Gain{}_Thr{}_{}V_{}min.bin".format(config['session_name'], i, *argums), 'wb') for i in range(4)]
            #send start acq
            WRP_Device.sendto(b"START")       
                     
            #flush
            for _ in range(1024):
                _, _ = WRP_Device.recvfrom()
            while self.COMM_VAL:
                data, _ = WRP_Device.recvfrom()
                #process the data to 32 bits 
                values = []
                for i in range(0, len(data), 4):
                    octets = data[i:i+4]
                    if len(octets) == 4:
                        value = struct.unpack('<I', octets)[0]
                        values.append(value)
                #split & save the data to the corresponding port file 
                sections = np.array_split(values, 4)
                for section, file in zip(sections, files):
                    for value in section:
                        file.write(struct.pack('<I', value))
                    file.flush()
            for file in files:
                file.close()
            self.started_daq = False
        return

    def debug_signal(self, mux_index : int):

        self.sending_function(self.MUX_OUTING, [mux_index])
        return

    def probe(self, channel_probe : int, cmd_shlg = False, cmd_shhg = False, cmd_palg = False, cmd_pahg = False):
        channel = channel_probe.text()
        prb =  Enum("mcd_prob", ['cmd_palg', 'cmd_pahg', 'cmd_shlg', 'cmd_shhq', 'cmd_TQ'], start=0)
        if(cmd_shlg) :
            self.sending_function(9, [2, channel, prb.cmd_shlg.value])
        elif(cmd_shhg) :
            self.sending_function(9, [2, channel, prb.cmd_shhq.value])
        elif(cmd_palg) :
            self.sending_function(9, [2, channel, prb.cmd_palg.value])
        elif(cmd_pahg) :
            self.sending_function(9, [2, channel, prb.cmd_pahg.value])

    def reset_probe(self):
        self.sending_function(9, 1)   # reset all channel register probe 
        self.sending_function(9, 3)   # reset analog probe 
        return
    
    
#####################################################################
################## AUTO MEASURE #####################################
#####################################################################

class BaseMeasurement(threading.Thread):
    def __init__(self, parent, config, channels, canvas):
        super().__init__()
        self.parent = parent
        self.config = config
        self.channels_on = channels
        self.canvas = canvas
        self.daq_running = threading.Event()
        self.progress = 0

    def update_progress(self, value):
        self.progress = value
        progress_bar = f"[{'#' * int(value/5)}{'.' * (20-int(value/5))}] {value}%"
        print(f"\rProgress: {progress_bar}", end="")
        if value == 100:
            print()

    def stop(self):
        self.daq_running.clear()


class DCRMeasurement(BaseMeasurement):
    def run(self):
        try:
            self.daq_running.set()
            start_range = int(self.config.get('dcr', {}).get('start_threshold', 0))
            stop_range = int(self.config.get('dcr', {}).get('stop_threshold', 1023))
            step = int(self.config.get('dcr', {}).get('step', 1))
            assert start_range >= 0 and start_range < 1024 and start_range < stop_range
            assert stop_range >= 0 and stop_range < 1024
            self.parent.pico.channel_mask_all("Mask All")
            for index, channel in enumerate(self.channels_on):
                if self.daq_running.is_set():
                    time.sleep(1)
                    self.parent.pico.channel_mask_one("Enable", channel)
                    time.sleep(0.05)
                    self.parent.pico.SC(step, start=start_range, stop=stop_range, window=100, channel=channel, canvas=self.canvas, pltres=True)
                    time.sleep(0.05)
                    self.parent.pico.channel_mask_one("Disable", channel)
                    time.sleep(0.05)
                    if len(self.channels_on) == 1:
                        self.update_progress(100)
                    else:
                        self.update_progress(int((index*100)/(len(self.channels_on)-1)))
                else:
                    break
            
        except Exception as e:
            if interactive:
                print(f"Erreur DCR: {e}")
        finally:
            self.daq_running.clear()
            if interactive:
                print("DCR STOP ....")


class DAQMeasurement(BaseMeasurement):
    def run(self):
        try:
            self.daq_running.set()
            if interactive:
                print("DAQ START ....")
            self.parent.pico.ethData(self.config)
            time.sleep(0.5)
            # -------------------------------------------
        except Exception as e:
            if interactive:
                print(f"Erreur DAQ: {e}")
        finally:
            self.daq_running.clear()
            if interactive:
                print("DAQ STOP ....")


class Measurements:
    def __init__(self, serial, picoTDC, dict_config={}):
        self.device = serial
        self.pico = picoTDC
        self.channels_on = []
        self.config = dict_config
        if 'channels' in self.config:
            self.channels_on = self.config['channels']
        self.canvas = Figure(figsize=(8, 6))
        self.measurement_thread = None

    @property
    def daq_running(self):
        return self.measurement_thread is not None and getattr(self.measurement_thread, "daq_running", None) and self.measurement_thread.daq_running.is_set()
    
    def load_config(self, config_file):
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        if 'channels' in self.config:
            self.channels_on = self.config['channels']
        if interactive:
            print(f"Loaded configuration: {self.config}")
        return self.config

    def save_config(self, config_file):
        with open(config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        if interactive:
            print(f"Configuration saved to {config_file}")

    def start_measure(self):
        if not self.config:
            if interactive:
                print("No configuration loaded!")
            return
        if not self.channels_on:
            if interactive:
                print("No channels specified in configuration!")
            return
        mode = self.config.get('measurement_type', 'DCR')
        if interactive:
            print(f"Starting measurement in {mode} mode on channels {self.channels_on}")

        if mode == "DCR":
            self.measurement_thread = DCRMeasurement(self, self.config, self.channels_on, self.canvas)
            self.measurement_thread.daemon = True
            self.measurement_thread.start()
            
        elif mode == "DAQ":
            #DAQ configuration
            for channel in self.channels_on:
                self.pico.channel_mask_one("Enable", channel)
                time.sleep(0.05)
            all_channels = range(64)
            enabled_channels = set(self.channels_on)
            for channel in all_channels:
                if channel not in enabled_channels:
                    self.pico.channel_mask_one("Disable", channel)
                    time.sleep(0.05)
            self.pico.set_comm_val()

            #Lance la DAQ
            self.measurement_thread = DAQMeasurement(self, self.config, self.channels_on, self.canvas)
            self.measurement_thread.daemon = True
            self.measurement_thread.start()


            # Lance le timer dans un thread séparé
            duration = int(self.config.get('daq', {}).get('duration', 60))
            self._timer_thread = threading.Thread(target=self._daq_timer, args=(duration,), daemon=True)
            self._timer_thread.start()
        else:
            if interactive:
                print("No Measurements mode found")
            return

    def _daq_timer(self, duration):
        start_time = time.time()
        while self.daq_running:
            elapsed = time.time() - start_time
            if duration > 0:
                progress = min(int((elapsed * 100) / duration), 100)
                if self.measurement_thread:
                    self.measurement_thread.update_progress(progress)
            if elapsed >= duration:
                if interactive:
                    print("Durée DAQ atteinte, arrêt de la mesure.")
                self.stop_measurement()
                break
            time.sleep(0.5)

    def stop_measurement(self):
        if self.measurement_thread:
            self.measurement_thread.stop()
            self.pico.reset_comm_val()
            if self.measurement_thread.is_alive():
                self.measurement_thread.join(timeout=5)
            self.measurement_thread = None

