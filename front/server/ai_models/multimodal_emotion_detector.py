"""
Complete Emotion Detection System with YOLO + GNN (Facial) + RNN (Voice)
Author: Comprehensive Multi-Modal Implementation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data, Batch, Dataset
from torch.utils.data import DataLoader, random_split
import cv2
import numpy as np
from ultralytics import YOLO
import pandas as pd
import os
import warnings
from collections import defaultdict
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import zipfile
import requests
import io
import sounddevice as sd
import soundfile as sf
import librosa
import librosa.display
import tempfile
import time
import threading
import queue
import wave
import speech_recognition as sr
from scipy import signal
import json
import pickle
from datetime import datetime

warnings.filterwarnings('ignore')

# ==================== Configuration ====================
EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
EMOTION_MAP = {0: 'angry', 1: 'disgust', 2: 'fear', 3: 'happy', 4: 'neutral', 5: 'sad', 6: 'surprise'}
IMG_SIZE = 48  # FER2013 uses 48x48 images
SAMPLE_RATE = 22050
DURATION = 3  # seconds for voice recording
N_MFCC = 40
MAX_PAD_LEN = 100  # max sequence length for RNN

# ==================== VOICE RECORDING & PROCESSING ====================
class VoiceRecorder:
    """Record and manage voice samples"""
    
    def __init__(self, sample_rate=SAMPLE_RATE, duration=DURATION):
        self.sample_rate = sample_rate
        self.duration = duration
        self.recordings_dir = "voice_recordings"
        os.makedirs(self.recordings_dir, exist_ok=True)
        
    def record_voice(self, duration=None, filename=None):
        """Record voice from microphone"""
        if duration is None:
            duration = self.duration
        
        print(f"\nRecording for {duration} seconds...")
        print("Speak now!")
        
        # Record audio
        audio_data = sd.rec(int(duration * self.sample_rate), 
                           samplerate=self.sample_rate, 
                           channels=1, 
                           dtype=np.float32)
        sd.wait()  # Wait for recording to complete
        
        # Flatten the array
        audio_data = audio_data.flatten()
        
        # Save if filename provided
        if filename:
            filepath = os.path.join(self.recordings_dir, filename)
            sf.write(filepath, audio_data, self.sample_rate)
            print(f"Recording saved to {filepath}")
        
        return audio_data
    
    def record_for_training(self, emotion_label, num_samples=5):
        """Record multiple samples for training"""
        print(f"\n=== Recording samples for emotion: {emotion_label} ===")
        recordings = []
        
        for i in range(num_samples):
            print(f"\nSample {i+1}/{num_samples}")
            input("Press Enter when ready to record...")
            audio = self.record_voice()
            recordings.append(audio)
            
            # Save with emotion label
            filename = f"{emotion_label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.wav"
            filepath = os.path.join(self.recordings_dir, filename)
            sf.write(filepath, audio, self.sample_rate)
            print(f"Saved: {filename}")
        
        print(f"\nCompleted recording {num_samples} samples for {emotion_label}")
        return recordings
    
    def load_recorded_data(self):
        """Load all recorded voice samples"""
        data = []
        labels = []
        
        for filename in os.listdir(self.recordings_dir):
            if filename.endswith('.wav'):
                # Extract emotion from filename (format: emotion_timestamp_index.wav)
                emotion = filename.split('_')[0]
                if emotion in EMOTIONS:
                    filepath = os.path.join(self.recordings_dir, filename)
                    audio, sr = librosa.load(filepath, sr=self.sample_rate)
                    data.append(audio)
                    labels.append(emotion)
        
        return data, labels
    
    def clear_recordings(self):
        """Delete all voice recordings"""
        confirm = input("Are you sure you want to delete all voice recordings? (y/n): ")
        if confirm.lower() == 'y':
            for file in os.listdir(self.recordings_dir):
                if file.endswith('.wav'):
                    os.remove(os.path.join(self.recordings_dir, file))
            print("All voice recordings deleted!")
        else:
            print("Operation cancelled")

# ==================== VOICE FEATURE EXTRACTION ====================
class VoiceFeatureExtractor:
    """Extract features from voice for RNN"""
    
    def __init__(self, sample_rate=SAMPLE_RATE, n_mfcc=N_MFCC, max_pad_len=MAX_PAD_LEN):
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.max_pad_len = max_pad_len
    
    def extract_mfcc(self, audio):
        """Extract MFCC features from audio"""
        mfcc = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=self.n_mfcc)
        
        # Pad or truncate to fixed length
        if mfcc.shape[1] < self.max_pad_len:
            pad_width = self.max_pad_len - mfcc.shape[1]
            mfcc = np.pad(mfcc, pad_width=((0, 0), (0, pad_width)), mode='constant')
        else:
            mfcc = mfcc[:, :self.max_pad_len]
        
        return mfcc.T  # Return as (time_steps, features)
    
    def extract_spectrogram(self, audio):
        """Extract spectrogram features"""
        spectrogram = librosa.feature.melspectrogram(y=audio, sr=self.sample_rate, n_mels=128)
        log_spectrogram = librosa.power_to_db(spectrogram, ref=np.max)
        
        # Pad or truncate
        if log_spectrogram.shape[1] < self.max_pad_len:
            pad_width = self.max_pad_len - log_spectrogram.shape[1]
            log_spectrogram = np.pad(log_spectrogram, pad_width=((0, 0), (0, pad_width)), mode='constant')
        else:
            log_spectrogram = log_spectrogram[:, :self.max_pad_len]
        
        return log_spectrogram.T
    
    def extract_pitch(self, audio):
        """Extract pitch (F0) features"""
        pitches, magnitudes = librosa.piptrack(y=audio, sr=self.sample_rate)
        
        # Get pitch values
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch_values.append(pitches[index, t])
        
        pitch_array = np.array(pitch_values)
        
        # Pad or truncate
        if len(pitch_array) < self.max_pad_len:
            pad_width = self.max_pad_len - len(pitch_array)
            pitch_array = np.pad(pitch_array, pad_width=(0, pad_width), mode='constant')
        else:
            pitch_array = pitch_array[:self.max_pad_len]
        
        return pitch_array.reshape(-1, 1)
    
    def extract_energy(self, audio):
        """Extract energy (RMS) features"""
        energy = librosa.feature.rms(y=audio)
        energy = energy.flatten()
        
        # Pad or truncate
        if len(energy) < self.max_pad_len:
            pad_width = self.max_pad_len - len(energy)
            energy = np.pad(energy, pad_width=(0, pad_width), mode='constant')
        else:
            energy = energy[:self.max_pad_len]
        
        return energy.reshape(-1, 1)
    
    def extract_all_features(self, audio):
        """Extract all features and combine"""
        mfcc = self.extract_mfcc(audio)
        spectrogram = self.extract_spectrogram(audio)
        pitch = self.extract_pitch(audio)
        energy = self.extract_energy(audio)
        
        # Combine features along feature dimension
        # MFCC: (time, 40), Spectrogram: (time, 128), Pitch: (time, 1), Energy: (time, 1)
        combined = np.concatenate([mfcc, spectrogram, pitch, energy], axis=1)
        
        return torch.tensor(combined, dtype=torch.float)

# ==================== RNN MODEL FOR VOICE ====================
class VoiceEmotionRNN(nn.Module):
    """RNN-based model for voice emotion recognition"""
    
    def __init__(self, input_dim=40+128+1+1, hidden_dim=256, num_layers=3, 
                 num_classes=7, dropout=0.3, bidirectional=True):
        super(VoiceEmotionRNN, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_dim, 
            hidden_dim, 
            num_layers, 
            batch_first=True,
            dropout=dropout,
            bidirectional=bidirectional
        )
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * self.num_directions, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )
        
        # Batch normalization
        self.bn = nn.BatchNorm1d(hidden_dim * self.num_directions)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * self.num_directions, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        
    def forward(self, x):
        # x shape: (batch, seq_len, features)
        
        # LSTM forward
        lstm_out, (hidden, cell) = self.lstm(x)
        # lstm_out shape: (batch, seq_len, hidden_dim * num_directions)
        
        # Attention mechanism
        attention_weights = torch.softmax(self.attention(lstm_out), dim=1)
        attended_output = torch.sum(attention_weights * lstm_out, dim=1)
        
        # Apply batch normalization
        attended_output = self.bn(attended_output)
        
        # Classification
        output = self.classifier(attended_output)
        
        return output

# ==================== GNN MODEL FOR FACIAL EMOTION (from previous) ====================
class GNNEmotionModel(nn.Module):
    """Enhanced GNN for facial emotion recognition"""
    
    def __init__(self, input_dim=35, hidden_dim=256, num_classes=7, dropout=0.3):
        super(GNNEmotionModel, self).__init__()
        
        # Graph convolution layers
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, hidden_dim)
        self.conv4 = GCNConv(hidden_dim, hidden_dim)
        
        # Batch normalization
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
        self.bn3 = nn.BatchNorm1d(hidden_dim)
        self.bn4 = nn.BatchNorm1d(hidden_dim)
        
        self.dropout = nn.Dropout(dropout)
        
        # Multi-head attention
        self.attention_heads = 4
        self.attention = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.Tanh(),
                nn.Linear(hidden_dim // 2, 1)
            ) for _ in range(self.attention_heads)
        ])
        
        # Residual connections
        self.residual1 = nn.Linear(input_dim, hidden_dim)
        self.residual2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 4, num_classes)
        )
        
    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        # Initial residual
        residual = self.residual1(x)
        
        # First convolution
        x = F.elu(self.bn1(self.conv1(x, edge_index)))
        x = self.dropout(x)
        
        # Second convolution with residual
        identity = x
        x = F.elu(self.bn2(self.conv2(x, edge_index)))
        x = x + identity
        
        # Third convolution
        x = F.elu(self.bn3(self.conv3(x, edge_index)))
        x = self.dropout(x)
        
        # Fourth convolution
        x = F.elu(self.bn4(self.conv4(x, edge_index)))
        
        # Multi-head attention pooling
        attention_weights = []
        for attention_head in self.attention:
            weights = torch.softmax(attention_head(x), dim=0)
            attention_weights.append(weights)
        
        # Average attention weights
        attention_weights = torch.stack(attention_weights).mean(dim=0)
        x = x * attention_weights
        
        # Global pooling
        x = global_mean_pool(x, batch)
        
        # Classification
        x = self.classifier(x)
        
        return x

# ==================== MULTI-MODAL FUSION ====================
class MultiModalEmotionFusion(nn.Module):
    """Fuse facial and voice emotion predictions"""
    
    def __init__(self, num_classes=7, fusion_type='weighted'):
        super(MultiModalEmotionFusion, self).__init__()
        self.num_classes = num_classes
        self.fusion_type = fusion_type
        
        if fusion_type == 'learned':
            self.fusion_weights = nn.Sequential(
                nn.Linear(num_classes * 2, num_classes * 2),
                nn.ReLU(),
                nn.Linear(num_classes * 2, num_classes)
            )
    
    def forward(self, facial_logits, voice_logits):
        if self.fusion_type == 'weighted':
            # Simple weighted average (weights can be learned or fixed)
            weights = torch.tensor([0.6, 0.4], device=facial_logits.device)
            fused = weights[0] * facial_logits + weights[1] * voice_logits
            return fused
        
        elif self.fusion_type == 'concatenation':
            # Concatenate and classify
            combined = torch.cat([facial_logits, voice_logits], dim=-1)
            return self.fusion_weights(combined)
        
        elif self.fusion_type == 'max':
            # Take maximum probability
            fused = torch.max(facial_logits, voice_logits)
            return fused
        
        else:  # average
            return (facial_logits + voice_logits) / 2

# ==================== FACIAL GRAPH CONSTRUCTOR ====================
class FacialGraphConstructor:
    """Constructs graph from facial landmarks"""
    
    def __init__(self):
        self.landmark_indices = {
            'jaw': list(range(0, 17)),
            'eyebrows': list(range(17, 27)),
            'nose': list(range(27, 36)),
            'eyes': list(range(36, 48)),
            'mouth': list(range(48, 68))
        }
        
        self.edges = self._create_edges()
        self.use_mediapipe = False
        
        try:
            import mediapipe as mp
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
            self.use_mediapipe = True
            print("MediaPipe initialized successfully")
        except:
            print("MediaPipe not available, using synthetic landmarks")
    
    def _create_edges(self):
        """Create edges connecting neighboring landmarks"""
        edges = []
        
        for region, indices in self.landmark_indices.items():
            for i in range(len(indices) - 1):
                edges.append([indices[i], indices[i+1]])
                edges.append([indices[i+1], indices[i]])
        
        # Cross-region connections
        for i in range(36, 48):
            for j in range(17, 27):
                if abs(i - j) < 10:
                    edges.append([i, j])
                    edges.append([j, i])
        
        for i in range(48, 68):
            for j in range(27, 36):
                if abs(i - j) < 15:
                    edges.append([i, j])
                    edges.append([j, i])
        
        return torch.tensor(edges, dtype=torch.long).t().contiguous()
    
    def extract_landmarks(self, face_img):
        """Extract facial landmarks"""
        if self.use_mediapipe:
            rgb_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_img)
            
            if results.multi_face_landmarks:
                landmarks = []
                for lm in results.multi_face_landmarks[0].landmark:
                    landmarks.append([lm.x, lm.y, lm.z])
                return np.array(landmarks)
        
        return self._generate_synthetic_landmarks(face_img)
    
    def _generate_synthetic_landmarks(self, face_img):
        """Generate synthetic landmarks for fallback"""
        h, w = face_img.shape[:2]
        landmarks = []
        
        for i in range(68):
            angle = 2 * np.pi * i / 68
            x = w/2 + (w/3) * np.cos(angle) * (0.5 + 0.3 * np.sin(angle))
            y = h/2 + (h/3) * np.sin(angle) * (0.8 + 0.2 * np.cos(angle))
            z = np.sin(angle) * 0.1
            landmarks.append([x/w, y/h, z])
        
        return np.array(landmarks)
    
    def construct_graph(self, landmarks):
        """Construct PyTorch Geometric graph"""
        node_features = torch.tensor(landmarks, dtype=torch.float)
        texture_features = torch.randn(node_features.size(0), 32) * 0.1
        node_features = torch.cat([node_features, texture_features], dim=1)
        
        return Data(x=node_features, edge_index=self.edges)

# ==================== COMPLETE EMOTION DETECTOR ====================
class MultiModalEmotionDetector:
    """Complete emotion detection with facial and voice analysis"""
    
    def __init__(self, yolo_model='yolov8n-face.pt', 
                 facial_model_path=None, 
                 voice_model_path=None,
                 device='cuda'):
        
        self.device = device if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {self.device}")
        
        # Initialize facial components
        self.yolo = YOLO(yolo_model)
        self.graph_constructor = FacialGraphConstructor()
        self.facial_model = GNNEmotionModel(input_dim=35, hidden_dim=256, num_classes=7).to(self.device)
        
        if facial_model_path and os.path.exists(facial_model_path):
            self.facial_model.load_state_dict(torch.load(facial_model_path, map_location=self.device))
            print(f"Facial model loaded from {facial_model_path}")
        
        # Initialize voice components
        self.voice_extractor = VoiceFeatureExtractor()
        self.voice_model = VoiceEmotionRNN(input_dim=40+128+1+1, hidden_dim=256, 
                                           num_classes=7).to(self.device)
        
        if voice_model_path and os.path.exists(voice_model_path):
            self.voice_model.load_state_dict(torch.load(voice_model_path, map_location=self.device))
            print(f"Voice model loaded from {voice_model_path}")
        
        # Fusion model
        self.fusion = MultiModalEmotionFusion(num_classes=7, fusion_type='weighted')
        
        # Set to evaluation mode
        self.facial_model.eval()
        self.voice_model.eval()
        
        # Emotion colors
        self.emotion_colors = {
            'angry': (0, 0, 255),
            'disgust': (0, 255, 255),
            'fear': (255, 0, 255),
            'happy': (0, 255, 0),
            'neutral': (255, 255, 255),
            'sad': (255, 0, 0),
            'surprise': (255, 255, 0)
        }
        
        self.recorder = VoiceRecorder()
    
    def detect_faces(self, image):
        """Detect faces using YOLO"""
        results = self.yolo(image)
        faces = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = box.conf[0]
                    
                    if confidence > 0.5:
                        face_img = image[y1:y2, x1:x2]
                        if face_img.size > 0:
                            faces.append({
                                'bbox': (x1, y1, x2, y2),
                                'confidence': confidence.item(),
                                'image': face_img
                            })
        
        return faces
    
    def predict_facial_emotion(self, face_img):
        """Predict emotion from face"""
        landmarks = self.graph_constructor.extract_landmarks(face_img)
        
        if landmarks is None or len(landmarks) == 0:
            return None, None
        
        graph = self.graph_constructor.construct_graph(landmarks)
        graph.batch = torch.zeros(1, dtype=torch.long)
        
        with torch.no_grad():
            graph = graph.to(self.device)
            output = self.facial_model(graph.unsqueeze(0))
            probabilities = F.softmax(output, dim=1)
            emotion_idx = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][emotion_idx].item()
        
        emotion = EMOTIONS[emotion_idx]
        return emotion, confidence
    
    def predict_voice_emotion(self, audio_data):
        """Predict emotion from voice"""
        # Extract features
        features = self.voice_extractor.extract_all_features(audio_data)
        
        # Add batch dimension
        features = features.unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            output = self.voice_model(features)
            probabilities = F.softmax(output, dim=1)
            emotion_idx = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][emotion_idx].item()
        
        emotion = EMOTIONS[emotion_idx]
        return emotion, confidence
    
    def predict_multi_modal(self, face_img=None, audio_data=None):
        """Fuse facial and voice predictions"""
        facial_emotion = None
        voice_emotion = None
        facial_conf = 0
        voice_conf = 0
        
        if face_img is not None:
            facial_emotion, facial_conf = self.predict_facial_emotion(face_img)
        
        if audio_data is not None:
            voice_emotion, voice_conf = self.predict_voice_emotion(audio_data)
        
        # Simple fusion based on confidence
        if facial_emotion and voice_emotion:
            if facial_conf > voice_conf:
                return facial_emotion, facial_conf, "facial"
            else:
                return voice_emotion, voice_conf, "voice"
        elif facial_emotion:
            return facial_emotion, facial_conf, "facial"
        elif voice_emotion:
            return voice_emotion, voice_conf, "voice"
        else:
            return None, 0, None
    
    def process_image_with_voice(self, image_path):
        """Process image and optionally record voice"""
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not read image {image_path}")
            return None
        
        faces = self.detect_faces(image)
        
        if not faces:
            print("No faces detected!")
            return None
        
        # Use the first detected face
        face_info = faces[0]
        x1, y1, x2, y2 = face_info['bbox']
        face_img = face_info['image']
        
        print("\n=== Facial Emotion Analysis ===")
        facial_emotion, facial_conf = self.predict_facial_emotion(face_img)
        print(f"Detected: {facial_emotion} (confidence: {facial_conf:.2f})")
        
        # Ask for voice input
        print("\n=== Voice Emotion Analysis ===")
        record_voice = input("Would you like to record voice for emotion analysis? (y/n): ")
        
        voice_emotion = None
        voice_conf = 0
        
        if record_voice.lower() == 'y':
            audio = self.recorder.record_voice()
            voice_emotion, voice_conf = self.predict_voice_emotion(audio)
            print(f"Detected: {voice_emotion} (confidence: {voice_conf:.2f})")
        
        # Multi-modal fusion
        print("\n=== Multi-Modal Fusion ===")
        if voice_emotion:
            final_emotion, final_conf, source = self.predict_multi_modal(face_img, audio)
            print(f"Final prediction: {final_emotion} (confidence: {final_conf:.2f})")
            print(f"Source: {source}")
        else:
            final_emotion = facial_emotion
            final_conf = facial_conf
            print(f"Final prediction: {final_emotion} (confidence: {final_conf:.2f})")
            print("Source: facial only")
        
        # Draw results on image
        color = self.emotion_colors.get(final_emotion, (255, 255, 255))
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        
        label = f"{final_emotion}: {final_conf:.2f}"
        if voice_emotion:
            label += f" | Voice: {voice_emotion}"
        
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(image, (x1, y1 - 25), (x1 + label_size[0], y1), color, -1)
        cv2.putText(image, label, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        cv2.imshow('Multi-Modal Emotion Detection', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return image

# ==================== VOICE TRAINING SYSTEM ====================
class VoiceTrainingSystem:
    """Train voice emotion model with recorded samples"""
    
    def __init__(self):
        self.extractor = VoiceFeatureExtractor()
        self.recorder = VoiceRecorder()
        self.model = VoiceEmotionRNN(input_dim=40+128+1+1, hidden_dim=256, num_classes=7)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)
        
    def collect_training_data(self):
        """Collect voice samples for each emotion"""
        print("\n=== Voice Training Data Collection ===")
        print("We'll record samples for each emotion")
        print("You'll need to record 5 samples per emotion")
        
        all_features = []
        all_labels = []
        
        for emotion_idx, emotion in enumerate(EMOTIONS):
            print(f"\n{'='*50}")
            print(f"Recording for emotion: {emotion.upper()}")
            print(f"Emotion index: {emotion_idx}")
            print("Try to express this emotion clearly in your voice")
            print("Speak naturally, say something like:")
            
            # Example phrases
            examples = {
                'angry': "I'm very angry right now! This is frustrating!",
                'disgust': "This is disgusting! I can't stand it!",
                'fear': "I'm so scared! This is terrifying!",
                'happy': "I'm so happy! This is wonderful!",
                'neutral': "I'm feeling neutral. Just normal.",
                'sad': "I'm so sad... This is disappointing.",
                'surprise': "Wow! This is amazing! I'm surprised!"
            }
            
            print(f"Example: '{examples.get(emotion, 'This is a sample phrase')}'")
            
            recordings = self.recorder.record_for_training(emotion, num_samples=5)
            
            # Extract features
            for audio in recordings:
                features = self.extractor.extract_all_features(audio)
                all_features.append(features)
                all_labels.append(emotion_idx)
            
            print(f"Completed {len(recordings)} samples for {emotion}")
        
        return all_features, all_labels
    
    def prepare_data_loaders(self, features, labels, batch_size=16, test_split=0.2):
        """Prepare data loaders for training"""
        # Convert to tensors
        features_tensor = torch.stack(features)
        labels_tensor = torch.tensor(labels, dtype=torch.long)
        
        # Split data
        dataset_size = len(features_tensor)
        test_size = int(dataset_size * test_split)
        train_size = dataset_size - test_size
        
        train_dataset, test_dataset = random_split(
            list(zip(features_tensor, labels_tensor)), 
            [train_size, test_size]
        )
        
        def collate_fn(batch):
            features = torch.stack([item[0] for item in batch])
            labels = torch.tensor([item[1] for item in batch])
            return features, labels
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, 
                                 shuffle=True, collate_fn=collate_fn)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, 
                                shuffle=False, collate_fn=collate_fn)
        
        return train_loader, test_loader
    
    def train_model(self, train_loader, val_loader, epochs=50):
        """Train the voice emotion model"""
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)
        
        history = {'train_loss': [], 'val_loss': [], 'val_acc': []}
        best_val_acc = 0
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0
            for features, labels in train_loader:
                features, labels = features.to(self.device), labels.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(features)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            # Validation
            self.model.eval()
            val_loss = 0
            correct = 0
            total = 0
            
            with torch.no_grad():
                for features, labels in val_loader:
                    features, labels = features.to(self.device), labels.to(self.device)
                    outputs = self.model(features)
                    loss = criterion(outputs, labels)
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs, 1)
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()
            
            val_acc = 100 * correct / total
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            
            history['train_loss'].append(avg_train_loss)
            history['val_loss'].append(avg_val_loss)
            history['val_acc'].append(val_acc)
            
            print(f"Epoch {epoch+1}/{epochs}")
            print(f"Train Loss: {avg_train_loss:.4f}")
            print(f"Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.2f}%")
            
            scheduler.step(avg_val_loss)
            
            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save(self.model.state_dict(), 'voice_emotion_model.pth')
                print(f"Saved best model with accuracy: {val_acc:.2f}%")
            
            print("-" * 50)
        
        return history
    
    def run_training_pipeline(self):
        """Complete training pipeline"""
        print("\n" + "="*60)
        print("VOICE EMOTION MODEL TRAINING")
        print("="*60)
        
        # Collect data
        features, labels = self.collect_training_data()
        
        if len(features) == 0:
            print("No training data collected!")
            return None
        
        print(f"\nCollected {len(features)} samples")
        
        # Prepare data loaders
        train_loader, val_loader = self.prepare_data_loaders(features, labels)
        
        # Train model
        history = self.train_model(train_loader, val_loader)
        
        # Plot results
        self.plot_training_results(history)
        
        print("\nTraining completed!")
        print("Model saved as 'voice_emotion_model.pth'")
        
        return self.model
    
    def plot_training_results(self, history):
        """Plot training results"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        ax1.plot(history['train_loss'], label='Train Loss')
        ax1.plot(history['val_loss'], label='Val Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.set_title('Training and Validation Loss')
        ax1.legend()
        ax1.grid(True)
        
        ax2.plot(history['val_acc'], label='Validation Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy (%)')
        ax2.set_title('Validation Accuracy')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()

# ==================== FER2013 DATASET (from previous) ====================
class FER2013Dataset(Dataset):
    """PyTorch Geometric Dataset for FER2013"""
    
    def __init__(self, data_path=None, transform=None, use_synthetic_landmarks=True):
        super().__init__()
        self.transform = transform
        self.use_synthetic_landmarks = use_synthetic_landmarks
        self.data_list = []
        
        if data_path and os.path.exists(data_path):
            self.load_from_file(data_path)
        else:
            print("Generating synthetic data for demonstration...")
            self.generate_synthetic_data()
    
    def generate_synthetic_landmarks(self, image):
        """Generate synthetic facial landmarks"""
        h, w = image.shape[:2] if len(image.shape) > 2 else (IMG_SIZE, IMG_SIZE)
        landmarks = []
        
        for i in range(68):
            angle = 2 * np.pi * i / 68
            x = w/2 + (w/3) * np.cos(angle) * (0.5 + 0.3 * np.sin(angle))
            y = h/2 + (h/3) * np.sin(angle) * (0.8 + 0.2 * np.cos(angle))
            z = np.sin(angle) * 0.1
            landmarks.append([x/w, y/h, z])
        
        return np.array(landmarks)
    
    def create_graph_from_landmarks(self, landmarks):
        """Create graph structure from landmarks"""
        node_features = torch.tensor(landmarks, dtype=torch.float)
        texture_features = torch.randn(node_features.size(0), 32) * 0.1
        node_features = torch.cat([node_features, texture_features], dim=1)
        
        edges = self.create_facial_edges()
        return Data(x=node_features, edge_index=edges)
    
    def create_facial_edges(self):
        """Create edge connections"""
        edges = []
        
        jaw_indices = list(range(0, 17))
        for i in range(len(jaw_indices) - 1):
            edges.append([jaw_indices[i], jaw_indices[i+1]])
            edges.append([jaw_indices[i+1], jaw_indices[i]])
        
        left_eyebrow = list(range(17, 22))
        right_eyebrow = list(range(22, 27))
        
        for region in [left_eyebrow, right_eyebrow]:
            for i in range(len(region) - 1):
                edges.append([region[i], region[i+1]])
                edges.append([region[i+1], region[i]])
        
        nose = list(range(27, 36))
        for i in range(len(nose) - 1):
            edges.append([nose[i], nose[i+1]])
            edges.append([nose[i+1], nose[i]])
        
        left_eye = list(range(36, 42))
        right_eye = list(range(42, 48))
        
        for eye in [left_eye, right_eye]:
            for i in range(len(eye) - 1):
                edges.append([eye[i], eye[i+1]])
                edges.append([eye[i+1], eye[i]])
        
        mouth_outer = list(range(48, 60))
        mouth_inner = list(range(60, 68))
        
        for mouth in [mouth_outer, mouth_inner]:
            for i in range(len(mouth) - 1):
                edges.append([mouth[i], mouth[i+1]])
                edges.append([mouth[i+1], mouth[i]])
        
        return torch.tensor(edges, dtype=torch.long).t().contiguous()
    
    def generate_synthetic_data(self):
        """Generate synthetic data for testing"""
        print("Generating synthetic training data...")
        num_samples = 1000
        
        for i in tqdm(range(num_samples), desc="Generating samples"):
            emotion = np.random.randint(0, 7)
            landmarks = self.generate_synthetic_landmarks(None)
            graph = self.create_graph_from_landmarks(landmarks)
            graph.y = torch.tensor([emotion], dtype=torch.long)
            self.data_list.append(graph)
        
        print(f"Generated {len(self.data_list)} synthetic samples")
    
    def len(self):
        return len(self.data_list)
    
    def get(self, idx):
        return self.data_list[idx]

# ==================== FACIAL TRAINING SYSTEM ====================
class FacialTrainingSystem:
    """Train facial emotion model"""
    
    def __init__(self):
        self.model = GNNEmotionModel(input_dim=35, hidden_dim=256, num_classes=7)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)
    
    def train_model(self, train_loader, val_loader, epochs=30):
        """Train facial emotion model"""
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)
        
        best_val_acc = 0
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0
            correct = 0
            total = 0
            
            for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
                batch = batch.to(self.device)
                optimizer.zero_grad()
                
                output = self.model(batch)
                loss = criterion(output, batch.y)
                
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(output, 1)
                total += batch.y.size(0)
                correct += (predicted == batch.y).sum().item()
            
            train_acc = 100 * correct / total
            avg_train_loss = train_loss / len(train_loader)
            
            # Validation
            self.model.eval()
            val_loss = 0
            correct = 0
            total = 0
            
            with torch.no_grad():
                for batch in val_loader:
                    batch = batch.to(self.device)
                    output = self.model(batch)
                    loss = criterion(output, batch.y)
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(output, 1)
                    total += batch.y.size(0)
                    correct += (predicted == batch.y).sum().item()
            
            val_acc = 100 * correct / total
            avg_val_loss = val_loss / len(val_loader)
            
            print(f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.2f}%")
            print(f"Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.2f}%")
            
            scheduler.step(avg_val_loss)
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save(self.model.state_dict(), 'facial_emotion_model.pth')
                print(f"Saved best model with accuracy: {val_acc:.2f}%")
            
            print("-" * 50)
    
    def run_training(self):
        """Run facial training pipeline"""
        print("\n" + "="*60)
        print("FACIAL EMOTION MODEL TRAINING")
        print("="*60)
        
        dataset = FER2013Dataset()
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
        
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
        
        print(f"Train samples: {len(train_dataset)}")
        print(f"Validation samples: {len(val_dataset)}")
        
        self.train_model(train_loader, val_loader)

