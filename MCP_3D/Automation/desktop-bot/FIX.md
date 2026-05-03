## Troubleshooting PyAutoGUI Installation

### Linux-Specific PyAutoGUI Issues

#### Common Problems
- Missing system libraries
- X11 dependencies not installed
- Virtual environment configuration issues

#### Troubleshooting Steps

1. **Install System Dependencies**
   ```bash
   # Fedora
   sudo dnf install -y \
       python3-devel \
       libXtst-devel \
       libXi-devel \
       libxkbcommon-devel \
       scrot \
       python3-xlib

   # Ubuntu
   sudo apt-get install -y \
       python3-dev \
       libxtst-dev \
       libxi-dev \
       libxkbcommon-dev \
       scrot \
       python3-xlib
   ```

2. **Verify Virtual Environment**
   ```bash
   # Activate virtual environment
   source venv/bin/activate

   # Upgrade pip and setuptools
   pip install --upgrade pip setuptools wheel

   # Reinstall PyAutoGUI
   pip install --upgrade pyautogui
   ```

3. **Test PyAutoGUI Installation**
   ```python
   # Python test script
   import pyautogui
   print(pyautogui.position())  # Should print current mouse position
   ```

### Potential Error Messages

- `ModuleNotFoundError: No module named 'pyautogui'`
  - Solution: Ensure virtual environment is activated
  - Reinstall PyAutoGUI with `pip install pyautogui`

- `ImportError` related to X11 or system libraries
  - Solution: Install additional system dependencies
  - Verify X11 libraries are present

### Debugging Information

If issues persist:
1. Check Python version: `python --version`
2. List installed packages: `pip list`
3. Verify system libraries: `ldconfig -p | grep libX`

## Advanced Configuration

For users experiencing persistent issues:
- Consider using alternative automation libraries
- Check system compatibility
- Consult project documentation# Desktop Automation Bot - Windows Setup Guide

## Prerequisites

- Windows 10 or Windows 11
- Administrator access
- Internet connection

## Installation Methods

### Method 1: PowerShell Script (Recommended)

1. **Download the Script**
   - Right-click on [windows_setup.ps1 link]
   - Select "Save link as..."
   - Save to a known location (e.g., Downloads folder)

2. **Run PowerShell as Administrator**
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)"

3. **Execute Setup Script**
   ```powershell
   # Navigate to script location
   cd C:\Users\YourUsername\Downloads

   # Allow script execution
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

   # Run the script
   .\windows_setup.ps1
   ```

### Method 2: Manual Installation

#### Install Dependencies Manually

1. **Install Chocolatey Package Manager**
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
   ```

2. **Install Core Dependencies**
   ```powershell
   # Install Python
   choco install python --version=3.9.7 -y

   # Install Tesseract OCR
   choco install tesseract -y

   # Install Git
   choco install git -y
   ```

3. **Create Project Environment**
   ```powershell
   # Create project directory
   mkdir C:\Projects\desktop-bot
   cd C:\Projects\desktop-bot

   # Clone repository
   git clone https://github.com/yourusername/desktop-bot.git .

   # Create virtual environment
   python -m venv venv
   .\venv\Scripts\Activate

   # Install dependencies
   pip install -r requirements.txt
   ```

```bash
# Navigate to your project directory
cd /path/to/desktop-bot

# Remove existing virtual environment if it exists
rm -rf venv

# Create new virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Explicitly install PyAutoGUI with additional dependencies
pip install pyautogui python3-xlib
```
## Post-Installation

### Activate Virtual Environment
```powershell
# Navigate to project directory
cd C:\Projects\desktop-bot

# Activate virtual environment
.\venv\Scripts\Activate
```

### Run the Application
```powershell
# With virtual environment activated
python app.py
```

## Troubleshooting

### Common Issues

1. **Script Execution Policy**
   - Ensure you run PowerShell as Administrator
   - Use `Set-ExecutionPolicy RemoteSigned`

2. **Python Not Recognized**
   - Restart PowerShell after installation
   - Verify Python installation: `python --version`

3. **Dependency Installation Fails**
   - Check internet connection
   - Ensure you have the latest pip: `python -m pip install --upgrade pip`

## System Requirements

- Minimum Python Version: 3.8
- Recommended: Python 3.9+
- At least 2 GB RAM
- 500 MB free disk space

## Security Notes

- Only download scripts from trusted sources
- Review script contents before execution
- Use a dedicated project user if possible

## Customization

- Modify `windows_setup.ps1` to:
  - Change Python version
  - Adjust installation paths
  - Add/remove specific dependencies

## Contributing

- Report issues on GitHub
- Submit pull requests with improvements

## License

[Specify your project's license]

## Support

- Check project documentation
- Open GitHub issues for specific problems