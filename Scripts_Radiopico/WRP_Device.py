# -*- coding: utf-8 -*-
"""
Created on Wed May 21 10:42:38 2025

"""

import sys, os, time
import socket, serial
import pandas as pd

from . import WRP_I2C as i2c

interactive = True

#####################################################################
################## ETHERNET METHODS #################################
#####################################################################

##### INIT #################################################
ip_address  = "192.168.1.10"  # doit etre saisie ou auto 
IP_PORT     = 40200
ser_port = "COM6"  #doit etre automatique ou saisie 
SERIAL_BAUD = 115200
ETHERNET_PACKET_SIZE = 1024

sock = None
ser = None

connect_status = 1
status_message = ''
dev = None
ethdev = None
#############################################################

def connect(serial_port = "COM6", board_ip = "192.168.1.10") -> None :
    global sock, ser, connect_status, dev, ethdev, ip_address, ser_port
    try:
        ip_address = board_ip
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if interactive:
            print(ip_address)
        #sock.setblocking(0)
        if(ser == None):
            if interactive:
                print(serial_port)
            ser_port =  serial_port
            ser = serial.Serial(serial_port, SERIAL_BAUD, timeout=1)
        else:
            if interactive:
                print(f"Serial connected to {SERIAL_BAUD}")
        if interactive:
            print(f'serial = {ser}')
        connect_status = 0
        #status_message = "connect ok"
        dev = ser
        ethdev = sock
        if interactive:
            print("connect ok")
        return 0
    #except Exception as e:
    except:
        ser = None
        connect_status = 1
        return 4
    

def sendto(req) -> None :
    global ip_address
    if interactive:
        print(f'send request to f{(ip_address, IP_PORT)}')
    sock.sendto(req, (ip_address, IP_PORT))
    return


def recvfrom() :
    return sock.recvfrom(ETHERNET_PACKET_SIZE)


# Serial methods
def readline() :
    return ser.readline()


def read_all() :
    return ser.read_all()


def write(data) :
    r = ser.write(data)
    return r


def read_word(x):
    if ser is None: return "00000000"
    else: return "00000001"
    

def flush(req):
    sendto(req)
    for i in range(120):
        sock.recvfrom(ETHERNET_PACKET_SIZE)



#####################################################################
################## RADIOROC #########################################
#####################################################################

def radio_set_val_evnt(enable : bool):
    manager = i2c.I2CDeviceManager()
    manager.define_register("Forced_ValEvt", 67, 0, nbbits=2, position=0)
    if enable:
        if(manager.set_value("Forced_ValEvt", 1)):
            return True
    else :
        if(manager.set_value("Forced_ValEvt", 0)):
            return True
    return False


def radio_set_threshold(threshold: int):
    manager = i2c.I2CDeviceManager()
    assert threshold >= 0 and threshold <= 1023, f"Threshold must be between 0 and 1023, got {threshold}"
    manager.define_register("Dac1_low", 65, 1, nbbits=8, position=0)
    manager.define_register("Dac1_high", 65, 2, nbbits=2, position=0)
    
    low_part = threshold & 0xFF 
    high_part = (threshold >> 8) & 0x03 
    
    low_success = manager.set_value("Dac1_low", low_part)
    high_success = manager.set_value("Dac1_high", high_part)
    
    if low_success and high_success:
        if interactive:
            print(f"Threshold set successfully to {threshold} (low: {low_part}, high: {high_part})")
        return True
    else:
        if interactive:
            print(f"Failed to set threshold: low_success={low_success}, high_success={high_success}")
        return False


def radio_set_patgain(gain: int):
    """Set patGain for all 64 channels at once"""
    manager = i2c.I2CDeviceManager()
    assert gain >= 0 and gain <= 63, f"Gain must be between 0 and 63, got {gain}"
    manager.define_register("all_patGain", 0, 1, nbbits=6, position=0, all_channels_add=True)
    return manager.set_value("all_patGain", gain)

def radio_set_patgain_ch(gain: int, ch: int):
    """Set patGain for a specific channel"""
    manager = i2c.I2CDeviceManager()
    assert gain >= 0 and gain <= 63, f"Gain must be between 0 and 63, got {gain}"
    assert ch >= 0 and ch < 64, f"Channel must be between 0 and 63, got {ch}"
    manager.define_register(f"patGain_ch{ch}", ch, 1, nbbits=6, position=0, all_channels_add=False)
    return manager.set_value(f"patGain_ch{ch}", gain)
 
 
def radio_set_inDac_ch(DAC: int, ch: int):
    """Set inDac for a specific channel"""
    manager = i2c.I2CDeviceManager()
    assert DAC >= 0 and DAC <= 255, f"DAC value must be between 0 and 255, got {DAC}"
    assert ch >= 0 and ch < 64, f"Channel must be between 0 and 63, got {ch}"
    manager.define_register(f"inDac_ch{ch}", ch, 0, nbbits=8, position=0, all_channels_add=False)
    return manager.set_value(f"inDac_ch{ch}", DAC)

