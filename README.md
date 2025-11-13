# NXP RW61x BLHOST Helper Script

A simple Python helper script for NXP RW61x chip programming using the BLHOST command-line interface. This tool provides an easy-to-use interface for erasing, writing, and reading operations on RW61x chips with external QSPI flash.

## Features

- **Flexible Device Configuration**: JSON-based device definitions with support for device categories and variants
- **Multiple Device Support**: Quectel modules (FCM363X, FCM363XL, FGMH63X, FCME63X, FCM365X, FCMA62N) and NXP development boards
- **Smart Interface Selection**: Auto-selects default interface (USB/UART) based on device configuration
- **Flash-based FCB Files**: FCB files named by flash chip manufacturer and model, reducing duplication
- **Interface Support**: USB and UART connections with automatic defaults
- **Flash Operations**: Erase, write (program), and read flash memory
- **Interactive Mode**: User-friendly prompts for variant selection, flash region, and size
- **Progress Tracking**: Real-time progress indication for operations
- **Cross-Platform**: Supports Windows COM ports and Linux serial ports (/dev/ttyUSB*)

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
rw61x-blhost-helper/
├── blhost_helper.py           # Main RW61x BLHOST helper script
├── device_config.json         # Device configuration (categories, variants, flash configs)
├── fcb/                       # Flash Configuration Block files (named by flash chip)
│   └── ...
├── output/                    # Output directory for read operations
└── README.md                  # This file
```

## Usage

### Command Line Arguments

```bash
python blhost_helper.py [OPTIONS] [OPERATION]
```

#### Device Parameters
- `-d, --device`: Device model (category or specific variant)
  - Category: FCM363X, FCM363XL, FGMH63X, FCME63X, FCM365X, FCMA62N, FRDMRW612, RDRW612BGA
  - Variant: FCM363XAB, FCM363XAC, FCM363XLAA, FCM363XLAB, FCM363XLAC, etc.
- `-i, --interface`: Connection interface (usb, uart) - optional if default is configured
- `-p, --port`: Serial port (required for UART)
  - Windows: COM3, COM4, etc.
  - Linux: /dev/ttyUSB0, /dev/ttyUSB1, etc.
- `-b, --baudrate`: Baud rate (optional for UART, default: 2000000)
- `--debug`: Enable detailed debug information

#### Operations
- `--test`: Test device connection
- `--read`: Read flash memory
- `--write`: Write firmware to flash
- `--erase`: Erase flash memory
- `--list`: List supported devices

#### Parameters
- `-a, --addr`: Memory address (e.g., 0x08000000) - optional, will prompt if needed
- `-s, --size`: Size in bytes (e.g., 0x1000) - optional, will prompt if needed
- `-f, --file`: Firmware file path (required for write operation)
- `-o, --output`: Output file path (optional for read operation)

### Usage Examples

#### 1. List Supported Devices
```bash
python blhost_helper.py --list
```

This displays all supported devices with their variants, interfaces, and flash configurations.

#### 2. Test Device Connection

**Using default interface (USB for most devices):**
```bash
# FCM363X - prompts to select variant if not specified
python blhost_helper.py -d FCM363X --test

# Specific variant - no prompt needed
python blhost_helper.py -d FCM363XAB --test
python blhost_helper.py -d FGMH63X --test
```

**Using UART (default for some devices like FCM363XL):**
```bash
# Windows
python blhost_helper.py -d FCM363XL -p COM3 --test
python blhost_helper.py -d FCMA62N -p COM5 --test

# Linux
python blhost_helper.py -d FCM363XL -p /dev/ttyUSB0 --test
```

**Override default interface:**
```bash
python blhost_helper.py -d FCM363X -i uart -p COM3 --test
```

#### 3. Read Flash Memory
```bash
# Read with default parameters
python blhost_helper.py -d FCM363X --read

# Read specific address and size
python blhost_helper.py -d FCM363XAB --read -a 0x08000400 -s 0x1000 -o firmware_backup.bin

# Read from UART device
python blhost_helper.py -d FCM363XLAC -p COM3 --read -a 0x08000400 -s 0x200
```

#### 4. Erase Flash Memory
```bash
# Interactive erase (prompts for region and size)
python blhost_helper.py -d FCM363X --erase

# Erase specific region with size
python blhost_helper.py -d FGMH63X --erase -a 0x08000000 -s 0x1000000

# Erase from specific address (prompts for size)
python blhost_helper.py -d FCME63X --erase -a 0x08000000
```

#### 5. Write Firmware
```bash
# Write firmware (uses default address 0x08000000)
python blhost_helper.py -d FCM363XAC --write -f firmware.bin

# Write to specific address
python blhost_helper.py -d FCM363XLAC -p COM3 --write -f app.bin -a 0x08000000

