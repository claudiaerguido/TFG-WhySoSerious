import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
from sklearn.metrics import classification_report
import nlp_model

# --- Configuración de la evaluación ---

# Dataset "Gold Standard": Conjunto de datos etiquetado y verificado manualmente por humanos.
# Se utiliza como referencia absoluta (Ground Truth) para medir el rendimiento del modelo.
GOLD_CSV = "../../data/teams_goldset_120.csv"
RESULTS_DIR = "results"
ERRORS_CSV = os.path.join(RESULTS_DIR, "gold_errors.csv")
SUMMARY_MD = os.path.join(RESULTS_DIR, "gold_summary.md")

# Palabras clave para detectar errores en casos concretos que nos interesan
PATTERNS = {
    "Neutros Peligrosos": ["pendiente", "revisar", "agendar", "cuando puedas", "sin prisa", "echar un ojo"],
    "Sobrecarga Real": ["urgente", "hoy", "ya", "no llego", "bloquea", "plazo", "asap", "fuego"],
    "Estrés": ["taquicardia", "ansiedad", "nudo", "hiperventil", "rumiar", "panico", "miedo"],
    "Cansancio": ["agotado", "zombie", "sin energía", "sueño", "no proceso", "batería", "fundido"]
}

TARGET_LABELS = ["TRISTEZA", "ESTRES_ANSIEDAD", "ENFADO_IRRITACION", "SOBRECARGA_URGENCIA", "CANSANCIO_FATIGA", "POSITIVO_ALIVIO", "NEUTRO"]

def get_keywords_in_text(text, keywords):
    """Detecta la presencia de palabras clave en el texto."""
    found = [k for k in keywords if k in text.lower()]
    return found