#####################################################################
################## TEST I2C #########################################
#####################################################################

def test_connection(serial_port, board_ip):
    """Test device connection"""
    if interactive:
        print("\n=== Testing Connection ===")
        print(f"Serial port: {serial_port}")
        print(f"Board IP: {board_ip}")
    status = connect(serial_port, board_ip)
    if status == 0:
        if interactive:
            print("\n✅ Connection successful")
            print(f"   Serial: {ser}")
            print(f"   Socket: {sock}")
        return True
    else:
        if interactive:
            print(f"\n❌ Connection failed with status {status}")
            print(f"   Error message: {status_message}")
        return False
    

def test_register_communication():
    """Test basic register read/write"""
    if interactive:
        print("\n=== Testing Register Communication ===")
    # Define test register (using a register that's safer to modify)
    # Update these with a safer register to test with
    test_add = 65  # DAC register address
    test_subadd = 1  # Low part sub-address
    # Read original value
    if interactive:
        print(f"Reading register {test_add}/{test_subadd}...")
    original_value = i2c.read_register(test_add, test_subadd)
    if original_value is None:
        if interactive:
            print("❌ Failed to read register")
        return False
    if interactive:
        print(f"Original value: {original_value} (binary)")
    # Write test value
    test_value = "10101010"  # Alternating bits
    if interactive:
        print(f"Writing test value {test_value} to register...")
    write_success = i2c.write_register(test_add, test_subadd, test_value)
    if not write_success:
        if interactive:
            print("❌ Failed to write register")
        return False
    # Read back value to verify
    read_value = i2c.read_register(test_add, test_subadd)
    if read_value is None:
        if interactive:
            print("❌ Failed to read back register value")
        return False
    if interactive:
        print(f"Read back value: {read_value} (binary)")
    # Verify value matches
    if read_value == test_value:
        if interactive:
            print("✅ Write/read verification successful")
    else:
        if interactive:
            print(f"❌ Value mismatch: wrote {test_value}, read {read_value}")
    # Restore original value
    if interactive:
        print(f"Restoring original value: {original_value}")
    restore_success = i2c.write_register(test_add, test_subadd, original_value)
    if not restore_success:
        if interactive:
            print("⚠️ Failed to restore original value")
    # Overall success
    return read_value == test_value


def test_set_value():
    """Test the register bit manipulation function set_value"""
    if interactive:
        print("\n=== Testing set_value Function ===")
    # Initialize device manager
    manager = i2c.I2CDeviceManager()
    # Define test register to modify just a few bits
    manager.define_register(
        "test_register",
        add=65,          # DAC register
        subadd=1,        # Low part sub-address
        nbbits=2,        # Modify just 2 bits
        position=2       # At position 2
    )
    # Read original value
    original_value = manager.get_value("test_register")
    if interactive:
        print(f"Original value at bit position: {original_value}")
    # Set test value (toggle between 0, 1, 2, 3)
    test_value = (original_value + 1) % 4
    if interactive:
        print(f"Setting value to {test_value}...")
    success = manager.set_value("test_register", test_value)
    if not success:
        if interactive:
            print("❌ Failed to set value")
        return False
    # Read back and verify
    read_value = manager.get_value("test_register")
    if interactive:
        print(f"Read back value: {read_value}")
    # Verify value matches
    if read_value == test_value:
        if interactive:
            print("✅ set_value verification successful")
    else:
        if interactive:
            print(f"❌ Value mismatch: set {test_value}, read {read_value}")
    # Restore original value
    if interactive:
        print(f"Restoring original value: {original_value}")
    restore_success = manager.set_value("test_register", original_value)
    if not restore_success:
        if interactive:
            print("⚠️ Failed to restore original value")
    # Overall success
    return read_value == test_value


