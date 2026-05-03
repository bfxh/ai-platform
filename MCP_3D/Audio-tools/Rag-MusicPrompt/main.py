import argparse
import os
import numpy as np

from transformers import pipeline

# ---- Generation model ----
MODEL_NAME = "facebook/musicgen-small"


def save_wav(path, audio_np, sr):
    import soundfile as sf
    sf.write(path, audio_np, sr)


def wav_to_mp3(wav_path, mp3_path, bitrate="192k"):
    from pydub import AudioSegment
    AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3", bitrate=bitrate)


def apply_bitcrusher(audio: np.ndarray, bit_depth: int = 8):
    audio = np.clip(audio, -1.0, 1.0)
    levels = 2 ** bit_depth
    crushed = np.round((audio + 1.0) * (levels - 1) / 2.0) * (2.0 / (levels - 1)) - 1.0
    return crushed.astype(np.float32)


def downsample_naive(audio: np.ndarray, sr: int, target_sr: int = 11025, anti_alias: bool = False):
    if target_sr >= sr:
        return audio, sr

    if anti_alias:
        taps = 101
        n = np.arange(taps) - (taps - 1) / 2
        norm_cut = 0.45 * (target_sr / 2.0) / (sr / 2.0)
        h = np.sinc(norm_cut * n) * np.hamming(taps)
        h /= np.sum(h)
        audio = np.convolve(audio, h, mode="same")

    step = int(round(sr / target_sr))
    ds = audio[::step]
    return ds.astype(np.float32), int(sr / step)


def _extract_audio_and_sr(result):
    """
    Supports return in dict or list[dict]/list[np.ndarray].
    """
    if isinstance(result, dict):
        return result["audio"], result["sampling_rate"]
    if isinstance(result, (list, tuple)):
        if len(result) == 0:
            raise RuntimeError("Pipeline retornou lista vazia.")
        if isinstance(result[0], dict):
            return result[0]["audio"], result[0]["sampling_rate"]
        # fallback: list[np.ndarray]
        return result[0], 32000
    raise TypeError(f"Formato de retorno inesperado do pipeline: {type(result)}")


def _to_mono_1d(audio: np.ndarray) -> np.ndarray:
    """
    Converts any shape to mono 1-D compatible with soundfile/scipy:
    - Accepts (N,), (C,N), (N,C) or with singular dimensions (1,1,N), etc.
    - Mixdown to mono when multichannel.
    """
    a = np.asarray(audio)
    # Remove dimensões de tamanho 1 (ex.: (1,1,N) -> (N,) ou (1,N)->(N,))
    a = np.squeeze(a)

    if a.ndim == 1:
        mono = a
    elif a.ndim == 2:
        # Detecta orientação. Esperamos (samples, channels); se vier (channels, samples) -> transpõe.
        if a.shape[0] <= 8 and a.shape[1] > a.shape[0]:
            # Provável (C, N)
            a = a.T  # agora (N, C)
        # Agora (N, C)
        if a.shape[1] == 1:
            mono = a[:, 0]
        else:
            # Mixdown simples (média dos canais)
            mono = a.mean(axis=1)
    else:
        # Mais de 2 dims: achata tudo e usa como 1-D (conservador)
        mono = a.reshape(-1)

    mono = np.asarray(mono, dtype=np.float32)
    # Clipa por segurança
    mono = np.clip(mono, -1.0, 1.0)
    return mono


