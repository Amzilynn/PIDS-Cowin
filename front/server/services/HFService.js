// import fetch from 'node-fetch'; // Native fetch used in Node 18+
import dotenv from 'dotenv';
dotenv.config();

const HF_TOKEN = process.env.HF_TOKEN;

export const HFService = {
  // Chatbot: Using BioMistral or Mistral-7B
  async chat(message, context = [], role = "delegate") {
    if (!HF_TOKEN) {
      // Fallback to Local Python AI at port 8000
      try {
        const localRes = await fetch("http://localhost:8000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, context, role })
        });
        const localData = await localRes.json();
        return localData.response || "Local AI processing...";
      } catch (e) {
        return "Ava AI: Local Engine unreachable. Please start 'main.py' on port 8000.";
      }
    }
    
    const prompt = `[INST] You are Dr. Khalil, an expert Medical AI Evaluator for Avalife. Respond to this medical delegate. User Context: ${context.join(', ')}. Message: ${message} [/INST]`;
    
    try {
      const response = await fetch("https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2", {
        headers: { Authorization: `Bearer ${HF_TOKEN}` },
        method: "POST",
        body: JSON.stringify({ inputs: prompt, parameters: { max_new_tokens: 150, temperature: 0.7 } }),
      });
      const result = await response.json();
      return result[0]?.generated_text?.split('[/INST]')[1]?.trim() || "I am processing your input...";
    } catch (err) {
      console.error("HF Chat Error:", err);
      return "Evaluation error. Check connectivity.";
    }
  },

  // STT: Whisper
  async stt(audioBuffer) {
    if (!HF_TOKEN) {
      try {
        const localRes = await fetch("http://localhost:8000/stt", {
          method: "POST",
          body: audioBuffer
        });
        const data = await localRes.json();
        return data.text || "";
      } catch (e) {
        return "";
      }
    }
    
    try {
      const response = await fetch("https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo", {
        headers: { Authorization: `Bearer ${HF_TOKEN}` },
        method: "POST",
        body: audioBuffer,
      });
      const result = await response.json();
      return result.text || "";
    } catch (err) {
      return "";
    }
  },

  // Emotion Analysis
  async analyzeEmotion(imageBuffer) {
    if (!HF_TOKEN) {
      try {
        const localRes = await fetch("http://localhost:8000/vision", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: imageBuffer.toString('base64') })
        });
        return await localRes.json();
      } catch (e) {
        return { label: 'Neutral', score: 1.0 };
      }
    }

    try {
      const response = await fetch("https://api-inference.huggingface.co/models/dima806/facial_emotions_image_detection", {
        headers: { Authorization: `Bearer ${HF_TOKEN}` },
        method: "POST",
        body: imageBuffer,
      });
      const result = await response.json();
      return result[0] || { label: 'Neutral', score: 1.0 };
    } catch (err) {
      return { label: 'Neutral', score: 1.0 };
    }
  },

  // Multimodal Fusion: Vision + Voice
  async analyzeMultimodal(imageB64, audioB64) {
    if (!HF_TOKEN) {
      try {
        const res = await fetch("http://localhost:8000/analyze_multimodal", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: imageB64, audio_b64: audioB64 })
        });
        return await res.json();
      } catch (e) {
        return { fused: "Neutral" };
      }
    }
    return { fused: "Neutral" };
  }
};