def test_dataframe_update():
    """Test updating multiple registers via dataframe"""
    if interactive:
        print("\n=== Testing DataFrame Update ===")
    # Create a small test dataframe with safe registers to modify
    test_df = pd.DataFrame([
        (65, 1, "10101010"),  # DAC low part
        (65, 2, "00000011")   # DAC high part
    ], columns=["add", "subadd", "data"])
    # Save original values
    if interactive:
        print("Reading original values...")
    original_values = []
    for _, row in test_df.iterrows():
        value = i2c.read_register(row["add"], row["subadd"])
        original_values.append((row["add"], row["subadd"], value))
        if interactive:
            print(f"Register {row['add']}/{row['subadd']}: {value}")
    # Update with test values
    if interactive:
        print("Updating registers with test values...")
    success = i2c.update_from_dataframe(test_df)
    if not success:
        if interactive:
            print("❌ Failed to update registers")
        return False
    # Verify values
    if interactive:
        print("Verifying updated values...")
    all_verified = True
    for i, row in enumerate(test_df.iterrows()):
        _, r = row
        value = i2c.read_register(r["add"], r["subadd"])
        if interactive:
            print(f"Register {r['add']}/{r['subadd']}: {value} (expected {r['data']})")
        if value != r["data"]:
            all_verified = False
    if all_verified:
        if interactive:
            print("✅ All register values verified successfully")
    else:
        if interactive:
            print("❌ Some register values did not match")
    # Restore original values
    if interactive:
        print("Restoring original values...")
    restore_df = pd.DataFrame(original_values, columns=["add", "subadd", "data"])
    restore_success = i2c.update_from_dataframe(restore_df)
    if not restore_success:
        if interactive:
            print("⚠️ Failed to restore some original values")
    return all_verified


def test_radio_functions():

    success = []

    """Test basic radio functions"""
    if interactive:
        print("\n=== Testing Radio Functions ===")
    # Import radio functions
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Test val_evnt
    if interactive:
        print("Testing radio_set_val_evnt...")
    success.append(radio_set_val_evnt(True))
    if interactive:
        print(f"  Set ValEvnt ON: {'✅ Success' if success[-1] else '❌ Failed'}")
    time.sleep(0.5)
    success.append(radio_set_val_evnt(False))
    if interactive:
        print(f"  Set ValEvnt OFF: {'✅ Success' if success[-1] else '❌ Failed'}")
    
    # Test threshold
    if interactive:
        print("\nTesting radio_set_threshold...")
    test_threshold = 600
    success.append(radio_set_threshold(test_threshold))
    if interactive:
        print(f"  Set threshold to {test_threshold}: {'✅ Success' if success[-1] else '❌ Failed'}")
    
    # Test patGain
    if interactive:
        print("\nTesting radio_set_patgain...")
    test_gain = 8
    success.append(radio_set_patgain(test_gain))
    if interactive:
        print(f"  Set patGain to {test_gain}: {'✅ Success' if success[-1] else '❌ Failed'}")
    
    # Test Bias
    if interactive:
        print("\nTesting radio_set_inDac_ch...")
    test_dac = 50
    test_channel = 0
    success.append(radio_set_inDac_ch(test_dac, test_channel))
    if interactive:
        print(f"  Set Dac to {test_dac} in channel {test_channel}: {'✅ Success' if success[-1] else '❌ Failed'}")
        print(f"Now turning off channel {test_channel}")
    success.append(radio_set_inDac_ch(0, test_channel))
    
    # Test Bias
    if interactive:
        print("\nTesting radio_set_patgain_ch...")
    test_gain = 50
    test_channel = 0
    success.append(radio_set_patgain_ch(test_gain, test_channel))
    if interactive:
        print(f"  Set gain to {test_gain} in channel {test_channel}: {'✅ Success' if success[-1] else '❌ Failed'}")
        print(f"Now setting gain to 0 in channel {test_channel}")
    success.append(radio_set_patgain_ch(0, test_channel))

    # True if all tests are a success
    # False if one or more tests failed
    return all(success)


def test_ALL():
    if interactive:
        print("=" * 50)
        print("I2C Communication Diagnostic Tool for RadioRoc")
        print("=" * 50)
    # Load I2C CSV
    try:
        if interactive:
            print("\nLoading I2C definitions from radio_default_i2c...")
        i2c.df_i2c = pd.read_csv("radio_default_i2c.csv", index_col=None, dtype={"add": int, "subadd": int, "data": str})
        if interactive:
            print(f"✅ Loaded {len(i2c.df_i2c)} register definitions")
    except Exception as e:
        if interactive:
            print(f"❌ Failed to load CSV file: {e}")
        return 1
    # Run tests
    connected = test_connection("COM6", "192.168.1.10")
    if not connected:
        if interactive:
            print("\n❌ Connection failed. Cannot proceed with further tests.")
        return 1
    # Run communication tests
    reg_test = test_register_communication()
    value_test = test_set_value()
    df_test = test_dataframe_update()
    radio_test = test_radio_functions()
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Connection test:       {'✅ Passed' if connected else '❌ Failed'}")
    print(f"Register R/W test:     {'✅ Passed' if reg_test else '❌ Failed'}")
    print(f"set_value test:        {'✅ Passed' if value_test else '❌ Failed'}")
    print(f"DataFrame update test: {'✅ Passed' if df_test else '❌ Failed'}")
    print(f"Radio functions test:  {'✅ Passed' if radio_test else '❌ Failed'}")
    if connected and reg_test and value_test and df_test and radio_test:
        print("\n✅ All tests passed! I2C communication is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1


