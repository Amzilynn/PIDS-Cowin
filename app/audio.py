from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import wave
import audioop
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from faster_whisper import WhisperModel
from gtts import gTTS

from .config import Settings
from .qa import answer_question


_WHISPER_CACHE = {}

# Language code mappings for whisper and gtts
_LANGUAGE_CODES = {
    "fr": "fr",
    "en": "en",
    "es": "es"
}

# Error messages in different languages
_ERROR_MESSAGES = {
    "fr": "Je n'ai pas réussi à transcrire la question audio.",
    "en": "I failed to transcribe the audio question.",
    "es": "No pude transcribir la pregunta de audio."
}

_NO_AUDIO_MESSAGES = {
    "fr": "Aucun enregistrement audio détecté. Veuillez parler puis réessayer.",
    "en": "No audio recording detected. Please speak and try again.",
    "es": "No se detectó ninguna grabación de audio. Por favor hable e inténtelo de nuevo."
}


def _get_whisper_model(size: str) -> WhisperModel:
    model = _WHISPER_CACHE.get(size)
    if model is None:
        model = WhisperModel(size, device="cpu", compute_type="int8")
        _WHISPER_CACHE[size] = model
    return model


def _median(values: List[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return int((ordered[mid - 1] + ordered[mid]) / 2)


def _trim_audio_end_on_silence(audio_path: Optional[str], settings: Settings) -> Optional[str]:
    if not audio_path:
        return audio_path

    source_path = Path(audio_path)
    if not source_path.exists():
        return audio_path

    if source_path.suffix.lower() != ".wav":
        return audio_path

    try:
        with wave.open(str(source_path), "rb") as wav_file:
            nchannels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            nframes = wav_file.getnframes()
            raw_audio = wav_file.readframes(nframes)

        if not raw_audio or framerate <= 0 or sampwidth <= 0:
            return audio_path

        if nchannels > 1:
            raw_audio = audioop.tomono(raw_audio, sampwidth, 0.5, 0.5)

        if sampwidth != 2:
            raw_audio = audioop.lin2lin(raw_audio, sampwidth, 2)
            sampwidth = 2

        window_ms = max(10, settings.analysis_window_ms)
        silence_min_ms = max(200, settings.silence_min_ms)
        min_voice_ms = max(100, settings.min_voice_ms)
        silence_threshold_rms = max(1, settings.silence_threshold_rms)

        bytes_per_second = framerate * sampwidth
        window_bytes = max(2, int((bytes_per_second * window_ms) / 1000))
        if window_bytes % 2 != 0:
            window_bytes += 1

        min_voice_windows = max(1, int(min_voice_ms / window_ms))
        silence_windows_needed = max(1, int(silence_min_ms / window_ms))
        speech_pad_windows = max(1, int(200 / window_ms))

        windows = [
            raw_audio[index : index + window_bytes]
            for index in range(0, len(raw_audio), window_bytes)
            if len(raw_audio[index : index + window_bytes]) >= 2
        ]

        if not windows:
            return audio_path

        rms_values = [audioop.rms(frame, 2) for frame in windows]

        probe_count = max(3, int(600 / window_ms))
        noise_floor = _median(rms_values[:probe_count])
        adaptive_threshold = max(120, int(noise_floor * 2.2))
        effective_threshold = min(silence_threshold_rms, adaptive_threshold) if adaptive_threshold > 0 else silence_threshold_rms
        effective_threshold = max(80, effective_threshold)

        voice_mask = [value >= effective_threshold for value in rms_values]

        filtered_mask = [False] * len(voice_mask)
        run_start = None
        for index, is_voice in enumerate(voice_mask):
            if is_voice and run_start is None:
                run_start = index
            if (not is_voice or index == len(voice_mask) - 1) and run_start is not None:
                end_index = index if not is_voice else index + 1
                if end_index - run_start >= min_voice_windows:
                    for write_index in range(run_start, end_index):
                        filtered_mask[write_index] = True
                run_start = None

        speech_indices = [index for index, is_voice in enumerate(filtered_mask) if is_voice]
        if not speech_indices:
            return audio_path

        first_speech = speech_indices[0]
        last_speech = speech_indices[-1]

        trim_start = max(0, first_speech - speech_pad_windows)
        trim_end = min(len(windows), last_speech + speech_pad_windows + 1)

        trailing_silence = len(windows) - trim_end
        if trailing_silence < silence_windows_needed:
            return audio_path

        trimmed_raw = b"".join(windows[trim_start:trim_end])
        if not trimmed_raw:
            return audio_path

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as out_file:
            trimmed_path = out_file.name

        with wave.open(trimmed_path, "wb") as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)
            wav_out.setframerate(framerate)
            wav_out.writeframes(trimmed_raw)

        return trimmed_path
    except Exception:
        return audio_path


def transcribe_audio(audio_path: Optional[str], settings: Settings) -> Tuple[str, Optional[str]]:
    if not audio_path:
        return "", None

    if not Path(audio_path).exists():
        return "", None

    model = _get_whisper_model(settings.whisper_model_size)
    forced_language = _LANGUAGE_CODES.get(settings.language)
    transcription_language = None if settings.whisper_auto_detect else forced_language
    segments, info = model.transcribe(
        audio_path,
        language=transcription_language,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": max(200, settings.silence_min_ms),
            "speech_pad_ms": 200,
        },
    )
    segments_list = list(segments)
    text = " ".join(segment.text.strip() for segment in segments_list).strip()

    detected_language: Optional[str] = None
    if settings.whisper_auto_detect:
        info_language = getattr(info, "language", None)
        info_confidence = float(getattr(info, "language_probability", 0.0) or 0.0)
        if info_language in {"fr", "en", "es"} and info_confidence >= settings.whisper_lang_min_conf:
            detected_language = info_language
    elif forced_language:
        detected_language = forced_language

    if detected_language is not None and detected_language not in {"fr", "en", "es"}:
        detected_language = None

    return text, detected_language


