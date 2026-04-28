"""
Générateur de rapport de session Co-Win (Version PDF).
Utilise fpdf2 pour créer un rapport professionnel téléchargeable.
"""

import os
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

class CoWinReport(FPDF):
    pass

def generate_report(delegue, messages, cv_summary):
    """
    Genere un rapport de session épuré et stable (Zéro débordement).
    """
    try:
        nom_delegue = delegue.get('nom', 'Inconnu')
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        report_dir = Path(base_path) / "reports"
        report_dir.mkdir(exist_ok=True)
        
        report_filename = f"Rapport_{nom_delegue.replace(' ', '_')}_{timestamp}.pdf"
        report_path = report_dir / report_filename
        
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_margins(25, 25, 25)
        pdf.add_page()
        
        # 1. TITRE
        pdf.set_font('helvetica', 'B', 20)
        pdf.set_text_color(44, 62, 80)
        pdf.set_x(25)
        pdf.multi_cell(150, 10, "BILAN DE PERFORMANCE IA")
        pdf.ln(2)
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(120, 120, 120)
        pdf.set_x(25)
        pdf.multi_cell(150, 6, f"DELEGUE : {nom_delegue.upper()} | DATE : {date_str}")
        pdf.ln(8)
        
        # 2. SCORES
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(52, 152, 219)
        pdf.set_x(25)
        pdf.multi_cell(150, 10, "  MESURES DES COMPETENCES", fill=True)
        pdf.ln(4)
        
        pdf.set_text_color(33, 37, 41)
        averages = cv_summary.get('averages', {}) if cv_summary else {}
        scores = [
            ("Performance Globale", f"{averages.get('performance', 0):.0%}"),
            ("Confiance", f"{averages.get('confidence', 0):.0%}"),
            ("Engagement", f"{averages.get('engagement', 0):.0%}"),
            ("Gestion Stress", f"{1 - averages.get('stress', 0):.0%}"),
        ]
        
        for label, val in scores:
            pdf.set_x(30)
            pdf.set_font('helvetica', 'B', 11)
            pdf.multi_cell(145, 8, f"- {label} : {val}")
            
        pdf.ln(8)
        
        # 3. ANALYSE PRODUIT (NLP)
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(46, 204, 113)
        pdf.set_x(25)
        pdf.multi_cell(150, 10, "  ANALYSE SCIENTIFIQUE DU DISCOURS", fill=True)
        pdf.ln(4)
        
        nlp = cv_summary.get('nlp', {}) if cv_summary else {}
        
        # COMMENTAIRE
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(33, 37, 41)
        pdf.set_x(25)
        pdf.multi_cell(150, 7, "BILAN DE L'IA :")
        pdf.set_font('helvetica', 'I', 10)
        pdf.set_x(25)
        pdf.multi_cell(150, 6, nlp.get('feedback_summary', 'Non disponible.'))
        pdf.ln(6)
        
        # POINTS FORTS
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(39, 174, 96)
        pdf.set_x(25)
        pdf.multi_cell(150, 7, "POINTS FORTS :")
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(33, 37, 41)
        corrects = nlp.get('correct_points', [])
        if corrects:
            for p in corrects:
                pdf.set_x(30)
                pdf.multi_cell(145, 6, f"- {p}")
        else:
            pdf.set_x(30)
            pdf.multi_cell(145, 6, "- Aucun point specifique valide.")
        pdf.ln(4)
        
        # ERREURS
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(231, 76, 60)
        pdf.set_x(25)
        pdf.multi_cell(150, 7, "ERREURS / OMISSIONS :")
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(33, 37, 41)
        mistakes = nlp.get('mistakes', [])
        if mistakes:
            for m in mistakes:
                pdf.set_x(30)
                pdf.multi_cell(145, 6, f"- {m}")
        else:
            pdf.set_x(30)
            pdf.multi_cell(145, 6, "- Aucune erreur detectee.")
            
        pdf.output(str(report_path))
        print(f"[Report] SUCCES : Rapport genere dans {report_path}")
        return str(report_path)
        
    except Exception as e:
        import traceback
        print(f"[Report] CRASH : {e}")
        traceback.print_exc()
        return None
        
    except Exception as e:
        import traceback
        print(f"[Report] CRASH : {e}")
        traceback.print_exc()
        return None