# Write to devices with different flash sizes
python blhost_helper.py -d FCME63X --write -f firmware_32m.bin
python blhost_helper.py -d FGMH63X --write -f firmware_16m.bin
```

#### 6. Debug Mode
```bash
# Enable debug output for troubleshooting
python blhost_helper.py -d FCM363X --test --debug
python blhost_helper.py -d FGMH63X --write -f test.bin --debug
```

## Supported Devices

### Quectel Modules

| Category | Variant | Description | Flash | Default Interface |
|----------|---------|-------------|-------|-------------------|
| **FCM363X** | FCM363XAB | FCM363XAB with 8M Flash | 8M | USB |
| | FCM363XAC | FCM363XAC with 8M Flash & 8M pSRAM | 8M | USB |
| **FCM363XL** | FCM363XLAA | FCM363X-L with 8M Flash | 8M | UART |
| | FCM363XLAB | FCM363X-L with 8M Flash & 8M pSRAM | 8M | UART |
| | FCM363XLAC | FCM363X-L with 16M Flash & 8M pSRAM | 16M | UART |
| **FGMH63X** | FGMH63X | FGMH63X with 16M Flash & 8M pSRAM | 16M | USB |
| **FCME63X** | FCME63X | FCME63X with 32M Flash & 8M pSRAM | 32M | USB |
| **FCM365X** | FCM365X | FCM365X with 8M Flash | 8M | USB |
| **FCMA62N** | FCMA62N | FCMA62N with 8M Flash | 8M | UART |

### NXP Development Boards

| Category | Variant | Description | Flash | Default Interface |
|----------|---------|-------------|-------|-------------------|
| **FRDMRW612** | FRDMRW612 | FRDM-RW612 development board | 64M | UART |
| **RDRW612BGA** | RDRW612BGA | RD-RW612-BGA development board | 64M | UART |

### Flash Chip Mapping

FCB files are named according to the flash chip manufacturer and model:

| Flash Chip | Capacity | FCB File | Used By |
|------------|----------|----------|---------|
| XMC XM25QH64D | 8MB | XMC_XM25QH64D.bin | FCM363XAB, FCM363XAC, FCMA62N |
| XMC XM25QH128D | 16MB | XMC_XM25QH128D.bin | FGMH63X |
| MXIC MX25L6433F | 8MB | MXIC_MX25L6433F.bin | FCM363XLAA, FCM363XLAB, FCM365X |
| MXIC MX25L12845G | 16MB | MXIC_MX25L12845G.bin | FCM363XLAC |
| MXIC MX25L25645G | 32MB | MXIC_MX25L25645G.bin | FCME63X |
| MXIC MX25U51245G | 64MB | MXIC_MX25U51245G.bin | RDRW612BGA |
| Winbond W25Q512JV | 64MB | Winbond_W25Q512JV.bin | FRDMRW612 |

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

Device configurations are stored in `device_config.json`. This file defines:
- Device categories and variants
- Supported interfaces and default interface
- Flash configurations with corresponding FCB files
- Default flash size for each variant

### Configuration Structure

```json
{
    "devices": {
        "CATEGORY_NAME": {
            "description": "Device description",
            "interfaces": ["uart", "usb"],
            "default_interface": "usb",
            "variants": {
                "VARIANT_NAME": {
                    "description": "Variant description",
                    "flash_configs": {
                        "8M": {
                            "fcb_file": "MXIC_MX25L6433F.bin",
                            "default": true
                        },
                        "16M": {
                            "fcb_file": "MXIC_MX25L12845G.bin",
                            "default": false
                        }
                    }
                }
            }
        }
    }
}
```

### Adding New Devices

1. **Identify the flash chip** used in your device
2. **Check if FCB file exists** in the `fcb/` directory
   - If yes, reuse the existing file
   - If no, create a new FCB file named: `<Manufacturer>_<Model>.bin`
3. **Add device configuration** to `device_config.json`:

```json
"NEWDEVICE": {
    "description": "New device description",
    "interfaces": ["uart", "usb"],
    "default_interface": "usb",
    "variants": {
        "NEWDEVICEA": {
            "description": "New device variant A with 8M Flash",
            "flash_configs": {
                "8M": {
                    "fcb_file": "MXIC_MX25L6433F.bin",
                    "default": true
                }
            }
        }
    }
}
```

**Benefits of this approach:**
- No need to edit Python source code
- FCB files are reusable across devices with same flash chip
- Easy to add new devices and variants
- Clear mapping between devices and flash configurations

## Troubleshooting

### Common Issues

1. **Device Not Found**
   - Ensure device is in bootloader mode
   - Check USB/UART connections
   - Verify correct serial port for UART
   - Windows: Check Device Manager for COM port
   - Linux: Check `ls /dev/ttyUSB*` or `dmesg | tail`

2. **BLHOST Command Not Found**
   - Install NXP SPSDK: `pip install spsdk`
   - Verify installation: `blhost --version`
   - Ensure Python Scripts directory is in PATH

3. **Permission Errors (Linux)**
   - Add user to dialout group: `sudo usermod -a -G dialout $USER`
   - Logout and login again
   - Or use sudo: `sudo python blhost_helper.py ...`

4. **FCB File Missing**
   - Ensure FCB files are in the `fcb/` directory
   - Check device configuration in `device_config.json`
   - Verify FCB file name matches configuration

5. **Wrong Interface Selected**
   - Some devices default to USB, others to UART
   - Use `-i` option to override: `-i uart` or `-i usb`
   - Check default interface with `--list`

6. **Variant Selection Prompt**
   - If device category has multiple variants, you'll be prompted
   - To avoid prompt, specify exact variant: `-d FCM363XAB`
   - Or choose when prompted

### Debug Mode

Use the `--debug` flag to enable detailed logging:

```bash
python blhost_helper.py -d FCM363X --test --debug
```

This will show:
- Full BLHOST command line being executed
- STDOUT and STDERR from BLHOST
- Return codes
- JSON parsing details
- Detailed error messages

### Getting Help

```bash
# Show help message
python blhost_helper.py -h

# List all supported devices
python blhost_helper.py --list
```