def synthesize_speech(text: str, lang: str = "fr", timeout_sec: int = 20, max_chars: int = 1200) -> Optional[str]:
    content = (text or "").strip()
    if not content:
        return None

    if len(content) > max_chars:
        content = content[:max_chars]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as file:
        output_path = file.name
    lang_code = _LANGUAGE_CODES.get(lang, "fr")

    def _save_tts() -> None:
        gTTS(text=content, lang=lang_code).save(output_path)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_save_tts)
            future.result(timeout=max(3, timeout_sec))

        if not os.path.exists(output_path):
            return None

        if os.path.getsize(output_path) <= 0:
            try:
                os.remove(output_path)
            except OSError:
                pass
            return None

        return output_path
    except TimeoutError:
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except OSError:
            pass
        return None
    except Exception:
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except OSError:
            pass
        return None


def process_audio_question(
    audio_path: Optional[str],
    settings: Settings,
    conversation_history: List[Dict[str, str]] | None = None,
) -> Tuple[str, str, Optional[str]]:
    if not audio_path:
        message = _NO_AUDIO_MESSAGES.get(settings.language, _NO_AUDIO_MESSAGES["fr"])
        return "", message, None

    processed_audio_path = _trim_audio_end_on_silence(audio_path, settings)
    transcript, detected_language = transcribe_audio(processed_audio_path, settings)
    if not transcript:
        message = _ERROR_MESSAGES.get(settings.language, _ERROR_MESSAGES["fr"])
        audio_answer = synthesize_speech(
            message,
            settings.language,
            timeout_sec=settings.tts_timeout_sec,
            max_chars=settings.tts_max_chars,
        )
        return "", message, audio_answer

    qa_result = answer_question(
        transcript,
        settings,
        preferred_language=detected_language,
        conversation_history=conversation_history,
    )
    answer = qa_result["answer"]
    answer_language = str(qa_result.get("answer_language", settings.language))
    answer_audio_path = synthesize_speech(
        answer,
        answer_language,
        timeout_sec=settings.tts_timeout_sec,
        max_chars=settings.tts_max_chars,
    )
    return transcript, answer, answer_audio_path