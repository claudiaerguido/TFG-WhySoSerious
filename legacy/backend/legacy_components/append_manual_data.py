
import pandas as pd
import os

import os

# Robust path finding
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_CSV = os.path.join(BASE_DIR, "../data/teams_es_augmented_500.csv")

# Nuevos ejemplos proporcionados por el usuario
NEW_EXAMPLES = [
    # --- Neutros / Planificación (Anti-Trigger para "Revisar/Pendiente") ---
    ("Estoy revisando los requisitos y mañana lo cerramos.", 0,0,0,0,0,0,1,1,0),
    ("Reviso el guion y lo comparto cuando lo tenga.", 0,0,0,0,0,0,1,1,0),
    ("Tengo la agenda lista para la demo, dura 8–10 minutos.", 0,0,0,0,0,0,1,1,0),
    ("Estoy con el checklist de entrega, luego te confirmo.", 0,0,0,0,0,0,1,1,0),
    ("He subido la nueva versión al repositorio.", 0,0,0,0,0,0,1,1,0),
    ("Mañana repasamos los puntos pendientes en la daily.", 0,0,0,0,0,0,1,1,0),
    ("Queda pendiente validar el diagrama, pero no corre prisa.", 0,0,0,0,0,0,1,1,0),
    ("Voy a revisar los correos antes de salir.", 0,0,0,0,0,0,1,1,0),
    
    # --- Cansancio / Fatiga (Para balancear vs Estrés) ---
    ("Voy en automático, no proceso nada.", 0,0,0,0,1,0,0,2,0),
    ("Me cuesta leer la pantalla, tengo la vista cansada.", 0,0,0,0,1,0,0,2,0),
    ("Mi cerebro ha hecho shutdown, no doy para más.", 0,0,0,0,1,0,0,3,0),
    ("Estoy espeso hoy, voy muy lento.", 0,0,0,0,1,0,0,2,0),
    ("No me entero de nada, necesito dormir.", 0,0,0,0,1,0,0,3,0),
    ("Llevo pilotando en automático toda la tarde.", 0,0,0,0,1,0,0,2,0),
    ("Estoy zombie, no me pidáis pensar mucho.", 0,0,0,0,1,0,0,2,0)
]

def append_manual():
    if not os.path.exists(TARGET_CSV):
        print("Error: CSV no encontrado")
        return

    df = pd.read_csv(TARGET_CSV)
    start_id = df['id'].max() + 1
    
    rows = []
    for text, tris, estr, enf, sobr, cans, posi, neut, inten, inc in NEW_EXAMPLES:
        rows.append({
            "id": start_id,
            "text": text,
            "TRISTEZA": tris, "ESTRES_ANSIEDAD": estr, "ENFADO_IRRITACION": enf,
            "SOBRECARGA_URGENCIA": sobr, "CANSANCIO_FATIGA": cans,
            "POSITIVO_ALIVIO": posi, "NEUTRO": neut,
            "INTENSIDAD": inten, "INCERTO": inc
        })
        start_id += 1
        
    new_df = pd.DataFrame(rows)
    # Ensure correct column order
    new_df = new_df[df.columns]
    
    new_df.to_csv(TARGET_CSV, mode='a', header=False, index=False)
    print(f"Added {len(new_df)} new examples (Neutro & Cansancio) to {TARGET_CSV}")

if __name__ == "__main__":
    append_manual()
