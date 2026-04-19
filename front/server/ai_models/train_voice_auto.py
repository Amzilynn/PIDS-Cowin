import os
import time
import torch
from multimodal_emotion_detector import VoiceTrainingSystem, VoiceRecorder, EMOTIONS

class CountdownVoiceRecorder(VoiceRecorder):
    def record_for_training(self, emotion_label, num_samples=5):
        print(f"\n=== Recording samples for emotion: {emotion_label.upper()} ===")
        recordings = []
        
        for i in range(num_samples):
            print(f"\nSample {i+1}/{num_samples}")
            print("Get ready...")
            for count in range(3, 0, -1):
                print(f"{count}...")
                time.sleep(1)
                
            print("🔴 RECORDING NOW (3 seconds) - SPEAK!")
            # Calls the original record_voice which handles sd.rec() internally
            audio = self.record_voice()
            recordings.append(audio)
            
            # Save logic is handled below in the original code, but we must replicate it here
            from datetime import datetime
            import soundfile as sf
            filename = f"{emotion_label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.wav"
            filepath = os.path.join(self.recordings_dir, filename)
            sf.write(filepath, audio, self.sample_rate)
            print(f"✅ Saved: {filename}")
            time.sleep(1) # Small pause before next sample
            
        print(f"\nCompleted recording {num_samples} samples for {emotion_label}")
        return recordings

def main():
    print("="*60)
    print("AVALIVE LIVE VOICE TRAINING INITIATED")
    print("="*60)
    print("This will loop through all 7 emotions.")
    print("For each emotion, you will hear a 3-2-1 countdown.")
    print("When it says 'RECORDING NOW', speak clearly into your microphone!")
    print("The system will train the RNN after all samples are collected.")
    print("="*60)
    time.sleep(3)
    
    trainer = VoiceTrainingSystem()
    trainer.recorder = CountdownVoiceRecorder() # Inject our auto-countdown recorder
    trainer.run_training_pipeline()
    
    print("\n[SUCCESS] Voice Emotion Model (.pth) successfully generated and trained!")
    print("You can close this window. The Avalive Main Server will immediately pick up the new model.")
    # Pause so user can read the success message
    time.sleep(10)

if __name__ == "__main__":
    main()