def generate_music(prompt: str,
                   seconds: int = 10,
                   seed: int | None = None,
                   guidance_scale: float = 7.5,
                   do_sample: bool = True,
                   device: str | None = None,
                   tokens_per_second: int = 50):
    """
    Generates audio from prompt.
    To MusicGen, uses max_new_tokens = seconds * tokens_per_second (≈50 tokens/s).
    Fallback: try audio_length_in_s if the pipeline supports.
    """
    # Seeding (best-effort)
    if seed is not None:
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except Exception:
            pass
        np.random.seed(seed)

    pipe_args = dict(task="text-to-audio", model=MODEL_NAME)
    if device:
        pipe_args["device"] = device  # ex.: "cuda:0"

    pipe = pipeline(**pipe_args)

    max_new_tokens = int(max(1, round(seconds * tokens_per_second)))

    # 1) Tente com generate_kwargs (MusicGen moderno)
    try:
        try:
            result = pipe(
                prompt,
                generate_kwargs={
                    "max_new_tokens": max_new_tokens,
                    "do_sample": do_sample,
                    "guidance_scale": guidance_scale,
                },
            )
        except TypeError:
            # guidance_scale/do_sample não suportados -> remova
            result = pipe(
                prompt,
                generate_kwargs={
                    "max_new_tokens": max_new_tokens,
                },
            )
    except Exception as e_primary:
        # 2) Fallback: alguns modelos aceitam audio_length_in_s diretamente
        try:
            result = pipe(prompt, audio_length_in_s=seconds)
        except Exception:
            raise e_primary

    audio, sr = _extract_audio_and_sr(result)
    # Normalize shape to mono 1-D for processing/saving
    audio = _to_mono_1d(audio)
    return audio, sr


def main():
    parser = argparse.ArgumentParser(description="Prompt-to-MP3 Music Generator (optional retro mode)")
    parser.add_argument("--prompt", required=True, help="Description of the music to generate")
    parser.add_argument("--seconds", type=int, default=10, help="Duration in seconds")
    parser.add_argument("--seed", type=int, default=None, help="Seed (reproductibility)")
    parser.add_argument("--guidance", type=float, default=7.5, help="Prompt fidelity (can be ignored depends on the version)")
    parser.add_argument("--sample", dest="do_sample", action="store_true", help="Enables sampling (creativity)")
    parser.add_argument("--no-sample", dest="do_sample", action="store_false", help="Disables sampling")
    parser.set_defaults(do_sample=True)

    parser.add_argument("--device", default=None, help='Ex.: "cuda:0" to GPU')
    parser.add_argument("--tps", type=int, default=50, help="Tokens per seccond (aprox.). seconds*tps = max_new_tokens")

    # Saída
    parser.add_argument("--out", default="output", help="Output folder")
    parser.add_argument("--basename", default="music", help="Basename (no extension)")
    parser.add_argument("--bitrate", default="192k", help="Bitrate MP3 (ex.: 128k, 192k, 256k)")

    # Modo retrô/chiptune
    parser.add_argument("--retro", action="store_true", help="Applies bitcrusher + downsampling (8-bit vibe)")
    parser.add_argument("--bitdepth", type=int, default=8, help="Bitcrusher number of bits (ex.: 8, 6, 4)")
    parser.add_argument("--sr_target", type=int, default=11025, help="Target sampling rate (ex.: 11025, 8000, 6000)")
    parser.add_argument("--no-aa", action="store_true", help="No anti-alias (dirty)")

    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    print(f"[INFO] Generating music for {args.seconds}s…")
    audio, sr = generate_music(
        prompt=args.prompt,
        seconds=args.seconds,
        seed=args.seed,
        guidance_scale=args.guidance,
        do_sample=args.do_sample,
        device=args.device,
        tokens_per_second=args.tps
    )

    if args.retro:
        print("[INFO] Applying bitcrusher/downsampling (retro mode)…")
        audio = apply_bitcrusher(audio, bit_depth=args.bitdepth)
        audio, sr = downsample_naive(
            audio, sr,
            target_sr=args.sr_target,
            anti_alias=not args.no_aa
        )

    wav_path = os.path.join(args.out, f"{args.basename}.wav")
    mp3_path = os.path.join(args.out, f"{args.basename}.mp3")

    print("[INFO] Saving WAV…")
    save_wav(wav_path, audio, sr)
    print("[INFO] Converting to MP3…")
    wav_to_mp3(wav_path, mp3_path, bitrate=args.bitrate)

    print(f"[OK] Done!\nWAV: {wav_path}\nMP3: {mp3_path}")


if __name__ == "__main__":
    main()
