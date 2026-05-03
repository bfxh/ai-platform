# Rag-MusicPrompt

Rag-MusicPrompt is a Python-based project that demonstrates how to generate music from natural language prompts using Hugging Face's **MusicGen** model.

It includes utilities for audio export, retro effects (bitcrusher + downsampling), and reproducibility with seeds.  

This repository can be used both as a tool for experimentation and as a foundation for integrating AI-generated music into indie games, multimedia projects, or research.

---

## 🚀 Features

- Text-to-audio generation using prompts (style, instruments, mood, etc.).  
- Adjustable guidance / sampling for creative fidelity vs consistency.  
- Retro mode: bit-crushing + downsampling + optional aliasing, to get 8-bit / lo-fi game vibes.  
- Output in **WAV** and **MP3** formats.  
- Command-line interface; configurable via arguments.  
- Useful for indie game music assets: menus, level intros, ambient loops, etc.,
- GPU support (CUDA).

---

## 📂 Repository Structure

```
Rag-MusicPrompt/
├── main.py              # Main script with CLI
├── README.md            # Project documentation
├── requirements.txt     # Python dependencies (optional)
├── /output              # Default output folder (created automatically)
```

---

## 📦 Installation

It is recommended to use a **virtual environment** to isolate dependencies.

### 1. Clone the repository
```bash
git clone https://github.com/RegoDefies/Rag-MusicPrompt.git
cd Rag-MusicPrompt
```

### 2. Create and activate a virtual environment
Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available, install directly:
```bash
pip install torch transformers pydub soundfile numpy
```

---

## 🚀 Usage

Run the tool from the command line with a text prompt:

```bash
python main.py --prompt "lofi hip hop beat with piano and rain sounds" --seconds 15 --out output_folder
```

### Arguments
- `--prompt` (str, required): Music description prompt.
- `--seconds` (int, default=10): Duration in seconds.
- `--seed` (int): Random seed for reproducibility.
- `--guidance` (float, default=7.5): Prompt fidelity.
- `--sample / --no-sample`: Enable or disable sampling.
- `--device` (str): Device (e.g., `"cuda:0"` for GPU).
- `--out` (str, default="output"): Output folder.
- `--basename` (str, default="music"): Base filename.
- `--bitrate` (str, default="192k"): MP3 bitrate.

### Retro Mode Options
- `--retro`: Enable retro mode.
- `--bitdepth` (int, default=8): Bitcrusher depth.
- `--sr_target` (int, default=11025): Target sample rate.
- `--no-aa`: Disable anti-alias filter.

---

## 🎼 Examples

1. **Epic orchestral soundtrack**
```bash
python main.py --prompt "Epic orchestral soundtrack with choir" --seconds 20 --out music_out --basename epic_track
```

2. **8-bit retro game vibe**
```bash
python main.py --prompt "8-bit retro game music, fast tempo" --seconds 12 --retro --bitdepth 6 --sr_target 8000 --out retro_out --basename chip_track
```

3. **Chill lofi loop**
```bash
python main.py --prompt "Chill lofi hip hop with vinyl crackle" --seconds 30 --out lofi_out --basename lofi_track
```

---

## 📜 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

