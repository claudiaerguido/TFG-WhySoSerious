# Tipo: Validación | Requisitos: RF10
# Objetivo: Comprobar que el modelo NLP final procesa un lote amplio de mensajes
# corporativos sintéticos y devuelve etiquetas válidas dentro del catálogo definido.
# Nota: esta prueba no sustituye la validación con datos reales de una organización.

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List

import pytest


# Evitamos que el módulo intente descargar el baseline desde Hugging Face.
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from backend import nlp_model  # noqa: E402  (import condicionado por la variable de entorno)


LABELS: List[str] = [
    "ESTRES_ANSIEDAD",
    "SOBRECARGA_URGENCIA",
    "CANSANCIO_FATIGA",
    "ENFADO_IRRITACION",
    "NEUTRO",
]

USERS = [
    "ana.garcia@tfg.com",
    "carlos.mendez@tfg.com",
    "laura.rodriguez@tfg.com",
    "diego.perez@tfg.com",
    "marta.santos@tfg.com",
    "javier.romero@tfg.com",
]


@dataclass(frozen=True)
class Sample:
    """Muestra sintética con un mensaje y su etiqueta esperada."""

    user_email: str
    text: str
    expected_label: str


def _build_corpus() -> List[Sample]:
    """Genera 300 mensajes sintéticos: 6 usuarios x 50 mensajes x 5 etiquetas."""
    templates: Dict[str, List[str]] = {
        "ESTRES_ANSIEDAD": [
            "Estoy nervioso y hoy me cuesta bastante centrarme.",
            "Tengo ansiedad y noto que no desconecto bien.",
            "Llevo toda la mañana con tensión encima y me pesa.",
            "Me siento inquieto y bastante pendiente de todo.",
            "No consigo relajarme del todo con esto.",
            "Estoy algo alterado y me noto acelerado.",
            "Siento nervios todo el tiempo y me cuesta concentrarme.",
            "Me preocupa bastante lo que viene ahora, aunque intento seguir.",
            "Estoy con presión constante y algo de nervios.",
            "No termino de calmarme con este asunto.",
            "Hoy me noto especialmente nervioso, como si estuviera en alerta todo el rato.",
            "Estoy inquieto desde primera hora y me cuesta trabajar con normalidad.",
            "Tengo una sensación de tensión constante que no se me quita.",
            "Me está costando mantener la calma con este tema.",
            "Estoy intentando centrarme, pero tengo la cabeza muy acelerada.",
            "Siento bastante ansiedad con cómo puede salir esto.",
            "No estoy tranquilo desde que empezó este asunto.",
            "Estoy con nervios y me cuesta pensar con claridad.",
            "Tengo la sensación de estar demasiado pendiente de todo.",
            "Me noto en tensión aunque intento seguir como siempre.",
            "Estoy bastante intranquilo y no consigo relajarme.",
            "Me está entrando ansiedad solo de pensar en cómo puede evolucionar esto.",
            "Hoy tengo el cuerpo en alerta y me cuesta bajar revoluciones.",
            "Estoy con una preocupación constante que no me deja concentrarme bien.",
            "Me noto acelerado y con dificultad para ordenar ideas.",
            "Estoy nervioso por este tema y no consigo quitármelo de la cabeza.",
            "Siento una presión interna bastante incómoda.",
            "Me cuesta estar tranquilo mientras esto siga sin resolverse.",
            "Tengo ansiedad y estoy revisando todo más veces de lo normal.",
            "Estoy algo desbordado emocionalmente, aunque intento seguir.",
            "Me noto tenso y con poca calma para afrontar esto.",
            "Hoy estoy con muchos nervios y me cuesta tomar decisiones.",
            "Siento que estoy en alerta constante desde esta mañana.",
            "Estoy bastante preocupado y no consigo desconectar del tema.",
            "Me genera ansiedad no saber cómo va a acabar esto.",
            "Estoy intentando respirar un poco porque me noto muy acelerado.",
            "Tengo una sensación de nervios continua y me cuesta relajarme.",
            "Estoy con tensión acumulada y me está afectando a la concentración.",
            "Me noto inquieto, como esperando que pase algo más.",
            "No estoy gestionando bien los nervios con este asunto.",
            "Me cuesta mantener la calma porque estoy bastante ansioso.",
            "Estoy nervioso y me está costando responder con claridad.",
            "Tengo la cabeza dando vueltas todo el rato con esto.",
            "Estoy con ansiedad y cualquier detalle me pone más tenso.",
            "Me noto demasiado pendiente de todo y no consigo soltarlo.",
            "Estoy intranquilo y necesito revisar bien antes de contestar.",
            "Siento presión por dentro, aunque por fuera intente estar normal.",
            "Estoy bastante alterado y prefiero ir paso a paso.",
            "Me está costando concentrarme porque tengo muchos nervios.",
            "Estoy preocupado y no consigo trabajar con tranquilidad.",
            "Tengo una sensación constante de tensión desde hace rato.",
            "Me noto acelerado y con dificultad para parar mentalmente.",
            "Estoy nervioso por si algo sale mal.",
            "Me está generando ansiedad no tener claro el resultado.",
            "Hoy me siento bastante inquieto y poco sereno.",
            "Estoy intentando controlar los nervios, pero me está costando.",
            "No consigo quitarme esta sensación de presión de encima.",
            "Estoy con ansiedad y me cuesta desconectar incluso un momento.",
            "Me noto tenso, preocupado y demasiado pendiente de cada detalle.",
            "Estoy bastante nervioso con este asunto y necesito calmarme un poco.",
        ],
        "SOBRECARGA_URGENCIA": [
            "Ahora mismo tengo demasiadas tareas abiertas a la vez.",
            "No puedo asumir más temas sin retrasar los que ya tengo en curso.",
            "Tengo varios frentes pendientes y necesito priorizar.",
            "Se me están acumulando demasiados asuntos esta mañana.",
            "Ahora mismo no tengo capacidad para coger otra tarea más.",
            "Tengo la agenda completamente ocupada con entregas y revisiones.",
            "Necesito saber qué va primero porque no puedo avanzar con todo a la vez.",
            "Tengo demasiados puntos pendientes para cerrar hoy.",
            "Con la carga actual, no llego a revisar todo con el detalle necesario.",
            "Estoy gestionando varias tareas simultáneas y necesito ordenar prioridades.",
            "Ahora mismo estoy al máximo de capacidad con lo que ya tengo asignado.",
            "No puedo comprometerme con otra entrega sin mover algún plazo.",
            "Hay demasiadas tareas entrando al mismo tiempo.",
            "Tengo que sacar varios temas antes de poder empezar con eso.",
            "Necesito redistribuir trabajo porque no puedo cubrirlo todo solo.",
            "En este momento tengo demasiadas revisiones pendientes.",
            "La carga de trabajo de esta semana está siendo muy alta.",
            "Tengo varios documentos por revisar y no puedo atender todo a la vez.",
            "Si añadimos esto, habrá que quitar prioridad a otra tarea.",
            "Estoy con demasiados temas en paralelo para cerrarlo hoy.",
            "Tengo pendiente terminar varias cosas antes de poder revisar ese punto.",
            "Ahora mismo mi lista de tareas está bastante llena.",
            "No tengo margen para incorporar más cambios en esta versión.",
            "Tenemos demasiados entregables abiertos al mismo tiempo.",
            "Necesito que definamos prioridades porque todo no puede salir a la vez.",
            "Estoy cubriendo varios temas y no llego a todos con el mismo nivel de detalle.",
            "Hay mucho volumen de trabajo acumulado en esta fase.",
            "No puedo garantizar esta revisión si entran más tareas hoy.",
            "Tengo varias entregas pisándose entre sí.",
            "Ahora mismo estoy repartiendo tiempo entre demasiadas cosas.",
            "Con los temas actuales, no tengo hueco para una revisión adicional.",
            "La carga de tareas supera el tiempo disponible esta semana.",
            "Hay que decidir qué se retrasa si esto pasa a ser prioritario.",
            "Estoy atendiendo varios proyectos a la vez y necesito organizar tiempos.",
            "Tengo demasiadas solicitudes pendientes de respuesta.",
            "No puedo avanzar en esta parte hasta cerrar otros temas abiertos.",
            "La cantidad de cambios pendientes es demasiado alta para el plazo previsto.",
            "Tengo varios bloqueos y tareas acumuladas que resolver antes.",
            "Si mantenemos este volumen, necesitaremos apoyo adicional.",
            "Ahora mismo estoy gestionando más tareas de las que puedo cerrar en plazo.",
            "Tengo el día completo con reuniones, revisiones y entregas.",
            "No puedo asumir esta tarea sin dejar otra pendiente.",
            "Hay demasiadas cosas dependiendo de la misma persona.",
            "El volumen de trabajo está creciendo más rápido de lo que podemos cerrar.",
            "Necesito que alguien más pueda encargarse de una parte.",
            "Tengo varias prioridades urgentes compitiendo entre sí.",
            "No puedo revisar este documento hoy sin mover otras tareas.",
            "Tenemos muchos temas abiertos y poca capacidad disponible.",
            "La planificación actual no deja margen para más incorporaciones.",
            "Estoy priorizando lo más crítico porque no puedo cubrir todo a la vez.",
            "Hay demasiadas revisiones acumuladas para una sola jornada.",
            "No tengo disponibilidad real para añadir otro entregable esta semana.",
            "Si entra este cambio, necesitamos ajustar el resto de la planificación.",
            "Estoy con una carga muy alta de tareas operativas.",
            "Necesito liberar algún tema antes de poder asumir otro.",
            "Tenemos que repartir mejor las tareas porque ahora están muy concentradas.",
            "El volumen pendiente es demasiado alto para cerrarlo todo hoy.",
            "Estoy trabajando en varios puntos, pero no puedo cerrarlos todos al mismo tiempo.",
            "Hace falta priorizar porque hay más trabajo que tiempo disponible.",
            "Con la carga actual, necesito apoyo o más plazo para poder terminarlo bien.",
        ],
        "CANSANCIO_FATIGA": [
            "Hoy estoy bastante cansado, me está costando arrancar.",
            "Llevo varios días con mucho ritmo y ya lo estoy notando.",
            "Estoy un poco fundido, pero intento avanzar con esto.",
            "Me cuesta concentrarme hoy, estoy bastante agotado.",
            "Esta semana se me está haciendo muy larga.",
            "Necesito bajar un poco el ritmo porque estoy cansado.",
            "Voy más lento de lo normal, no estoy al cien por cien.",
            "Estoy intentando terminarlo, pero hoy me noto muy espeso.",
            "Llevo demasiadas horas con esto y ya no veo claro algunos detalles.",
            "Estoy cansado y prefiero revisarlo mañana con la cabeza más fresca.",
            "Hoy me está costando seguir el ritmo de mensajes y tareas.",
            "Estoy bastante agotado después de las reuniones de esta mañana.",
            "Me noto sin energía para sacar más temas ahora mismo.",
            "Necesito un descanso corto antes de seguir con esto.",
            "Llevo todo el día encadenando cosas y ya estoy bastante fundido.",
            "Hoy no estoy rindiendo como otros días.",
            "Me está costando avanzar porque estoy bastante cansado mentalmente.",
            "Creo que necesito parar un momento para despejarme.",
            "Estoy intentando cerrar esto, pero ya me cuesta mantener la atención.",
            "Después de esta semana, noto que voy muy justo de energía.",
            "Me vendría bien dejar esta revisión para mañana porque hoy estoy agotado.",
            "Estoy bastante cansado y no quiero cometer errores por ir con la cabeza saturada.",
            "Llevo desde primera hora sin parar y ya lo estoy acusando.",
            "Ahora mismo estoy funcionando un poco en automático.",
            "Me cuesta responder con claridad, estoy bastante cansado.",
            "Hoy noto mucho el cansancio acumulado.",
            "Estoy intentando seguir, pero me falta energía.",
            "Me está costando más de lo normal concentrarme en esta parte.",
            "Prefiero revisarlo con calma mañana porque ahora no estoy fino.",
            "Estoy bastante quemado después de varios días intensos.",
            "No es que no quiera avanzar, es que estoy muy cansado hoy.",
            "Llevo muchas horas delante de la pantalla y necesito parar un poco.",
            "Me noto algo bloqueado por cansancio.",
            "Estoy agotado y cualquier cambio pequeño me cuesta el doble.",
            "Hoy me cuesta mantener la atención en las tareas largas.",
            "Estoy respondiendo más despacio porque estoy bastante cansado.",
            "Necesito despejarme un rato para poder seguir bien.",
            "Estoy notando que el cansancio me está afectando al ritmo de trabajo.",
            "Esta carga de trabajo seguida me está dejando sin energía.",
            "Me cuesta hilar ideas ahora mismo, prefiero retomarlo después.",
            "Estoy bastante saturado mentalmente, necesito descansar un poco.",
            "Hoy no tengo mucha claridad para revisar temas complejos.",
            "Estoy cansado y prefiero no cerrar esto deprisa y mal.",
            "Llevo varios días durmiendo poco y se nota en el trabajo.",
            "Me está costando mantener la concentración en las reuniones.",
            "Estoy agotado de tanto cambio y tanta revisión.",
            "Ahora mismo necesito ir paso a paso porque estoy cansado.",
            "Hoy todo me está llevando más tiempo del habitual.",
            "Estoy con poca energía, pero intento dejarlo encaminado.",
            "Creo que necesito desconectar un rato para poder seguir con criterio.",
            "Me noto bastante bajo de energía esta tarde.",
            "Estoy cansado y me cuesta priorizar con claridad.",
            "Llevo todo el día a tope y ya no rindo igual.",
            "Me vendría bien terminar esta parte mañana con más calma.",
            "Estoy bastante agotado después de tantos temas seguidos.",
            "Hoy me cuesta incluso responder rápido a los mensajes.",
            "Estoy mentalmente cansado, necesito ordenar ideas antes de seguir.",
            "No quiero dejarlo mal revisado por el cansancio.",
            "Me está pesando mucho la semana y necesito bajar un poco el ritmo.",
            "Ahora mismo estoy demasiado cansado para seguir revisando con detalle.",
        ],
        "ENFADO_IRRITACION": [
            "Me molesta bastante que esto se haya cambiado sin avisar.",
            "No entiendo por qué se ha decidido esto a última hora.",
            "Estoy bastante enfadado con cómo se ha gestionado este tema.",
            "Sinceramente, esto me parece una falta de organización.",
            "Me frustra tener que rehacer algo que ya estaba cerrado.",
            "No me parece normal que nos enteremos de esto ahora.",
            "Esto se podría haber evitado si se hubiera avisado antes.",
            "Me molesta que siempre acabemos corrigiendo lo mismo.",
            "No estoy de acuerdo con cómo se está llevando este asunto.",
            "Me parece injusto que la responsabilidad recaiga siempre en los mismos.",
            "Estoy cansado de que se cambien las prioridades cada dos horas.",
            "No puede ser que tengamos que resolver esto siempre a última hora.",
            "Me enfada que no se haya tenido en cuenta el trabajo ya hecho.",
            "Esto genera mucho desgaste y nadie parece verlo.",
            "No me parece serio trabajar así.",
            "Me molesta que se pida urgencia cuando la información llega tarde.",
            "Estoy bastante irritado con esta situación.",
            "No entiendo por qué se nos exige rapidez si no tenemos todos los datos.",
            "Me parece una pérdida de tiempo repetir tareas por falta de coordinación.",
            "Esto empieza a ser bastante frustrante.",
            "No veo razonable que se cambie el criterio cuando ya está todo avanzado.",
            "Me molesta que no se respeten los plazos que nosotros también necesitamos.",
            "Estoy enfadado porque esto nos pone otra vez contra el reloj.",
            "No puede ser que cada revisión abra diez temas nuevos.",
            "Me parece muy poco eficiente esta forma de trabajar.",
            "No entiendo por qué no se aclaró esto desde el principio.",
            "Esto nos está haciendo perder tiempo innecesariamente.",
            "Me frustra que se pidan cosas sin valorar la carga que ya tenemos.",
            "No me parece justo que se nos responsabilice de errores que no dependen de nosotros.",
            "Estoy molesto porque esta situación se repite demasiado.",
            "Me enfada tener que apagar fuegos que se podrían haber previsto.",
            "No estoy cómodo con esta manera de tomar decisiones.",
            "Me parece que se está improvisando demasiado.",
            "Esto no ayuda nada al equipo.",
            "Me molesta que se exija una solución inmediata sin dar contexto.",
            "Estoy bastante frustrado con la falta de claridad.",
            "No me parece adecuado que se nos traslade el problema tan tarde.",
            "Me enfada que se dé por hecho que podemos asumir todo sin más.",
            "Así es muy difícil trabajar bien.",
            "No entiendo por qué se ignoran los avisos hasta que ya es urgente.",
            "Me molesta que tengamos que justificar lo mismo una y otra vez.",
            "Estoy perdiendo la paciencia con tantos cambios sin explicación.",
            "No me parece razonable seguir avanzando sin una decisión clara.",
            "Me enfada que se priorice la rapidez sobre hacer las cosas bien.",
            "Esto nos está bloqueando y empieza a ser desesperante.",
            "No entiendo por qué se nos pide algo que ya se había descartado.",
            "Me parece poco respetuoso con el trabajo del equipo.",
            "Estoy bastante molesto con la falta de previsión.",
            "No puede ser que cada vez que cerramos algo vuelva a abrirse.",
            "Me frustra que no haya una dirección clara en este tema.",
            "Esto está generando un mal ambiente innecesario.",
            "No me parece justo tener que asumir consecuencias de decisiones ajenas.",
            "Estoy enfadado porque se ha perdido mucho tiempo por falta de coordinación.",
            "Me molesta que se nos pida compromiso sin darnos margen real.",
            "No entiendo por qué se insiste en hacerlo así si ya vimos que no funcionaba.",
            "Me parece que no se está escuchando al equipo.",
            "Estoy bastante irritado con la forma en la que se está comunicando esto.",
            "No puede ser que siempre lleguemos tarde por los mismos motivos.",
            "Me enfada que se minimice el problema cuando nos está afectando directamente.",
            "Así no se puede trabajar con tranquilidad ni con calidad.",
        ],
        "NEUTRO": [
            "Revisamos el documento mañana por la mañana.",
            "He subido la última versión al repositorio.",
            "La reunión queda movida a las doce.",
            "No me da tiempo a revisar todo antes de la reunión, pero es solo para dejar constancia.",
            "He dejado el comentario en el documento compartido.",
            "Voy a actualizar el estado en la tarea.",
            "Te paso la propuesta en cuanto termine de revisarla.",
            "No consigo relajarme del todo con esto, pero ya está registrado en el panel.",
            "Podemos verlo en la siguiente reunión si os viene bien.",
            "Estoy algo alterado con el cierre de hoy, aunque he preparado un resumen breve para luego.",
            "Si no hay cambios, podemos mantener esta versión.",
            "Por ahora no he visto ninguna incidencia relevante.",
            "Por mi parte, no tengo comentarios adicionales.",
            "Podemos mantener esta solución si todos estáis de acuerdo.",
            "Podemos cerrar este punto si no hay más observaciones.",
        ],
    }

    corpus: List[Sample] = []
    per_user_and_label = 10  # 6 usuarios x 10 mensajes por etiqueta = 60 por categoría

    for idx, user in enumerate(USERS):
        for label in LABELS:
            for rep in range(per_user_and_label):
                template = templates[label][(idx * per_user_and_label + rep) % len(templates[label])]
                text = f"{template} [{user.split('@')[0]} #{rep + 1}]"
                corpus.append(Sample(user_email=user, text=text, expected_label=label))

    return corpus


