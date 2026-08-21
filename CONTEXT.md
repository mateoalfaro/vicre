# Vicre

Servicio de usuario que captura la pantalla, consulta a OpenCode con las fuentes del curso y escribe la respuesta directamente donde esté escribiendo el usuario.

## Language

**Vicre**:
El programa completo: daemon de usuario + CLI (`vicre capture|paste1|paste2`) + módulo de NixOS.
_Avoid_: el servicio, el bot

**Captura**:
Captura de pantalla completa (todos los monitores) tomada al activar el atajo de captura; se guarda en `~/.vicre/photos`.
_Avoid_: screenshot, foto suelta

**Acciones**:
Los tres atajos globales: **Capturar** (`ctrl+i`, inicia la Consulta), **Pegar respuesta** (`ctrl+o`, escribe la Respuesta Tipo 1) y **Pegar código** (`ctrl+p`, escribe la Respuesta Tipo 2).
_Avoid_: comandos, hotkeys

**Consulta**:
El ciclo completo: captura → prompt fijo + imagen enviados a OpenCode → respuesta parseada y almacenada en memoria.
_Avoid_: request, pregunta

**Respuesta Tipo 1**:
Texto con las respuestas directas a cada pregunta/parte vacía de la Captura, numeradas como en la foto (ej. `#1: 23`). Lo que pega `ctrl+o`.
_Avoid_: respuesta corta, solución

**Respuesta Tipo 2**:
Código Wolfram Mathematica que verifica los resultados de la Respuesta Tipo 1, listo para pegar en Mathematica. Lo que pega `ctrl+p`.
_Avoid_: código de verificación, script

**Fuentes**:
Los PDFs del curso (capítulos y compilaciones de exámenes) que viajan dentro del paquete de Vicre y se exponen en `~/.vicre/fuentes` para que OpenCode los consulte.
_Avoid_: biblioteca, documentos

**Directorio de trabajo**:
`~/.vicre`: contiene `photos/`, `fuentes/` y es el cwd desde el que corre OpenCode.
_Avoid_: home de vicre, data dir
