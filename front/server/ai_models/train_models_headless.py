import os
import torch
import numpy as np

# Override VoiceRecorder to not require manual input to train the RNN model
from multimodal_emotion_detector import FacialTrainingSystem, VoiceTrainingSystem, VoiceRecorder, EMOTIONS

class MockVoiceRecorder(VoiceRecorder):
    def record_for_training(self, emotion_label, num_samples=5):
        print(f"Synthesizing 5 voice samples automatically for {emotion_label}...")
        # Generate random audio data (white noise) instead of blocking for microphone
        return [np.random.randn(int(self.duration * self.sample_rate)).astype(np.float32) for _ in range(num_samples)]

print("Starting Headless Model Training for Ava Live AI Base...")

# Train Facial GNN (.pth generator)
print("\n--- Training Facial GNN Model ---")
facial_trainer = FacialTrainingSystem()
# Only train for 1 epoch to quickly generate the .pth file for integration
dataset = facial_trainer.train_model.__globals__['FER2013Dataset']()
from torch.utils.data import DataLoader, random_split
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
facial_trainer.train_model(train_loader, val_loader, epochs=1)

# Train Voice RNN (.pth generator)
print("\n--- Training Voice RNN Model ---")
voice_trainer = VoiceTrainingSystem()
voice_trainer.recorder = MockVoiceRecorder() # Use mock recorder
features, labels = voice_trainer.collect_training_data()
train_loader, val_loader = voice_trainer.prepare_data_loaders(features, labels)
voice_trainer.train_model(train_loader, val_loader, epochs=1)

print("\nModels trained and saved successfully (facial_emotion_model.pth, voice_emotion_model.pth)!")
