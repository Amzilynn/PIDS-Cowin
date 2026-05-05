
import pyaudio
p = pyaudio.PyAudio()
print("Audio Devices:")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"[{i}] {info.get('name')} - Max Input Channels: {info.get('maxInputChannels')}")
p.terminate()
