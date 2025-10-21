#!/usr/bin/env python3
"""
NXP RW61x BLHOST Helper Script
A simple helper script for NXP RW61x chip programming using BLHOST
Provides easy-to-use interface for erase, write and read operations
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

class BlhostHelper:
    """NXP RW61x BLHOST Helper Class"""
    
    # Fixed configuration constants
    USB_PARAMS = "-u 0x1FC9,0x0020"
    DEFAULT_BAUDRATE = 2000000
    DEFAULT_READ_SIZE = "0x200"
    MAX_ERASE_BLOCK = 0x100000  # 1MB
    
    # FLASH size mapping
    FLASH_SIZE_MAPPING = {
        "8M": 0x800000,     # 8MB
        "16M": 0x1000000,   # 16MB  
        "64M": 0x4000000,   # 64MB
    }
    
    # FLASH region definitions
    FLASH_REGIONS = {
        "NS": {
            "name": "External QSPI flash (NS)",
            "start_addr": 0x08000000,
            "read_addr": 0x08000400
        },
        "S": {
            "name": "External QSPI flash (S)", 
            "start_addr": 0x18000000,
            "read_addr": 0x18000400
        }
    }
    
    def __init__(self, debug=False):
        self.debug = debug
        self.script_dir = Path(__file__).parent
        self.config_file = self.script_dir / "device_config.json"
        self.fcb_dir = self.script_dir / "fcb"
        self.output_dir = self.script_dir / "output"
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Connection parameters
        self.device_model = None
        self.interface = None
        self.connection_params = None
    
    def _load_config(self):
        """Load device configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error: Cannot load config file {self.config_file}: {e}")
            sys.exit(1)
    
    def setup_device(self, device_model, interface, com_port=None, baudrate=None):
        """Setup device connection parameters"""
        # Validate device
        if device_model not in self.config["devices"]:
            print(f"Error: Unsupported device model: {device_model}")
            return False
        
        device_config = self.config["devices"][device_model]
        
        # Validate interface
        if interface not in device_config["interfaces"]:
            print(f"Error: Device {device_model} does not support {interface.upper()} interface")
            return False
        
        self.device_model = device_model
        self.interface = interface
        
        # Set connection parameters
        if interface == "usb":
            self.connection_params = self.USB_PARAMS
        else:  # uart
            if not com_port:
                print("Error: UART interface requires COM port specification")
                return False
            
            baud = baudrate or self.DEFAULT_BAUDRATE
            self.connection_params = f"-p {com_port},{baud}"
        
        print(f"Device: {device_model}")
        print(f"Interface: {interface.upper()}")
        print(f"Connection params: {self.connection_params}")
        return True
    
    def run_command(self, command, use_json=True):
        """Execute blhost command"""
        json_flag = "-j " if use_json else ""
        full_command = f"blhost {self.connection_params} {json_flag}-- {command}"
        
        if self.debug:
            print(f"Executing: {full_command}")
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Debug output
            if self.debug:
                if result.stdout:
                    print(f"STDOUT: {result.stdout}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                print(f"Return code: {result.returncode}")
            
            if use_json and result.returncode == 0 and result.stdout.strip():
                try:
                    json_data = json.loads(result.stdout)
                    return json_data
                except json.JSONDecodeError as e:
                    print(f"JSON parsing failed: {e}")
                    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            print("❌ Command execution timeout")
            return None
        except Exception as e:
            print(f"❌ Command execution error: {e}")
            return None
    
    def test_connection(self):
        """Test device connection"""
        print("Testing device connection...")
        result = self.run_command("get-property 1 0")
        
        if result:
            # If JSON format response
            if isinstance(result, dict) and "status" in result:
                status = result.get("status", {})
                if isinstance(status, dict) and status.get("value") == 0:
                    print("✅ Device connection successful")
                    if "response" in result and result["response"]:
                        version = result["response"][0]
                        print(f"Device version: 0x{version:08X}")
                    return True
                else:
                    print("❌ Device response status error")
                    print(f"Status: {status}")
                    return False
            
            # If not JSON but command executed successfully
            elif result.get("returncode") == 0:
                print("✅ Device connection successful (non-JSON response)")
                return True
            
            # Command execution failed
            else:
                print("❌ Device connection failed")
                if result.get("stderr"):
                    if "SpsdkNoDeviceFoundError" in result["stderr"]:
                        print("Device not found, please check connection and bootloader mode")
                    else:
                        print(f"Error: {result['stderr']}")
                return False
        
        print("❌ Cannot get command result")
        return False
    
    def initialize_flash(self):
        """Initialize FLASH"""
        print("Initializing FLASH...")
        
        device_config = self.config["devices"][self.device_model]
        fcb_file = self.fcb_dir / device_config["fcb_file"]
        
        if not fcb_file.exists():
            print(f"❌ FCB file does not exist: {fcb_file}")
            return False
        
        commands = [
            "fill-memory 0x2000F000 4 0xC0100002 word",
            f"write-memory 0x2000F000 {fcb_file}",
            "configure-memory 9 0x2000F000"
        ]
        
        for cmd in commands:
            result = self.run_command(cmd, use_json=False)
            if not result or result.get("returncode", 1) != 0:
                print(f"❌ Initialization failed: {cmd}")
                return False
        
        print("✅ FLASH initialization successful")
        return True
    
    def get_flash_size_options(self):
        """Get FLASH size options for current device"""
        if not self.device_model:
            return []
        
        device_config = self.config["devices"].get(self.device_model, {})
        return device_config.get("flash_sizes", [])
    
    def convert_flash_size_to_bytes(self, size_str):
        """Convert FLASH size string to bytes"""
        return self.FLASH_SIZE_MAPPING.get(size_str, None)
    
    def prompt_flash_region_selection(self):
        """Prompt user to select FLASH region"""
        print("\nPlease select FLASH region:")
        regions = list(self.FLASH_REGIONS.items())
        
        for i, (key, region) in enumerate(regions, 1):
            print(f"  {i}. {region['name']} (0x{region['start_addr']:08X})")
        
        try:
            choice = input(f"Please select (1-{len(regions)}, Enter=NS region): ").strip()
            
            if not choice:
                return "NS"  # Default NS region
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(regions):
                return regions[choice_idx][0]
                
        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled")
            return None
        
        return "NS"  # Default
    
    def prompt_flash_size_selection(self):
        """Prompt user to select FLASH size"""
        options = self.get_flash_size_options()
        if not options:
            return None
        
        print(f"\nSupported FLASH sizes for device {self.device_model}:")
        for i, size in enumerate(options, 1):
            size_bytes = self.convert_flash_size_to_bytes(size)
            if size_bytes:
                print(f"  {i}. {size} ({size_bytes:0,} bytes, 0x{size_bytes:X})")
            else:
                print(f"  {i}. {size}")
        
        print(f"  {len(options) + 1}. Full erase (entire FLASH)")
        
        try:
            choice = input("Please select (1-{}, Enter=full erase): ".format(len(options) + 1)).strip()
            
            if not choice or choice == str(len(options) + 1):
                # Full erase, use default FLASH size
                default_size = self.config["devices"][self.device_model].get("default_flash_size")
                if default_size:
                    return self.convert_flash_size_to_bytes(default_size)
                return None
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                return self.convert_flash_size_to_bytes(options[choice_idx])
            
        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled")
            return None
        
        return None
    
    def erase_flash(self, start_addr=None, size=None):
        """Erase FLASH"""
        if not self.initialize_flash():
            return False
        
        # Handle address parameter
        if start_addr is None:
            # If no address specified, prompt user to select FLASH region
            region_key = self.prompt_flash_region_selection()
            if region_key is None:
                print("❌ No valid FLASH region selected")
                return False
            
            region = self.FLASH_REGIONS[region_key]
            start_int = region['start_addr']
            start_addr = f"0x{start_int:08X}"
            print(f"Selected FLASH region: {region['name']} ({start_addr})")
        else:
            if isinstance(start_addr, str):
                if not start_addr.startswith('0x'):
                    start_addr = f"0x{start_addr}"
            start_int = int(start_addr, 16)
        
        # Handle size parameter
        if size is None:
            # If no size specified, prompt user to select FLASH size for full erase
            flash_options = self.get_flash_size_options()
            if len(flash_options) == 1:
                # Only one option, use it directly
                size_bytes = self.convert_flash_size_to_bytes(flash_options[0])
                print(f"Auto-selected FLASH size: {flash_options[0]} ({size_bytes:0,} bytes) - full erase")
            else:
                # Multiple options, let user choose
                size_bytes = self.prompt_flash_size_selection()
                if size_bytes is None:
                    print("❌ No valid FLASH size selected")
                    return False
        else:
            # User specified size
            if isinstance(size, str):
                size_bytes = int(size, 0)
            else:
                size_bytes = size
        
        if size_bytes is None or size_bytes <= 0:
            print("❌ Invalid erase size")
            return False
        
        print(f"Starting FLASH erase: {start_addr}, size: {size_bytes:0,} bytes")
        
        addr = start_int
        remaining = size_bytes
        
        while remaining > 0:
            block_size = min(remaining, self.MAX_ERASE_BLOCK)
            addr_hex = f"0x{addr:08X}"
            size_hex = f"0x{block_size:X}"
            
            progress = ((size_bytes - remaining) / size_bytes) * 100
            print(f"Erase progress: {progress:.1f}% - {addr_hex} ({size_hex})")
            
            result = self.run_command(f"flash-erase-region {addr_hex} {size_hex} 0", use_json=False)
            if not result or result.get("returncode", 1) != 0:
                print(f"❌ Erase failed: {addr_hex}")
                return False
            
            addr += block_size
            remaining -= block_size
        
        print("✅ FLASH erase completed")
        return True
    
    def write_firmware(self, firmware_path, start_addr=None):
        """Write firmware"""
        if not os.path.exists(firmware_path):
            print(f"❌ Firmware file does not exist: {firmware_path}")
            return False
        
        if not start_addr:
            start_addr = f"0x{self.FLASH_REGIONS['NS']['start_addr']:08X}"
        
        file_size = os.path.getsize(firmware_path)
        if file_size == 0:
            print("❌ Firmware file is empty")
            return False
        
        print(f"Firmware file: {firmware_path} ({file_size} bytes)")
        
        # Erase FLASH
        if not self.erase_flash(start_addr, file_size):
            return False
        
        # Write firmware
        print(f"Starting firmware write to {start_addr}...")
        result = self.run_command(f"write-memory {start_addr} {firmware_path}", use_json=False)
        
        if result and result.get("returncode") == 0:
            print("✅ Firmware write successful")
            return True
        else:
            print("❌ Firmware write failed")
            return False
    
    def read_flash(self, start_addr=None, size=None, output_file=None):
        """Read FLASH contents"""
        if not self.initialize_flash():
            return False
        
        # Set default values
        if not start_addr:
            start_addr = f"0x{self.FLASH_REGIONS['NS']['read_addr']:08X}"
        if not size:
            size = self.DEFAULT_READ_SIZE
        
        # Format address
        if not start_addr.startswith('0x'):
            start_addr = f"0x{start_addr}"
        
        # Generate output filename
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"{self.device_model}_{start_addr}_{timestamp}.bin"
        else:
            output_file = Path(output_file)
        
        print(f"Reading FLASH: {start_addr}, size: {size}")
        print(f"Output file: {output_file}")
        
        # Read data
        result = self.run_command(f"read-memory {start_addr} {size}", use_json=False)
        
        if not result or result.get("returncode", 1) != 0:
            print("❌ FLASH read failed")
            return False
        
        # Parse hex output
        hex_data = result.get("stdout", "")
        if self._parse_hex_to_file(hex_data, output_file):
            print("✅ FLASH read successful")
            return True
        else:
            print("❌ Hex data parsing failed")
            return False
    
    def _parse_hex_to_file(self, hex_output, output_path):
        """Parse hex output and save as file"""
        try:
            lines = hex_output.strip().split('\n')
            binary_data = bytearray()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('{'):
                    break
                
                # Check if it's a hex data line
                if all(c in '0123456789ABCDEFabcdef ' for c in line):
                    hex_bytes = line.split()
                    for hex_byte in hex_bytes:
                        if len(hex_byte) == 2 and all(c in '0123456789ABCDEFabcdef' for c in hex_byte):
                            binary_data.append(int(hex_byte, 16))
            
            if not binary_data:
                print("❌ No valid hex data found")
                return False
            
            # Save file
            with open(output_path, 'wb') as f:
                f.write(binary_data)
            
            print(f"Saved {len(binary_data)} bytes to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error parsing hex data: {e}")
            return False

def list_devices():
    """List supported devices"""
    try:
        config_file = Path(__file__).parent / "device_config.json"
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("Supported devices:")
        print("-" * 50)
        for name, device_config in config["devices"].items():
            interfaces = ", ".join(device_config["interfaces"])
            flash_sizes = ", ".join(device_config["flash_sizes"])
            print(f"{name:12} | {interfaces:10} | {flash_sizes}")
        
    except Exception as e:
        print(f"❌ Cannot load device list: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="NXP RW61x BLHOST Helper Script",
        epilog="""
Usage examples:
  # List devices
  python %(prog)s --list
  
  # Test connection
  python %(prog)s -d FCM363X -i usb --test
  
  # Read FLASH
  python %(prog)s -d FCM363X -i usb --read -a 0x08000400 -s 0x200 -o test.bin
  
  # Erase FLASH (address and size are optional)
  python %(prog)s -d FCM363X -i usb --erase -a 0x08000000 -s 0x1000
  python %(prog)s -d FCM363X -i usb --erase -a 0x08000000  
  python %(prog)s -d FCM363X -i usb --erase
  
  # Write firmware
  python %(prog)s -d FCM363X -i usb --write -f firmware.bin -a 0x08000000
  
  # Enable debug output
  python %(prog)s -d FCM363X -i usb --test --debug
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Device parameters
    parser.add_argument('-d', '--device', 
                       choices=['FCM363X', 'FCM363XL', 'FCM365X', 'FCMA62N', 'FRDMRW612', 'RDRW612BGA'],
                       help='Device model')
    parser.add_argument('-i', '--interface', 
                       choices=['usb', 'uart'],
                       help='Connection interface')
    parser.add_argument('-c', '--com', 
                       help='COM port (required for UART)')
    parser.add_argument('-b', '--baudrate', type=int,
                       help='Baud rate (optional for UART)')
    parser.add_argument('--debug', action='store_true',
                       help='Show detailed debug information')
    
    # Operations
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--test', action='store_true', help='Test connection')
    group.add_argument('--read', action='store_true', help='Read FLASH')
    group.add_argument('--write', action='store_true', help='Write firmware')
    group.add_argument('--erase', action='store_true', help='Erase FLASH')
    group.add_argument('--list', action='store_true', help='List supported devices')
    
    # Parameters
    parser.add_argument('-a', '--addr', help='Address (e.g.: 0x08000000, optional)')
    parser.add_argument('-s', '--size', help='Size (e.g.: 0x1000, optional)')
    parser.add_argument('-f', '--file', help='File path')
    parser.add_argument('-o', '--output', help='Output file')
    
    args = parser.parse_args()
    
    # List devices
    if args.list:
        list_devices()
        return 0
    
    # Need device and interface parameters
    if not args.device or not args.interface:
        if not any([args.test, args.read, args.write, args.erase]):
            parser.print_help()
            return 0
        print("❌ Device model and interface must be specified")
        return 1
    
    # UART requires COM port
    if args.interface == 'uart' and not args.com:
        print("❌ UART interface requires COM port specification")
        return 1
    
    # Create helper instance
    tool = BlhostHelper(debug=args.debug)
    
    # Setup device
    if not tool.setup_device(args.device, args.interface, args.com, args.baudrate):
        return 1
    
    print("-" * 50)
    
    # Execute operation
    success = False
    
    if args.test:
        success = tool.test_connection()
    
    elif args.read:
        success = tool.read_flash(args.addr, args.size, args.output)
    
    elif args.write:
        if not args.file:
            print("❌ Write operation requires file specification")
            return 1
        success = tool.write_firmware(args.file, args.addr)
    
    elif args.erase:
        # Address and size parameters are optional, user will be prompted if not specified
        success = tool.erase_flash(args.addr, args.size)
    
    else:
        # Default test connection
        success = tool.test_connection()
    
    print("-" * 50)
    print("✅ Operation successful" if success else "❌ Operation failed")
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nUser interrupted operation")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unknown error: {e}")
        sys.exit(1)
