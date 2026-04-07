"""
Générateur de Dashboard Final (HTML Interactif)
Prend la timeline exacte de la performance (Historique du Scorer) 
et construit un rapport visuel de la simulation de vente/médicale.
"""
import os
import json
import collections

def generate_html_dashboard(history_data, output_path="evaluation_report.html"):
    if not history_data:
        print("Erreur : Aucun historique fourni.")
        return None
        
    # Extraire les données pour le graphique
    timestamps = [h['timestamp'] for h in history_data]
    scores = [h['overall_score'] for h in history_data]
    
    # Calculs pour les KPIs
    avg_score = sum(scores) / len(scores)
    
    # Rassembler toutes les pénalités et les compter
    toutes_les_fautes = []
    for h in history_data:
        # On ne va pas compter 30 fois la même erreur si le bras est croisé 1 seconde
        # Mais pour la simplification du Dashboard on rassemble tout et on reduit
        toutes_les_fautes.extend(h['penalties'])
        
    # Réduire le spam (ex: "bras croisés" détectés 30 frames de suite = 1 seconde)
    frequence_brute = collections.Counter(toutes_les_fautes)
    # On divise par le FPS approximatif (ex: 30) pour avoir un résultat en secondes
    frequence_secondes = {k: max(1, v // 10) for k, v in frequence_brute.items()}
    
    # Choix des couleurs du Dashboard
    theme_color = "#10b981" if avg_score >= 70 else "#f59e0b" if avg_score >= 50 else "#ef4444"
    status_text = "Performant" if avg_score >= 70 else "Moyen" if avg_score >= 50 else "À Améliorer"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rapport d'Évaluation Multimodale</title>
        <!-- Import de Chart.js pour des graphiques dynamiques magnifiques -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{
                --bg: #0f172a;
                --cardBg: #1e293b;
                --textMain: #f8fafc;
                --textMuted: #94a3b8;
                --accent: {theme_color};
            }}
            body {{
                font-family: 'Inter', -apple-system, sans-serif;
                background-color: var(--bg);
                color: var(--textMain);
                margin: 0;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
            }}
            .header h1 {{ margin: 0; font-size: 32px; }}
            .header p {{ color: var(--textMuted); }}
            
            .card {{
                background-color: var(--cardBg);
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            }}
            .kpi-row {{
                display: flex;
                gap: 20px;
                margin-bottom: 24px;
            }}
            .kpi-card {{
                flex: 1;
                background-color: var(--cardBg);
                border-radius: 16px;
                padding: 24px;
                text-align: center;
                border-top: 4px solid var(--accent);
            }}
            .kpi-value {{
                font-size: 48px;
                font-weight: 800;
                color: var(--accent);
                margin: 10px 0;
            }}
            .penalties-list {{
                list-style: none;
                padding: 0;
            }}
            .penalties-list li {{
                background: rgba(239, 68, 68, 0.1);
                border-left: 4px solid #ef4444;
                padding: 12px 16px;
                margin-bottom: 8px;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Rapport de Simulation - Avatar Médecin</h1>
                <p>Laboratoire Vital - Suivi des Délégués Médicaux</p>
            </div>
            
            <div class="kpi-row">
                <div class="kpi-card">
                    <div style="color: var(--textMuted); font-weight: 600;">SCORE GLOBAL</div>
                    <div class="kpi-value">{avg_score:.0f} / 100</div>
                    <div style="color: {theme_color};">{status_text}</div>
                </div>
            </div>
            
            <div class="card">
                <h3 style="margin-top: 0;">📉 Timeline de l'Assurance (Temps Réel)</h3>
                <canvas id="timelineChart" height="100"></canvas>
            </div>
            
            <div class="card">
                <h3 style="margin-top: 0; color: #ef4444;">⚠️ Analyse Critique (Signes de stress ou doute détectés)</h3>
                <ul class="penalties-list">
                    {"".join([f"<li><strong>{k}</strong> : Détecté pendant ~{v} secondes</li>" for k, v in frequence_secondes.items()]) if frequence_secondes else "<li>✅ Parfait ! Aucune attitude négative détectée.</li>"}
                </ul>
            </div>
        </div>

        <script>
            // Le graphique
            const ctx = document.getElementById('timelineChart').getContext('2d');
            const dataScores = {json.dumps(scores)};
            const timestamps = {json.dumps([f"{t:.1f}s" for t in timestamps])};
            
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: timestamps,
                    datasets: [{{
                        label: 'Score de performance (/100)',
                        data: dataScores,
                        borderColor: '{theme_color}',
                        backgroundColor: '{theme_color}22', // Transparence
                        borderWidth: 3,
                        pointRadius: 0, // Enlever les gros points pour lisser
                        fill: true,
                        tension: 0.4 // Courbe douce
                    }}]
                }},
                options: {{
                    responsive: true,
                    interaction: {{ mode: 'index', intersect: false }},
                    scales: {{
                        y: {{ min: 0, max: 100, title: {{ display: true, text: 'Score' }} }},
                        x: {{ title: {{ display: true, text: 'Temps (secondes)' }} }}
                    }},
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Sauvegarde sur le disque
    output_abs_path = os.path.abspath(output_path)
    with open(output_abs_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return output_abs_path
