# desktop-bot

A versatile desktop automation bot with advanced capabilities for UI interaction, task scheduling, remote system management, and AI-powered assistance.

## Features

- **UI Automation**: Control mouse, keyboard, and screen interactions using PyAutoGUI
- **Computer Vision**: Image recognition and OCR capabilities with OpenCV and Tesseract
- **Task Scheduling**: Automated task execution with APScheduler and Schedule
- **Remote System Management**: Connect to remote systems via SSH using Paramiko
- **Email Integration**: Process and respond to emails automatically
- **Natural Language Processing**: Understand and generate text using Spacy and Transformers
- **Speech Recognition**: Convert speech to text for voice-controlled automation
- **Web API**: RESTful interface with Flask for remote control and integration
- **Data Analysis**: Process and visualize data with Pandas, Matplotlib and Seaborn

## Installation

### Prerequisites

- Python 3.9+ 
- For Linux users: Additional system dependencies may be required

### System Dependencies

#### Linux
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-dev gcc tesseract-ocr
```

#### macOS
```bash
brew install portaudio tesseract
```

#### Windows
- Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- Ensure it's added to your PATH

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/automatyzer/desktop.git
   cd desktop
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Note: If you encounter issues with PyAudio installation, try:
   ```bash
   pip install --upgrade --no-build-isolation pyaudio
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Usage

Basic usage instructions:

```python
# Example code for using desktop
from desktop_bot import Bot

bot = Bot()
bot.start()
```

## Cross-Platform Compatibility

desktop is designed to work across multiple platforms:
- **Windows**: Full support with native window management via pygetwindow
- **Linux**: Supported with pywinctl for window management
- **macOS**: Supported with pywinctl for window management

## Advanced Features

### Automated UI Testing
Use desktop to automate UI testing by capturing screenshots, recognizing UI elements, and simulating user interactions.

### Workflow Automation
Create scheduled tasks to automate repetitive workflows, such as data entry, report generation, or system maintenance.

### AI-Assisted Automation
Leverage the integrated NLP capabilities to create intelligent automation that can understand context and adapt to changing conditions.

## Configuration

The bot can be configured using environment variables or a `.env` file. Key configuration options include:

- `LOG_LEVEL`: Set logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `SCHEDULER_ENABLED`: Enable/disable the task scheduler
- `API_ENABLED`: Enable/disable the REST API
- `API_PORT`: Port for the REST API server
- `OCR_ENGINE`: Select OCR engine configuration

## Development

### Project Structure
```
desktop/
├── bot/              # Core bot functionality
├── api/              # REST API implementation
├── nlp/              # Natural language processing modules
├── vision/           # Computer vision and OCR capabilities
├── scheduler/        # Task scheduling implementation
├── utils/            # Utility functions and helpers
├── tests/            # Test suite
└── update/           # Update scripts and tools
```

### Testing

Run tests with pytest:

```bash
pytest
```

For coverage report:

```bash
pytest --cov=. tests/
```

### Updating Dependencies

To update project dependencies:

```bash
python update/requirements.py
```

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### PyAudio Installation Issues
If you encounter issues installing PyAudio:

1. Ensure you have the required system dependencies installed
2. Try installing with: `pip install --upgrade --no-build-isolation pyaudio`
3. On Windows, you may need to install a pre-built binary: `pip install pipwin && pipwin install pyaudio`

### OCR Functionality
If OCR features aren't working:
1. Verify Tesseract OCR is properly installed
2. Check that the Tesseract executable is in your PATH
3. Set the `TESSERACT_CMD` environment variable to the Tesseract executable path

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- All the open-source libraries that make this project possible
- Contributors and community members who have helped improve the project

## Quick Start

### Local Development
1. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
