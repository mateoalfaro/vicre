# Rúbrica de evaluación del LLM

Esta rúbrica evalúa `test/01_preguntas.md` sin incluir las respuestas.

Puntaje total sugerido: **8 puntos**.

- **Pregunta 1 - 1.0 punto:** notación y función de crecimiento correctas.
- **Pregunta 2 - 1.0 punto:** orden completo correcto. Puede darse 0.25 por cada método colocado en la posición correcta.
- **Pregunta 3 - 1.0 punto:** tres incisos. Sugerencia: 1/3 por cada inciso correcto.
- **Pregunta 4 - 1.0 punto:** debe identificar la opción asintótica completa; se aceptan formas algebraicamente equivalentes.
- **Pregunta 5 - 1.0 punto:** notación y base exponencial correctas.
- **Pregunta 6 - 1.0 punto:** debe identificar correctamente tanto la parte exponencial como la potencia de $n$.
- **Pregunta 7 - 1.0 punto:** respuesta categórica correcta; si el modelo propone un entero, es incorrecto.
- **Pregunta 8 - 1.0 punto:** 0.5 por la sumatoria y 0.5 por el O grande.

## Criterios adicionales

No penalice diferencias puramente sintácticas, por ejemplo:

- `Theta(n^19)` vs. $\Theta(n^{19})$.
- $(11/20)^{-n}$ vs. $(20/11)^n$.
- `((n-2)!)^5` vs. $((n-2)!)^5$.

Sí penalice cuando el modelo cambie el tipo de cota (`O`, `Omega`, `Theta`) o la función dominante.
