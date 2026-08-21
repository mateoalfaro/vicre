PROMPT = "Esta foto es una pregunta de un examen de matemáticas discretas que se resuelve con Wolfram Mathematica, empleando la biblioteca de Vilcretas. Con base en tus fuentes presentes en fuentes/, responde EXACTAMENTE en dos secciones, sin ningún texto fuera de ellas:\n\nRESPUESTA_TIPO1: respuestas directas a cada pregunta o parte vacía de la foto, numeradas como aparecen en ella (por ejemplo: #1: 23, #2: 45/2). Sin explicaciones ni desarrollo.\n\nRESPUESTA_TIPO2: el código Wolfram Mathematica que verifica cada resultado de RESPUESTA_TIPO1 (donde sea apropiado), listo para pegar en un notebook.\n\nLa imagen de la pregunta está en <IMAGE_PATH>."


def build_prompt(image_path):
    return PROMPT.replace("<IMAGE_PATH>", image_path)