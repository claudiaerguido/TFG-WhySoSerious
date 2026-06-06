import os
import random
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from db_client import get_supabase_client
from db_repository import save_risk_metrics
import nlp_model

# CONVERSACIONES TÍPICAS POR ESTADO DEL PROYECTO
CONV_HEALTHY = [
    "Buenos días equipo, ¿empezamos la daily?",
    "Sí, yo ya he subido la pull request para que la reviséis.",
    "Genial, la miro ahora mismo y te la apruebo.",
    "Perfecto, el despliegue ha ido sin problemas.",
    "Buen trabajo hoy, equipo. Cierro por hoy, hasta mañana.",
    "La demo con el cliente ha sido un éxito, están muy contentos.",
    "Todo bajo control con mi parte del ticket.",
    "He dejado la documentación actualizada en la wiki."
]

CONV_MODERATE = [
    "Oye, tenemos un par de bugs menores en producción.",
    "Voy un poco retrasado con mi tarea, ¿alguien me echa una mano?",
    "Me pongo contigo en 5 minutos y lo miramos.",
    "El cliente ha pedido un cambio de última hora, pero es pequeño.",
    "Uf, hoy está siendo un día un poco denso de reuniones.",
    "A ver si cerramos esto hoy, que se nos acumula para el sprint.",
    "No me funciona el entorno local, ¿a ti te va bien?",
    "Me está costando un poco entender esta parte del código nuevo."
]

CONV_CRITICAL = [
    "¡Se ha caído producción! ¿Quién ha tocado la base de datos?",
    "No llego a la entrega ni de broma, esto es imposible.",
    "Llevo 12 horas trabajando y esto sigue fallando, estoy harto.",
    "Otra vez nos cambian los requisitos, no puedo trabajar así.",
    "Es insoportable la carga de trabajo que tenemos ahora mismo en este proyecto.",
    "Siento que voy a explotar con tanta presión.",
    "Nadie me ayuda con esto y estoy bloqueado, es muy frustrante.",
    "Me duele la cabeza, llevo demasiadas horas seguidas mirando logs."
]

def run_simulation(days=30):
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Error: No se pudo conectar a Supabase.")
        return
        
    print("⏳ Cargando modelo de Inteligencia Artificial (esto puede tardar)...")
    if nlp_model._model is None:
        nlp_model._load_model()
        
    # Obtener proyectos activos
    projects_res = supabase.table("projects").select("id, name").execute()
    projects = projects_res.data
    
    if not projects:
        print("⚠️ No hay proyectos en la BBDD.")
        return

    # Obtener miembros por proyecto
    pm_res = supabase.table("project_members").select("project_id, user_email").is_("end_date", "null").execute()
    project_members = {}
    for pm in pm_res.data:
        pid = pm["project_id"]
        if pid not in project_members:
            project_members[pid] = []
        project_members[pid].append(pm["user_email"])

    # Asignar una "salud" a cada proyecto para que los datos tengan sentido
    # 1 proyecto MUY ESTRESADO (CRITICAL)
    # 1 o 2 proyectos REGULARES (MODERATE)
    # El resto TRANQUILOS (HEALTHY)
    random.shuffle(projects)
    project_states = {}
    
    for i, p in enumerate(projects):
        pid = p["id"]
        if i == 0:
            project_states[pid] = "CRITICAL"
        elif i == 1 or i == 2:
            project_states[pid] = "MODERATE"
        else:
            project_states[pid] = "HEALTHY"
            
        print(f"📌 Proyecto '{p['name']}' -> Estado simulado: {project_states[pid]}")

    now = datetime.utcnow()
    total_inserted = 0

    print(f"\n🚀 Generando conversaciones inter-miembros durante {days} días...")

    for i in range(days):
        current_date = now - timedelta(days=i)
        
        if current_date.weekday() >= 5 and random.random() > 0.1:
            continue
            
        for p in projects:
            pid = p["id"]
            members = project_members.get(pid, [])
            
            # Si el proyecto tiene menos de 2 personas, es difícil que hablen entre ellos, pero simulamos igual
            if not members:
                continue
                
            state = project_states[pid]
            
            # Elegir qué set de frases usar según la situación natural del proyecto
            if state == "CRITICAL":
                msg_pool = CONV_CRITICAL
                msgs_per_conversation = random.randint(3, 8)
            elif state == "MODERATE":
                msg_pool = CONV_MODERATE
                msgs_per_conversation = random.randint(2, 5)
            else:
                msg_pool = CONV_HEALTHY
                msgs_per_conversation = random.randint(1, 3)

            # Generamos un "hilo" de conversación
            hour = random.randint(9, 17)
            minute = random.randint(0, 50)
            
            for m_idx in range(msgs_per_conversation):
                # Turno de palabra: elegimos un miembro aleatorio del proyecto
                speaker = random.choice(members)
                text = random.choice(msg_pool)
                
                prediction = nlp_model.final_predict(text)
                scores = prediction.get("labels", {})
                
                # Cada mensaje ocurre unos minutos después del anterior
                minute += random.randint(1, 5)
                if minute >= 60:
                    hour += 1
                    minute -= 60
                
                # Evitar pasar de medianoche
                if hour >= 24: hour = 23
                    
                msg_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                msg_id = f"sim_conv_{uuid.uuid4().hex[:10]}"
                
                save_risk_metrics(
                    supabase=supabase,
                    user_email=speaker,
                    timestamp=msg_time.isoformat() + "Z",
                    scores=scores,
                    message_id=msg_id,
                    project_id=pid
                )
                total_inserted += 1

    print(f"\n✅ ¡Simulación completada! Se han analizado con la IA y guardado {total_inserted} mensajes entre compañeros de proyectos.")

if __name__ == "__main__":
    run_simulation()
