"""
Module Couche 2 : Action Units (FACS) et Micro-expressions
Utilise l'outil professionnel OpenFace 2.0 pour extraire précisément les 44 Action Units.
"""
import os
import subprocess
import pandas as pd

class ActionUnitAnalyzer:
    def __init__(self, openface_path=None):
        """
        Initialise l'analyseur FACS.
        :param openface_path: Chemin absolu vers l'exécutable FeatureExtraction.exe
        """
        self.openface_path = openface_path
        self.is_installed = self.check_installation()

    def check_installation(self):
        """
        Vérifie si le binaire d'OpenFace existe à l'emplacement indiqué.
        Sinon, guide amicalement l'utilisateur pour l'installation comme demandé.
        """
        if self.openface_path and os.path.exists(self.openface_path):
            return True
            
        print("\n" + "="*55)
        print(" ⚠️  OpenFace 2.0 INTROUVABLE ou NON CONFIGURE ")
        print("="*55)
        print("Pour l'analyse pointue des Action Units (FACS) comme les ")
        print("froncements (AU4) ou la joie (AU12), ce module nécessite OpenFace.")
        print("\n📝 COMMENT INSTALLER SOUS WINDOWS :")
        print("  1. Téléchargez OpenFace_2.2.0_win_x64.zip depuis :")
        print("     https://github.com/TadasBaltrusaitis/OpenFace/releases")
        print("  2. Extrayez le dossier dans C:\\OpenFace par exemple.")
        print("  3. Ouvrez 'evaluation/config.py' et modifiez le chemin :")
        print("     'openface_executable_path' = r'C:\\OpenFace\\FeatureExtraction.exe'")
        print("-" * 55)
        print("En attendant, le système fonctionnera en mode asynchrone sans les AUs.\n")
        return False

    def process_frame(self, frame):
        """
        Fonction espace-réservé pour traitement en temps réel.
        Lancer le .exe sur chaque frame prend ~1s, ce n'est pas viable pour la webcam.
        En production "Real-Time", nous utiliserons la vision par défaut MediaPipe 
        ou piperons le flux à OpenFace via C++ socket. 
        Pour ce pipeline python, on se concentrera sur l'analyse asynchrone d'une vidéo (process_video_batch).
        """
        return {
            "has_au": False,
            "au_intensities": {}, 
            "au_presence": {}
        }

    def process_video_batch(self, video_path, output_dir):
        """
        Analyse complète d'un fichier vidéo (idéal après un enregistrement).
        Retourne un DataFrame pandas avec la timeline parfaite de 44 AUs.
        """
        if not self.is_installed:
            return None
            
        print(f"Lancement d'OpenFace sur {os.path.basename(video_path)}... (Cela peut prendre du temps)")
        try:
            # Exécution silencieuse d'OpenFace
            command = [
                self.openface_path,
                "-f", video_path,
                "-out_dir", output_dir
            ]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            csv_path = os.path.join(output_dir, f"{base_name}.csv")
            
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                # On normalise les temps et filtre les colonnes inutiles (garder que AU_*_r et AU_*_c)
                cols_to_keep = ['timestamp', 'confidence', 'success'] + [c for c in df.columns if 'AU' in c]
                df = df[cols_to_keep]
                # OpenFace ajoute des espaces devant le nom des colonnes, on nettoie
                df.columns = df.columns.str.strip()
                return df
                
        except Exception as e:
            print(f"Erreur d'exécution d'OpenFace : {e}")
            
        return None

def run_test():
    print("Démarrage du test d'initialisation ActionUnitAnalyzer...")
    print("Ce test va vérifier le chemin dans config.py.")
    
    import sys
    # Ajout du dossier root au path pour importer config
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        import config
        path = config.EMOTION_CONFIG.get('openface_executable_path')
        print(f"--> Chemin lu dans config.py : {path}")
    except Exception as e:
        print(f"Erreur de lecture de config: {e}")
        path = "chemin_introuvable.exe"
        
    au_analyzer = ActionUnitAnalyzer(openface_path=path)
    
if __name__ == "__main__":
    run_test()