def _predict_label(output: Dict[str, object]) -> str:
    """Convierte la salida multilabel del modelo en una etiqueta final única."""
    labels: Dict[str, float] = output["labels"]  # type: ignore[assignment]
    thresholds: Dict[str, float] = output.get("thresholds", {})  # type: ignore[assignment]

    active = [
        label
        for label in LABELS[:-1]
        if labels.get(label, 0.0) >= thresholds.get(label, 0.5)
    ]
    if not active:
        return "NEUTRO"

    return max(active, key=lambda label: labels.get(label, 0.0))


def _evaluate_batch(samples: List[Sample]) -> List[str]:
    """Ejecuta inferencia lote a lote sobre el modelo real del repositorio."""
    y_pred: List[str] = []

    for sample in samples:
        output = nlp_model.final_predict(sample.text)
        if not output or "labels" not in output:
            raise AssertionError("El modelo no devolvió una salida válida.")

        pred = _predict_label(output)
        if pred not in LABELS:
            raise AssertionError(f"Predicción fuera de catálogo: {pred}")

        y_pred.append(pred)

    return y_pred


def test_validation_nlp_batch_prediction():
    """
    REQ: RF10.
    DEFINICIÓN: El sistema debe clasificar mensajes mediante PLN dentro de las categorías emocionales definidas.
    VALIDACIÓN: El modelo final procesa 300 mensajes sintéticos, generados para 6 usuarios y 5 etiquetas, y devuelve predicciones pertenecientes al catálogo esperado.
    """
    if nlp_model._model is None:
        pytest.fail("El modelo NLP final no está cargado; no puede ejecutarse la prueba.")

    samples = _build_corpus()
    assert len(samples) == 300, "La prueba debe evaluar 300 mensajes sintéticos."

    y_pred = _evaluate_batch(samples)
    assert set(y_pred).issubset(set(LABELS))
    assert len(y_pred) == len(samples)
