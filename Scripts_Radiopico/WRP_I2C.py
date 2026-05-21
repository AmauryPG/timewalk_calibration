from . import WRP_Device as device

import pandas as pd
import tkinter as tk
from tkinter import filedialog

interactive = False


# Global dataframe for I2C data
df_i2c = pd.DataFrame()

# I2C Communication Functions
def write_register(add: int, subadd: int, data: str, verify=True, retries=3):
    """
    Write data to a specific register with verification and retries
    
    Returns:
    bool: True if successful, False otherwise
    """
    if device.connect_status != 0:
        if interactive:
            print("Not connected to the board. Check the connection.")
        return False
    
    for attempt in range(retries):
        try:
            device.read_all()
            
            # Ensure data is in correct format
            if isinstance(data, str) and all(bit in '01' for bit in data) and len(data) == 8:
                binary_data = data
            elif isinstance(data, int) and 0 <= data <= 255:
                binary_data = "{0:08b}".format(data)
            else:
                if interactive:
                    print(f"Invalid data format: {data}")
                return False
            
            d = f"!3!"
            d += f"{add}!{subadd}!{int(binary_data, 2)}!255!"
            d += "$"
            
            device.write(d.encode())
            device.readline()  # Clear read buffer
            
            # Verify write if requested
            if verify:
                read_data = read_register(add, subadd)
                if read_data == binary_data:
                    return True
                else:
                    if interactive:
                        print(f"Verification failed on attempt {attempt+1}/{retries}: wrote {binary_data}, read {read_data}")
                    if attempt == retries - 1:
                        return False
            else:
                return True
                
        except Exception as e:
            if interactive:
                print(f"Error writing register on attempt {attempt+1}/{retries}: {e}")
            if attempt == retries - 1:
                return False
    return False


def write_fifo(df: pd.DataFrame):
    """Write multiple registers from a dataframe"""
    for _, row in df.iterrows():
        write_register(row["add"], row["subadd"], row["data"])
        

def read_register(add: int, subadd: int, retries=3):
    """
    Read data from a specific register with retry capability
    
    Returns:
    str: Binary representation of register value, or None if failed
    """
    if device.connect_status != 0:
        if interactive:
            print("Not connected to the board. Check the connection.")
        return None
    
    for attempt in range(retries):
        try:
            device.read_all()
            
            d = f"!4!"
            d += f"{add}!{subadd}!"
            d += "$"
            device.write(d.encode())
            
            response = device.readline()
            if not response:
                if interactive:
                    print(f"No response on attempt {attempt+1}/{retries}")
                continue
                
            try:
                result = eval(response)
                return "{0:08b}".format(result)
            except Exception as e:
                if interactive:
                    print(f"Error parsing register data on attempt {attempt+1}/{retries}: {e}")
                continue
                
        except Exception as e:
            if interactive:
                print(f"Error reading register on attempt {attempt+1}/{retries}: {e}")
            if attempt == retries - 1:
                return None
    
    if interactive:
        print(f"Failed to read register after {retries} attempts")
    return None


def read_fifo(df: pd.DataFrame):
    """Read multiple registers based on dataframe addresses"""
    output = []
    for _, row in df.iterrows():
        value = read_register(int(row["add"]), int(row["subadd"]))
        if value:
            output.append(int(value, 2).to_bytes(length=1, byteorder='little')[0])
    
    return output


def verify_data(data_read, df: pd.DataFrame):
    """Verify read data matches expected data"""
    dataOK = True
    for i, row in enumerate(df.iterrows()):
        _, d = row
        if int(data_read[i]) != int(d["data"], 2):
            df.at[i, "data"] = '{0:08b}'.format(int(data_read[i]))
            if interactive:
                print(f"Error I2C add{d['add']} subadd{d['subadd']}: read={'{0:08b}'.format(int(data_read[i]))} != sent={d['data']}")
            dataOK = False
    return dataOK


def update_from_dataframe(df: pd.DataFrame, verify=True):
    """
    Update device registers from dataframe with error handling
    
    Returns:
    bool: True if all registers updated successfully, False otherwise
    """
    global df_i2c
    
    if device.connect_status != 0:
        if interactive:
            print("Not connected to the board. Check the connection.")
        return False
    
    dataOK = True
    updated_count = 0
    failed_count = 0
    
    # Update df_i2c with data from input df
    for _, row in df.iterrows():
        index = df_i2c.index[(df_i2c["add"] == row["add"]) & (df_i2c["subadd"] == row["subadd"])].tolist()
        if not index:
            continue
            
        index = index[0]
        data = list(df_i2c.iloc[index, 2])
        
        for j, b in enumerate(list(row["data"])):
            if b == '0' or b == '1':
                data[j] = b

        data = "".join(data)
        df.loc[(df["add"] == row["add"]) & (df["subadd"] == row["subadd"]), "data"] = data
        df_i2c.iloc[index, 2] = data
    
    # Write data to device
    for _, row in df.iterrows():
        success = write_register(row["add"], row["subadd"], row["data"], verify=verify)
        if success:
            updated_count += 1
        else:
            failed_count += 1
            dataOK = False
    
    if interactive:
        print(f"I2C update: {updated_count} registers updated, {failed_count} failed")
    return dataOK


