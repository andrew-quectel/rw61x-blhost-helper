# NXP RW61x BLHOST Helper Script

A simple Python helper script for NXP RW61x chip programming using the BLHOST command-line interface. This tool provides an easy-to-use interface for erasing, writing, and reading operations on RW61x chips with external QSPI flash.

## Features

- **RW61x Support**: Specifically designed for RW61x chip family
- **Interface Support**: USB and UART connections
- **Flash Operations**: Erase, write (program), and read flash memory
- **Interactive Mode**: User-friendly prompts for device configuration
- **Progress Tracking**: Real-time progress indication for operations

## Prerequisites

### Software Requirements

1. **Python 3.6+**: Ensure Python is installed and available in your PATH
2. **NXP SPSDK**: Install using pip to get the BLHOST tool
   ```bash
   pip install spsdk
   ```
   This provides the `blhost` command-line tool as part of the NXP Secure Provisioning SDK

### Hardware Requirements

- NXP RW61x development board or target device
- USB connection (for USB interface) or UART connection (for UART interface)
- Device must be in bootloader mode

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/andrew-quectel/rw61x-blhost-helper.git
   cd nxp-blhost-tool
   ```

2. **Install dependencies**:
   ```bash
   pip install spsdk
   ```

3. **Verify BLHOST installation**:
   ```bash
   blhost --version
   ```

## Project Structure

```
blhost_tool/
├── blhost_helper.py           # Main RW61x BLHOST helper script
├── device_config.json         # RW61x device configuration
├── fcb/                       # Flash Configuration Block files
└── output/                    # Output directory for read operations
```

## Usage

### Command Line Arguments

```bash
python blhost_helper.py [OPTIONS] [OPERATION]
```

#### Device Parameters
- `-d, --device`: RW61x device model (FCM363X, FCM363XL, FCM365X, FCMA62N, FRDMRW612, RDRW612BGA)
- `-i, --interface`: Connection interface (usb, uart)
- `-c, --com`: COM port (required for UART)
- `-b, --baudrate`: Baud rate (optional for UART, default: 2000000)
- `--debug`: Enable detailed debug information

#### Operations
- `--test`: Test device connection
- `--read`: Read flash memory
- `--write`: Write firmware to flash
- `--erase`: Erase flash memory
- `--list`: List supported devices

#### Parameters
- `-a, --addr`: Memory address (e.g., 0x08000000)
- `-s, --size`: Size in bytes (e.g., 0x1000)
- `-f, --file`: Firmware file path
- `-o, --output`: Output file path

### Usage Examples

#### 1. List Supported RW61x Devices
```bash
python blhost_helper.py --list
```

#### 2. Test Device Connection
```bash
# USB connection
python blhost_helper.py -d FCM363X -i usb --test

# UART connection
python blhost_helper.py -d FCM363X -i uart -c COM3 --test
```

#### 3. Read Flash Memory
```bash
# Read with default parameters
python blhost_helper.py -d FCM363X -i usb --read

# Read specific address and size
python blhost_helper.py -d FCM363X -i usb --read -a 0x08000400 -s 0x1000 -o firmware_backup.bin
```

#### 4. Erase Flash Memory
```bash
# Interactive erase (prompts for region and size)
python blhost_helper.py -d FCM363X -i usb --erase

# Erase specific region
python blhost_helper.py -d FCM363X -i usb --erase -a 0x08000000 -s 0x100000

# Erase from specific address (prompts for size)
python blhost_helper.py -d FCM363X -i usb --erase -a 0x08000000
```

#### 5. Write Firmware
```bash
# Write firmware to default address
python blhost_helper.py -d FCM363X -i usb --write -f firmware.bin

# Write firmware to specific address
python blhost_helper.py -d FCM363X -i usb --write -f firmware.bin -a 0x08000000
```

#### 6. Debug Mode
```bash
# Enable debug output for troubleshooting
python blhost_helper.py -d FCM363X -i usb --test --debug
```

## Supported RW61x Devices

| Device     | Interfaces  | Flash Sizes | FCB File |
|------------|-------------|-------------|----------|
| FCM363X    | UART, USB   | 8M, 16M     | fcm363x.fcb.bin |
| FCM363XL   | UART        | 8M          | fcm363xl.fcb.bin |
| FCM365X    | UART, USB   | 8M          | fcm365x.fcb.bin |
| FCMA62N    | UART        | 8M          | fcma62n.fcb.bin |
| FRDMRW612  | UART        | 64M         | frdmrw612.fcb.bin |
| RDRW612BGA | UART        | 64M         | rdrw612bga.fcb.bin |

## Flash Memory Regions

The tool supports two main flash regions:

1. **NS (Non-Secure) Region**: 
   - Start Address: `0x08000000`
   - Read Address: `0x08000400`
   - Default region for most operations

2. **S (Secure) Region**: 
   - Start Address: `0x18000000`
   - Read Address: `0x18000400`

## Configuration

RW61x device configurations are stored in `device_config.json`. You can modify this file to add new RW61x variants or update existing configurations:

```json
{
    "devices": {
        "DEVICE_NAME": {
            "fcb_file": "device.fcb.bin",
            "interfaces": ["uart", "usb"],
            "flash_sizes": ["8M", "16M"]
        }
    }
}
```

## Troubleshooting

### Common Issues

1. **Device Not Found**
   - Ensure RW61x device is in bootloader mode
   - Check USB/UART connections
   - Verify correct COM port for UART

2. **BLHOST Command Not Found**
   - Install NXP SPSDK: `pip install spsdk`
   - Verify installation with `blhost --version`

3. **Permission Errors**
   - Run with administrator privileges on Windows
   - Check COM port permissions on Linux

4. **FCB File Missing**
   - Ensure FCB files are in the `fcb/` directory
   - Check device configuration in `device_config.json`

### Debug Mode

Use the `--debug` flag to enable detailed logging:

```bash
python blhost_helper.py -d FCM363X -i usb --test --debug
```

This will show:
- Full command line being executed
- STDOUT and STDERR from BLHOST
- Return codes
- Detailed error messages
