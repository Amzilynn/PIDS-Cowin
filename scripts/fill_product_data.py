import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
from shared.database import SessionLocal
from shared.models import Product

def split_description(text):
    if not text:
        return None, None, None
    
    # Regex pour capturer les sections entre les balises --- TEST ---
    patterns = {
        'indications': r'---\s*INDICATIONS\s*---(.*?)(?=---\s*[A-Z ]+\s*---|$)',
        'compositions': r'---\s*(?:COMPOSITION|COMPOSITIONS)\s*---(.*?)(?=---\s*[A-Z ]+\s*---|$)',
        'usage_advice': r'---\s*(?:CONSEILS D\'UTILISATION|CONSEILS|ADVICE)\s*---(.*?)(?=---\s*[A-Z ]+\s*---|$)'
    }
    
    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        results[key] = match.group(1).strip() if match else None
        
    return results['indications'], results['compositions'], results['usage_advice']

def migrate():
    db = SessionLocal()
    products = db.query(Product).all()
    
    print(f"🔄 Traitement de {len(products)} produits...")
    
    updated_count = 0
    for p in products:
        ind, comp, adv = split_description(p.description)
        
        # On ne met à jour que si on a trouvé quelque chose
        if ind or comp or adv:
            p.indications = ind
            p.compositions = comp
            p.usage_advice = adv
            updated_count += 1
            print(f"✅ Mis à jour : {p.name}")
        else:
            print(f"⚠️  Aucune balise trouvée pour : {p.name}")
            
    db.commit()
    print(f"\n✨ Terminé ! {updated_count} produits ont été mis à jour.")
    db.close()

if __name__ == "__main__":
    migrate()