def set_value(register_info, value, verify=True):
    """
    Set a register value with validation and error handling
    
    Parameters:
    register_info: dict with register addressing information
    value: value to set
    verify: whether to verify writes
    
    Returns:
    bool: True if successful, False otherwise
    """
    if device.connect_status != 0:
        if interactive:
            print("Not connected to the board. Check the connection.")
        return False
    
    add = register_info.get("add")
    subadd = register_info.get("subadd")
    nbbits = register_info.get("nbbits")
    position = register_info.get("position")
    all_add = register_info.get("all_channels_add", False)
    all_subadd = register_info.get("all_channels_subadd", False)
    
    # Convert value to int
    if isinstance(value, bool):
        data = int(value)
    else:
        data = int(value)
    
    # Validate parameters
    if None in (add, subadd, nbbits, position):
        if interactive:
            print("Missing required parameters in register_info")
        return False
        
    # Validate value range
    max_val = (1 << nbbits) - 1
    if data < 0 or data > max_val:
        if interactive:
            print(f"Value {data} out of range [0-{max_val}] for {nbbits}-bit field")
        return False
    
    dataOK = True
    pos = 8 - position
    
    if all_add or all_subadd:
        # Bulk update for multiple registers
        if all_add:
            df_temp = df_i2c[(df_i2c["add"] >= add) & (df_i2c["add"] < add + 64) & (df_i2c["subadd"] == subadd)]
        else:
            df_temp = df_i2c[(df_i2c["add"] == add) & (df_i2c["subadd"] < subadd + 64) & (df_i2c["subadd"] >= subadd)]

        # Format the new value as binary string of correct width
        bin_data = ("{0:0" + str(nbbits) + "b}").format(data)
        
        # Update each register
        for ch in range(min(64, len(df_temp))):
            old_data = list(df_temp.iloc[ch, 2])
            df_temp.iat[ch, 2] = "".join(old_data[0:pos - nbbits] + 
                                       list(bin_data) + 
                                       old_data[pos:])
        
        # Write and verify data integrity
        dataOK = update_from_dataframe(df_temp, verify=verify)
    elif (nbbits + position) > 8:
        # Handle multi-register data (spanning multiple registers)
        if isinstance(subadd, str) and ',' in subadd:
            sub = subadd.split(',')
            subadd_lsb = int(sub[0])
            subadd_msb = int(sub[1])
            
            # Format data as binary
            fmt = "{0:0" + str(nbbits) + "b}"
            data_bin = fmt.format(data)
            
            # Split into MSB and LSB parts
            position_value = 8 - position
            msbx = "".join(['x'] * (16 - nbbits - position))
            lsbx = "".join(['x'] * position)
            lsb = data_bin[nbbits - position_value:] + lsbx
            msb = msbx + data_bin[0:nbbits - position_value]
            
            df = pd.DataFrame([
                (add, subadd_lsb, lsb),
                (add, subadd_msb, msb)
            ], columns=["add", "subadd", "data"])
            
            dataOK = update_from_dataframe(df, verify=verify)
        else:
            if interactive:
                print("Invalid subadd format for multi-register operation")
            return False
    else:
        # Single register operation
        indices = df_i2c.index[(df_i2c["add"] == add) & (df_i2c["subadd"] == subadd)].tolist()
        if not indices:
            if interactive:
                print(f"Register not found: add={add}, subadd={subadd}")
            return False
            
        i = indices[0]
        old_data = list(df_i2c.iloc[i, 2])
        
        # Format the new value as binary string of correct width
        bin_data = ("{0:0" + str(nbbits) + "b}").format(data)
        
        # Insert new bits at correct position
        data_list = old_data[0:pos - nbbits] + list(bin_data) + old_data[pos:]
        new_data = "".join(data_list)
        df_i2c.iloc[i, 2] = new_data

        if device.connect_status == 0:
            # Write register and verify data integrity
            if write_register(add, subadd, new_data, verify=verify):
                return True
            else:
                if interactive:
                    print(f"Failed to write register add={add}, subadd={subadd}")
                return False
    
    return dataOK


