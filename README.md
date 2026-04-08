# Biometric Attendance Sync Tool <span style="font-size: 0.6em; font-style: italic">(For ERPNext)</span>

Python Scripts to poll your biometric attendance system _(BAS)_ for logs and sync with your ERPNext instance


## Table of Contents
 - [Pre-requisites](#pre-requisites)
 - [Usage](#usage)
    - [GUI](#gui)
    - [CLI](#cli)
 - [Setup Specifications](#setup-specifications-(for-cli))
    - [UNIX](#unix)
    - [Windows](#windows)
  - [Setting Up Config](#setting-up-config)
  - [ZKBioTime API Integration](#zkbiotime-api-integration)
  - [Resources](#resources)
  - [License](#license)


## Pre-requisites
* Python 3.6+


## Usage
There's two ways you can use this tool. If accessing the CLI is a bit of a pain for you, the GUI has a simple form to guide you through the process.

Under [/releases](https://github.com/frappe/biometric-attendance-sync-tool/releases), for a particular release download the `biometric-attendance-sync-tool-[version]-[distribution].zip` and unzip it's contents. Now from the location of the unzipped files, you can go ahead with the CLI or GUI method.

### GUI
Run the `attendance-sync` file from the folder; This should setup all it's dependencies automatically and start the GUI.

### CLI
The `erpnext_sync.py` file is the "backbone" of this project. Apart from Windows _(which has its own wrapper `erpnext_sync_win.py`)_, this file can be directly used to set up the sync tool. Further information provided in the [/Wiki](https://github.com/frappe/biometric-attendance-sync-tool/wiki).


## Setup Specifications (For CLI)

1. Setup dependencies
    ```
    cd biometric-attendance-sync-tool
      && python3 -m venv venv
      && source venv/bin/activate
      && pip install -r requirements.txt
    ```
2. Setup `local_config.py`

   Make a copy of and rename `local_config.py.template` file. [Learn More](#setting-up-config)

3. Run this script using `python3 erpnext_sync.py`

### UNIX

There's a [Wiki](https://github.com/frappe/biometric-attendance-sync-tool/wiki/Running-this-script-in-production) for this.

### Windows

Installing as a Windows service

1. Install pywin32 using `pip install pywin32`
2. Got to this repository's Directory
3. Install the windows service using `python erpnext_sync_win.py install`
4. Done

#### Update the installed windows service
    python erpnext_sync_win.py update

#### Stop the windows service
    net stop ERPNextBiometricPushService

#### To see the status of the service
    mmc Services.msc


## Setting up config
- You need to make a copy of `local_config.py.template` file and rename it to `local_config.py`
- Please fill in the relevant sections in this file as per the comments in it.
- Below are the delineation of the keys contained in `local_config.py`:
  - ERPNext connection configs:
    - `ERPNEXT_API_KEY`: The API Key of the ERPNext User
    - `ERPNEXT_API_SECRET`: The API Secret of the ERPNext User

      > Please refer to [this link](https://frappe.io/docs/user/en/guides/integration/how_to_set_up_token_based_auth#generate-a-token) to learn how to generate API key and secret for a user in ERPNext.
      > The ERPNext User who's API key and secret is used, needs to have at least the following permissions:
      > 1. Create Permissions for 'Employee Checkin' DocType.
      > 2. Write Permissions for 'Shift Type' DocType.

    - `ERPNEXT_URL`: The web address at which you would access your ERPNext. eg:`'https://yourcompany.erpnext.com'`, `'https://erp.yourcompany.com'`
    - `ERPNEXT_VERSION`: The base version of your ERPNext app. eg: 12, 13, 14
  - This script's operational configs:
    - `PULL_FREQUENCY`: The time in minutes after which a pull for punches from the biometric device and push to ERPNext is attempted again.
    - `LOGS_DIRECTORY`: The Directory in which the logs related to this script's whereabouts are stored.
      > Hint: For most cases you can leave the above two keys unchanged.
    - `IMPORT_START_DATE`: The date after which the punches are pushed to ERPNext. Expected Format: `YYYYMMDD`.
      > For some cases you would have a lot of old punches in the biometric device. But, you would want to only import punches after certain date. You could set this key appropriately. Also, you can leave this as `None` if this case does not apply to you.

> TODO: fill this section with more info to help Non-Technical Individuals.

## ZKBioTime API Integration

This tool supports an alternative mode of fetching attendance data via the **ZKBioTime REST API** instead of connecting directly to biometric devices using the ZK protocol. This is useful when:

- Biometric devices are behind a firewall or NAT and not directly accessible
- You already use a ZKBioTime server to manage devices centrally
- You prefer server-side polling over direct device connections

### How It Works

Instead of using `pyzk` to connect to each device individually, the tool queries the ZKBioTime server's API endpoints:
- `GET /iclock/api/terminals/` — list registered devices
- `GET /iclock/api/transactions/` — fetch attendance logs with pagination

The adapter (`zkbiotime_adapter.py`) handles authentication, pagination, and converts the response into the standard attendance log format expected by `erpnext_sync.py`.

### Configuration

Add the following to your `local_config.py`:

```python
# ZKBioTime API Configuration
USE_ZKBIOTIME_API = True
ZKBIOTIME_URL = "http://your-zkbiotime-server:port"
ZKBIOTIME_USERNAME = "admin"
ZKBIOTIME_PASSWORD = "your_password"
```

### Multiple ZKBioTime Servers

If your biometric devices are managed by **different ZKBioTime servers**, each device can specify its own server URL:

```python
USE_ZKBIOTIME_API = True

devices = [
    # Old device on one ZKBioTime server
    {
        'device_id': 'old_device_1',
        'ip': '192.168.1.100',
        'punch_direction': 'AUTO',
        'clear_from_device_on_fetch': False,
        'zkbiotime_url': 'http://old-server:81',
        'zkbiotime_username': 'admin',
        'zkbiotime_password': 'admin@123',
    },
    # New device on a different ZKBioTime server
    {
        'device_id': 'new_device_1',
        'ip': '192.168.2.200',
        'punch_direction': 'AUTO',
        'clear_from_device_on_fetch': False,
        'zkbiotime_url': 'http://new-server:81',
        'zkbiotime_username': 'admin',
        'zkbiotime_password': 'different_password',
    },
]
```

Devices without `zkbiotime_url` fall back to the global `ZKBIOTIME_URL`.

When `USE_ZKBIOTIME_API` is `True`, the tool bypasses direct device connections and fetches attendance from the respective ZKBioTime server. The device `ip` field is still used to match config entries to server config.

### Testing the Connection

A standalone test script (`test_zkbiotime.py`) is included to verify API connectivity before running the full sync:

```bash
python test_zkbiotime.py
```

This will authenticate, list devices, and fetch recent transactions to confirm everything is working.

### Known Limitations

- The adapter fetches **all** transactions across all devices; device-level filtering is done downstream
- Token re-authentication happens on each instantiation (no caching)
- No retry logic for transient API failures

These are areas for future improvement.

---

## To build executable file for GUI
### Linux and Windows:
1. Activate virtual environment.
1. Navigate to the repository folder (where `gui.py` located) by
    ```
    cd biometric-attendance-sync-tool
    ```
1. Run the following commands:
    ```
    pip install pyinstaller
    ```

    ```
    python -m PyInstaller --name="attendance-sync" --windowed --onefile gui.py
    ```
1. The executable file `attendance-sync` created inside `dist/` folder.

### Resources

* Article on [ERPNext Documentation](https://docs.erpnext.com/docs/user/manual/en/setting-up/articles/integrating-erpnext-with-biometric-attendance-devices).
* This Repo's [/Wiki](https://github.com/frappe/biometric-attendance-sync-tool/wiki).

### License

This project is licensed under [GNU General Public License v3.0](LICENSE)