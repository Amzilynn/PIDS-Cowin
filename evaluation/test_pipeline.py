"""
Script de validation "Live" du pipeline complet.
Démarre la caméra et le micro, synchronise l'audio avec la vidéo, 
et affiche l'analyse multimodale avec le score en direct.
"""
import cv2
import time
import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluation.pipeline import AvatarEvaluationPipeline

# Configuration Audio
AUDIO_SR = 16000
CHUNK_DURATION = 0.5 # Analyser le son par blocs de 500ms
try:
    import sounddevice as sd
    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False
    print("⚠️ sounddevice introuvable. L'audio est désactivé.")

# Buffer partagé pour le flux micro
audio_buffer = []

def audio_callback(indata, frames, time_info, status):
    """Callback appelé par le hardware audio en arrière-plan."""
    global audio_buffer
    audio_buffer.extend(indata.flatten().tolist())

def run_live_test():
    print("="*60)
    print("DÉMARRAGE DU SIMULATEUR D'ÉVALUATION COMPLET")
    print("="*60)
    
    # 1. Instancier le méga-pipeline
    pipeline = AvatarEvaluationPipeline()
    
    # 2. Ouvrir les périphériques (Cam + Micro)
    cap = cv2.VideoCapture(0)
    audio_stream = None
    if AUDIO_ENABLED:
        audio_stream = sd.InputStream(samplerate=AUDIO_SR, channels=1, dtype='float32', callback=audio_callback)
        audio_stream.start()

    print("\n🎬 Système actif. Appuyez sur 'q' pour quitter.\n")
    
    prev_time = time.time()
    last_audio_analysis_time = time.time()
    current_audio_chunk = None
    
    global audio_buffer

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1) # Mode miroir
        
        # Gestion du sync Audio : On extrait un chunk toutes les 500ms
        now = time.time()
        fps = 1 / (now - prev_time) if now - prev_time > 0 else 0
        prev_time = now
        
        if AUDIO_ENABLED and (now - last_audio_analysis_time) >= CHUNK_DURATION:
            if len(audio_buffer) >= int(AUDIO_SR * CHUNK_DURATION):
                # Extraire le bloc et vider partiellement le buffer
                extract_len = int(AUDIO_SR * CHUNK_DURATION)
                current_audio_chunk = np.array(audio_buffer[:extract_len], dtype='float32')
                audio_buffer = audio_buffer[extract_len:]
            last_audio_analysis_time = now
        elif not AUDIO_ENABLED:
            current_audio_chunk = None
            
        # ====================================================
        # EXÉCUTION DU PIPELINE COMPLET !!!
        # ====================================================
        results = pipeline.process_tick(frame, current_audio_chunk)
        
        # ====================================================
        # Rendu HUD (Affichage visuel style Ironman)
        # ====================================================
        annotated = frame.copy()
        
        # - Dessin (On peut réutiliser le dessinateur du pose_tracker)
        if results["pose"]["has_pose"]:
            annotated = pipeline.pose_tracker.draw_landmarks(annotated, results["mp_pose_results"])
            
        # - Textes
        score = results["score_data"]
        
        # Score Principal
        color = (0, 255, 0) if score["overall_score"] > 70 else (0, 0, 255)
        cv2.putText(annotated, f"SCORE: {score['overall_score']:.0f}/100", (20, 50), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, color, 3)
                    
        # Emotion et Voix
        cv2.putText(annotated, f"Emotion: {results['emotion']['dominant_emotion']}", 
                    (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
                    
        vol = results['audio']['energy']
        cv2.putText(annotated, f"Voix V:{vol:.3f} | Conf: {results['speech']['confidence_score']*100:.0f}%", 
                    (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    
        # Gestes critiques
        if results["gesture"]["arms_crossed"]:
            cv2.putText(annotated, "--- BRAS CROISES !", (20, 160), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
        if score["is_critical"]:
             cv2.putText(annotated, "ALERTE CRITIQUE", (400, 50), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 2)
             for i, pen in enumerate(score["penalties"]):
                 cv2.putText(annotated, f"- {pen}", (400, 80 + i*20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        cv2.putText(annotated, f"FPS: {int(fps)}", (10, frame.shape[0]-20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Evaluation Medicale en temps reel", annotated)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if audio_stream:
        audio_stream.stop()
        audio_stream.close()
    cap.release()
    cv2.destroyAllWindows()
    
    # --- GÉNÉRATION DU DASHBOARD AU CLIC SUR 'q' ---
    historic_data = pipeline.get_session_history()
    print(f"\n[Rapport] Session terminée. J'ai récolté {len(historic_data)} instants d'évaluation.")
    
    if len(historic_data) > 0:
        from evaluation.report.report_generator import generate_html_dashboard
        import webbrowser
        print("📊 Construction du Dashboard Final...")
        # Creation dossier report si inexistant depuis le test_pipeline
        os.makedirs(os.path.join(os.path.dirname(__file__), 'report'), exist_ok=True)
        report_path = generate_html_dashboard(historic_data, os.path.join(os.path.dirname(__file__), 'report', 'dashboard_final.html'))
        print("🚀 Ouverture du dashboard dans votre navigateur...")
        webbrowser.open(f"file://{report_path}")

if __name__ == "__main__":
    run_live_test()