def set_register_value(register_info, value):
    """Set a full register value (all 8 bits)"""
    add = register_info.get("add")
    subadd = register_info.get("subadd")
    all_add = register_info.get("all_channels_add", False)
    all_subadd = register_info.get("all_channels_subadd", False)
    
    # Format data as 8-bit binary string
    if isinstance(value, int):
        data = "{0:08b}".format(value)
    else:
        data = value
    
    # Ensure data is 8 bits
    if len(data) != 8 or not all(bit in '01' for bit in data):
        if interactive:
            print("Invalid data format. Expected 8-bit binary string.")
        return False
    
    dataOK = True
    if add is not None and subadd is not None:
        if all_add or all_subadd:
            if all_add:
                df_temp = df_i2c[(df_i2c["add"] >= add) & (df_i2c["add"] < add + 64) & (df_i2c["subadd"] == subadd)]
            else:
                df_temp = df_i2c[(df_i2c["add"] == add) & (df_i2c["subadd"] < subadd + 64) & (df_i2c["subadd"] >= subadd)]

            for ch in range(min(64, len(df_temp))):
                df_temp.iloc[ch, 2] = data
                
            # Write and read register and verify data integrity
            dataOK = update_from_dataframe(df_temp)
        else:
            indices = df_i2c.index[(df_i2c["add"] == add) & (df_i2c["subadd"] == subadd)].tolist()
            if not indices:
                if interactive:
                    print(f"Register not found: add={add}, subadd={subadd}")
                return False
                
            i = indices[0]
            df_i2c.iloc[i, 2] = data

            if device.read_word(100) != "00000000":
                # Write and read register and verify data integrity
                write_register(add, subadd, df_i2c.iloc[i, 2])
                data_read = read_register(add, subadd)
                if data_read != data:
                    dataOK = False
    
    return dataOK


def get_register_value(register_info):
    """
    Get a register value based on register information
    
    Parameters:
    register_info: dict with keys 'add', 'subadd', 'nbbits', 'position'
    
    Returns:
    int: The value at the specified location
    """
    add = register_info.get("add")
    subadd = register_info.get("subadd")
    nbbits = register_info.get("nbbits", 8)
    position = register_info.get("position", 0)
    
    if add is None or subadd is None:
        if interactive:
            print("Missing required address parameters")
        return None
    
    if position + nbbits <= 8:
        pos = 8 - position
        indices = df_i2c.index[(df_i2c["add"] == add) & (df_i2c["subadd"] == subadd)].tolist()
        if not indices:
            if interactive:
                print(f"Register not found: add={add}, subadd={subadd}")
            return None
            
        data = df_i2c.iloc[indices[0]]["data"]
        return int(data[pos - nbbits:pos], 2)
    else:
        # Handle multi-register data
        if isinstance(subadd, str) and ',' in subadd:
            sub = subadd.split(',')
            subadd_lsb = int(sub[0])
            subadd_msb = int(sub[1])
            
            indices_lsb = df_i2c.index[(df_i2c["add"] == add) & (df_i2c["subadd"] == subadd_lsb)].tolist()
            indices_msb = df_i2c.index[(df_i2c["add"] == add) & (df_i2c["subadd"] == subadd_msb)].tolist()
            
            if not indices_lsb or not indices_msb:
                if interactive:
                    print(f"Multi-register not found: add={add}, subadd={subadd}")
                return None
                
            data_lsb = df_i2c.iloc[indices_lsb[0]]["data"]
            data_msb = df_i2c.iloc[indices_msb[0]]["data"]
            
            combined_data = data_msb + data_lsb
            return int(combined_data[(16 - position - nbbits):(16 - position)], 2)
        else:
            if interactive:
                print("Invalid subadd format for multi-register operation")
            return None
        

def save_file(filename=None):
    """Save the I2C register dataframe to a CSV file"""
    if filename is None:
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
    if filename:
        df_i2c.to_csv(filename, sep=',', index=False)
        if interactive:
            print(f"File saved to {filename}")
        return True
    
    return False


def load_file(filename=None):
    """Load I2C register data from a CSV file"""
    if filename is None:
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
    if filename:
        global df_i2c
        df = pd.read_csv(filename, index_col=None, dtype={"add": int, "subadd": int, "data": str})
        df_i2c = df.copy()
        if interactive:
            print(f"File loaded from {filename}")
        return True
    
    return False


# --- Example Usage ---

class I2CDeviceManager:
    """Class for managing I2C device registers"""
    
    def __init__(self):
        """Initialize the I2C device manager"""
        self.register_map = {}  # Store register info by name for easier access
        
    def initialize_dataframe(self, registers):
        """
        Initialize the I2C dataframe with a list of registers
        
        Parameters:
        registers: List of tuples (add, subadd, default_data)
        """
        global df_i2c
        df_i2c = pd.DataFrame(registers, columns=["add", "subadd", "data"])
        
    def define_register(self, name, add, subadd, nbbits=8, position=0, 
                       all_channels_add=False, all_channels_subadd=False):
        """Define a register for easier access"""
        self.register_map[name] = {
            "add": add,
            "subadd": subadd,
            "nbbits": nbbits,
            "position": position,
            "all_channels_add": all_channels_add,
            "all_channels_subadd": all_channels_subadd
        }
        
    def set_value(self, register_name, value):
        """Set a value to a named register"""
        if register_name not in self.register_map:
            if interactive:
                print(f"Register '{register_name}' not defined")
            return False
            
        return set_value(self.register_map[register_name], value)
        
    def get_value(self, register_name):
        """Get a value from a named register"""
        if register_name not in self.register_map:
            if interactive:
                print(f"Register '{register_name}' not defined")
            return None
            
        return get_register_value(self.register_map[register_name])