# ==================== MAIN APPLICATION ====================
def main():
    print("\n" + "="*60)
    print("MULTI-MODAL EMOTION DETECTION SYSTEM")
    print("Facial (YOLO + GNN) + Voice (RNN)")
    print("="*60)
    
    while True:
        print("\n" + "="*50)
        print("MAIN MENU")
        print("="*50)
        print("1. Train Facial Model (GNN on FER2013)")
        print("2. Train Voice Model (RNN on Recorded Samples)")
        print("3. Multi-Modal Detection (Face + Voice)")
        print("4. Facial Detection Only")
        print("5. Voice Detection Only")
        print("6. Manage Voice Recordings")
        print("7. Exit")
        print("="*50)
        
        choice = input("Enter your choice (1-7): ")
        
        if choice == '1':
            print("\nTraining Facial Emotion Model...")
            trainer = FacialTrainingSystem()
            trainer.run_training()
            
        elif choice == '2':
            print("\nTraining Voice Emotion Model...")
            print("You will record samples for each emotion")
            print("Make sure your microphone is working!")
            trainer = VoiceTrainingSystem()
            trainer.run_training_pipeline()
            
        elif choice == '3':
            print("\nMulti-Modal Emotion Detection")
            print("This will use both face and voice for emotion recognition")
            
            detector = MultiModalEmotionDetector(
                facial_model_path='facial_emotion_model.pth' if os.path.exists('facial_emotion_model.pth') else None,
                voice_model_path='voice_emotion_model.pth' if os.path.exists('voice_emotion_model.pth') else None
            )
            
            print("\nOptions:")
            print("1. Process image with voice recording")
            print("2. Real-time video with voice recording")
            subchoice = input("Select option (1-2): ")
            
            if subchoice == '1':
                image_path = input("Enter image path: ")
                if os.path.exists(image_path):
                    detector.process_image_with_voice(image_path)
                else:
                    print("Image not found!")
            
            elif subchoice == '2':
                print("\nReal-time detection mode")
                print("Press 'q' to quit, 'r' to record voice")
                # Real-time implementation would go here
                print("Feature coming soon!")
            
        elif choice == '4':
            print("\nFacial Detection Only")
            detector = MultiModalEmotionDetector(
                facial_model_path='facial_emotion_model.pth' if os.path.exists('facial_emotion_model.pth') else None
            )
            
            print("\nOptions:")
            print("1. Process image")
            print("2. Real-time video")
            subchoice = input("Select option (1-2): ")
            
            if subchoice == '1':
                image_path = input("Enter image path: ")
                if os.path.exists(image_path):
                    detector.process_image_with_voice(image_path)  # This will work but skip voice
                else:
                    print("Image not found!")
            
            elif subchoice == '2':
                print("Real-time facial detection mode")
                # Simplified real-time implementation
                cap = cv2.VideoCapture(0)
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    faces = detector.detect_faces(frame)
                    for face in faces:
                        x1, y1, x2, y2 = face['bbox']
                        face_img = face['image']
                        emotion, conf = detector.predict_facial_emotion(face_img)
                        
                        if emotion:
                            color = detector.emotion_colors.get(emotion, (255, 255, 255))
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            label = f"{emotion}: {conf:.2f}"
                            cv2.putText(frame, label, (x1, y1-5), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    cv2.imshow('Facial Emotion Detection', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                cap.release()
                cv2.destroyAllWindows()
        
        elif choice == '5':
            print("\nVoice Detection Only")
            detector = MultiModalEmotionDetector(
                voice_model_path='voice_emotion_model.pth' if os.path.exists('voice_emotion_model.pth') else None
            )
            
            if not os.path.exists('voice_emotion_model.pth'):
                print("No voice model found! Please train the model first (Option 2)")
                continue
            
            print("\nRecording for 3 seconds...")
            recorder = VoiceRecorder()
            audio = recorder.record_voice()
            
            emotion, confidence = detector.predict_voice_emotion(audio)
            print(f"\nDetected emotion: {emotion.upper()}")
            print(f"Confidence: {confidence:.2f}")
            
            # Visualize the audio
            plt.figure(figsize=(12, 4))
            plt.subplot(1, 2, 1)
            plt.plot(audio)
            plt.title('Audio Waveform')
            plt.xlabel('Time')
            plt.ylabel('Amplitude')
            
            plt.subplot(1, 2, 2)
            mfcc = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=20)
            librosa.display.specshow(mfcc, x_axis='time')
            plt.title('MFCC Features')
            plt.colorbar()
            
            plt.tight_layout()
            plt.show()
        
        elif choice == '6':
            print("\nManage Voice Recordings")
            print("1. View recorded samples")
            print("2. Delete all recordings")
            
            subchoice = input("Select option (1-2): ")
            
            if subchoice == '1':
                recorder = VoiceRecorder()
                data, labels = recorder.load_recorded_data()
                print(f"\nTotal recordings: {len(data)}")
                
                # Count by emotion
                from collections import Counter
                label_counts = Counter(labels)
                for emotion, count in label_counts.items():
                    print(f"  {emotion}: {count} samples")
            
            elif subchoice == '2':
                recorder = VoiceRecorder()
                recorder.clear_recordings()
        
        elif choice == '7':
            print("\nExiting...")
            break
        
        else:
            print("Invalid choice! Please try again.")

# ==================== CHECK REQUIREMENTS ====================
def check_requirements():
    """Check and print system requirements"""
    print("\nChecking requirements...")
    
    try:
        import torch
        print(f"✓ PyTorch: {torch.__version__}")
        print(f"  CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA Version: {torch.version.cuda}")
            print(f"  GPU: {torch.cuda.get_device_name()}")
    except:
        print("✗ PyTorch not installed properly")
    
    try:
        import torch_geometric
        print(f"✓ PyTorch Geometric: {torch_geometric.__version__}")
    except:
        print("✗ PyTorch Geometric not installed")
    
    try:
        import cv2
        print(f"✓ OpenCV: {cv2.__version__}")
    except:
        print("✗ OpenCV not installed")
    
    try:
        from ultralytics import YOLO
        print("✓ Ultralytics YOLO: Installed")
    except:
        print("✗ Ultralytics YOLO not installed")
    
    try:
        import librosa
        print(f"✓ Librosa: {librosa.__version__}")
    except:
        print("✗ Librosa not installed")
    
    try:
        import sounddevice as sd
        print(f"✓ Sounddevice: {sd.__version__}")
    except:
        print("✗ Sounddevice not installed")
    
    try:
        import mediapipe as mp
        print("✓ MediaPipe: Installed")
    except:
        print("✗ MediaPipe not installed (optional)")
    
    print("\nTo install missing dependencies, run:")
    print("pip install torch torchvision torch-geometric ultralytics opencv-python")
    print("pip install mediapipe pandas matplotlib seaborn scikit-learn tqdm")
    print("pip install librosa sounddevice soundfile pyaudio speechrecognition")

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("MULTI-MODAL EMOTION DETECTION SYSTEM")
    print("Facial (YOLO + GNN) + Voice (RNN)")
    print("="*60)
    
    check_requirements()
    
    # Create necessary directories
    os.makedirs("voice_recordings", exist_ok=True)
    
    # Download YOLO face model if not exists
    if not os.path.exists('yolov8n-face.pt'):
        print("\nDownloading YOLO face detection model...")
        try:
            from ultralytics import YOLO
            model = YOLO('yolov8n-face.pt')
            print("✓ YOLO model downloaded successfully")
        except:
            print("✗ Could not download YOLO model automatically")
            print("  Please run: pip install ultralytics")
    
    # Run main application
    main()
