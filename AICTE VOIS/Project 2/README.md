# Network Port Scanner GUI

A multi-threaded TCP port scanner with GUI.

## Features

* **Simple interface** – enter target host, start port, and end port  
* **Multi-threaded scanning** – uses multiple threads for faster scanning  
* **Service identification** – detects common services (HTTP, SSH, FTP, etc.)  
* **Real-time results** – open ports are displayed live during scanning  
* **Progress tracking** – progress bar and live scan status updates  
* **Elapsed time tracking** – displays total scan duration  
* **Save results** – export open ports to a `.txt` file  
* **Clear results** – reset output and start fresh  
* **Graceful stop** – allows stopping an ongoing scan  
* **Scrollable output** – supports large scan results  
* **Cross-platform** – works on Windows, macOS, and Linux  

## Requirements

* Python 3.7 or newer  
* Tkinter (usually included with Python; on Linux install `python3-tk`)  

No external libraries required.

## Usage

```bash
python portscanergui.py
```

1. Enter the **Target** (IP address or hostname)
2. Set the **Start Port** and **End Port**
3. Click **Start Scan**
4. Open ports will appear in real time
5. Click **Stop** to halt scanning

## Disclaimer

Use this tool only on systems you own or have permission to test. Unauthorized scanning may be illegal.

## License

MIT License