def main():
    print(f"--- Iniciando Evaluación con Gold Set: {GOLD_CSV} ---")
    
    # 2. CARGA DEL DATASET
    if not os.path.exists(GOLD_CSV):
        print(f"Error Crítico: No se encuentra el archivo {GOLD_CSV}.")
        return

    df = pd.read_csv(GOLD_CSV)
    print(f"Muestras a evaluar: {len(df)}")
    
    # 3. INFERENCIA Y COMPARACIÓN
    y_true = []
    y_pred = []
    error_analysis = []
    
    # Inicialización de contadores para estadísticas por patrón
    pattern_stats = {cat: {"FP": 0, "FN": 0} for cat in PATTERNS.keys()}

    for idx, row in df.iterrows():
        text = row["text"]
        
        # A. Recuperar Etiquetas Reales (Ground Truth)
        true_labels = []
        true_vector = []
        for l in TARGET_LABELS:
            val = int(row.get(l, 0))
            if val == 1:
                true_labels.append(l)
            true_vector.append(val)
        y_true.append(true_vector)
        
        # B. Realizar Predicción con el Modelo en Producción
        # Usamos `nlp_model.final_predict` para simular exactamente el comportamiento del sistema real,
        # incluyendo lógica de umbrales dinámicos y heurísticas, no solo la salida cruda del modelo.
        pred_out = nlp_model.final_predict(text)
        pred_labels_dict = pred_out["labels"] 
        thresholds = pred_out["thresholds"]
        is_fallback = pred_out.get("is_fallback", False)
        
        detected_labels = []
        pred_vector = []
        
        for l in TARGET_LABELS:
            score = pred_labels_dict.get(l, 0.0)
            th = thresholds.get(l, 0.5)
            
            is_hit = score >= th
            if is_hit:
                 detected_labels.append(l)
            
            pred_vector.append(1 if is_hit else 0)
        
        y_pred.append(pred_vector)
        
        # C. Análisis de Errores (Falsos Positivos / Falsos Negativos)
        row_errors = []
        for i, label in enumerate(TARGET_LABELS):
            t = true_vector[i]
            p = pred_vector[i]
            
            error_type = None
            if t == 1 and p == 0:
                error_type = "FN" # Falso Negativo (Omisión)
            elif t == 0 and p == 1:
                error_type = "FP" # Falso Positivo (Alarma Falsa)
                
            if error_type:
                # Correlación con patrones lingüísticos conocidos
                for cat, keywords in PATTERNS.items():
                    hits = get_keywords_in_text(text, keywords)
                    if hits:
                        # Contamos solo los casos que realmente nos importan para los KPIs
                        if cat == "Neutros Peligrosos" and label == "SOBRECARGA_URGENCIA" and error_type == "FP":
                             pattern_stats[cat]["FP"] += 1
                        
                        if label == "SOBRECARGA_URGENCIA" and cat == "Sobrecarga Real" and error_type == "FN":
                            pattern_stats[cat]["FN"] += 1
                        
                        if label == "ESTRES_ANSIEDAD" and cat == "Estrés" and error_type == "FN":
                             pattern_stats[cat]["FN"] += 1

                row_errors.append(f"{label}:{error_type}")

        # Registro detallado para auditoría
        res_entry = {
            "id": row.get("id", idx),
            "text": text,
            "true_labels": str(true_labels),
            "pred_labels": str(detected_labels),
        }
        # Añadir probabilidades crudas para depuración
        for l in TARGET_LABELS:
            res_entry[f"prob_{l}"] = f"{pred_labels_dict.get(l,0.0):.3f}"
            
        res_entry["errors"] = "; ".join(row_errors) if row_errors else "OK"
        res_entry["is_fallback"] = is_fallback
        error_analysis.append(res_entry)

    # 4. CÁLCULO DE MÉTRICAS GLOBALES
    y_true_np = np.array(y_true)
    y_pred_np = np.array(y_pred)
    
    report_dict = classification_report(y_true_np, y_pred_np, target_names=TARGET_LABELS, output_dict=True, zero_division=0)
    
    # 5. GENERACIÓN DE REPORTES
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        
    # A. Archivo CSV de Errores (para inspección granular)
    df_errors = pd.DataFrame(error_analysis)
    df_errors.to_csv(ERRORS_CSV, index=False)
    print(f"CSV de Errores guardado: {ERRORS_CSV}")
    
    # B. Informe en Markdown con métricas y análisis de errores
    with open(SUMMARY_MD, "w") as f:
        f.write("# Informe de Evaluación del Modelo (Gold Set)\n\n")
        f.write(f"**Dataset:** `{GOLD_CSV}`\n")
        f.write(f"**Muestras Totales:** {len(df)}\n\n")
        
        # Tabla de Métricas por Clase
        f.write("## 1. Desempeño por Clase\n")
        f.write("| Etiqueta | Precisión | Recall | F1-Score | Soporte |\n")
        f.write("|---|---|---|---|---|\n")
        for label in TARGET_LABELS:
            m = report_dict[label]
            f.write(f"| {label} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1-score']:.3f} | {m['support']} |\n")
        
        # Métricas Agregadas
        micro = report_dict["micro avg"]
        macro = report_dict["macro avg"]
        f.write(f"| **MICRO AVG** | {micro['precision']:.3f} | {micro['recall']:.3f} | {micro['f1-score']:.3f} | {micro['support']} |\n")
        f.write(f"| **MACRO AVG** | {macro['precision']:.3f} | {macro['recall']:.3f} | {macro['f1-score']:.3f} | {macro['support']} |\n\n")
        
        # Análisis de Errores Críticos (Top Errors)
        f.write("## 2. Análisis de Errores Críticos\n")
        
        def get_top_errors(label, err_type, n=10):
            filtered = df_errors[df_errors["errors"].str.contains(f"{label}:{err_type}", na=False)]
            return filtered.head(n)
            
        f.write("### Falsos Positivos: Sobrecarga (Alarmas Injustificadas)\n")
        fp_sobr = get_top_errors("SOBRECARGA_URGENCIA", "FP")
        if fp_sobr.empty:
            f.write("_Ninguno detectado._\n")
        else:
            for _, r in fp_sobr.iterrows():
                f.write(f"- `{r['text']}` (Prob: {r['prob_SOBRECARGA_URGENCIA']}) -> Real: {r['true_labels']}\n")
        
        f.write("\n### Falsos Negativos: Sobrecarga (Riesgos No Detectados)\n")
        fn_sobr = get_top_errors("SOBRECARGA_URGENCIA", "FN")
        if fn_sobr.empty:
            f.write("_Ninguno detectado._\n")
        else:
            for _, r in fn_sobr.iterrows():
                f.write(f"- `{r['text']}` (Prob: {r['prob_SOBRECARGA_URGENCIA']}) -> Pred: {r['pred_labels']}\n")
                
        # Estadísticas de Patrones
        f.write("\n## 3. Análisis de Patrones Lingüísticos\n")
        f.write("| Grupo de Patrones | Conteo de Errores Específicos |\n")
        f.write("|---|---|\n")
        f.write(f"| **Neutros Adversarios** (pendiente, revisar...) | FP Sobrecarga: **{pattern_stats['Neutros Peligrosos']['FP']}** |\n")
        f.write(f"| **Sobrecarga Explícita** (urgente, plazo...) | FN Sobrecarga: **{pattern_stats['Sobrecarga Real']['FN']}** |\n")
        
        # Criterios de aceptación del modelo
        f.write("\n## 4. Validación de KPIs (Criterios de Aceptación)\n")
        
        # KPI A: Robustez ante falsos positivos en neutros
        fp_neutros_limit = 2 
        pass_a = pattern_stats['Neutros Peligrosos']['FP'] <= fp_neutros_limit
        icon_a = "OK" if pass_a else "NO OK"
        f.write(f"- {icon_a} **KPI A:** Robustez ante 'Neutros Adversarios' (FP <= {fp_neutros_limit}). Actual: {pattern_stats['Neutros Peligrosos']['FP']}\n")
        
        # KPI B: Sensibilidad (Recall) en Sobrecarga
        rec_sobr = report_dict["SOBRECARGA_URGENCIA"]["recall"]
        limit_b = 0.80
        pass_b = rec_sobr >= limit_b
        icon_b = "OK" if pass_b else "NO OK"
        f.write(f"- {icon_b} **KPI B:** Sensibilidad en Sobrecarga (Recall >= {limit_b}). Actual: {rec_sobr:.3f}\n")
        
    print(f"Informe Generado: {SUMMARY_MD}")

if __name__ == "__main__":
    main()
