# Tarjetas de procedimiento de Wolfram

Estas tarjetas son la fuente operativa compacta para la Consulta. Describen
patrones, no respuestas de exámenes. No contienen preguntas, claves ni
rúbricas; tampoco se deben usar para copiar un resultado numérico.

Elige una o más tarjetas según lo que pida la captura y decláralas en el
marcador final `PROCEDIMIENTO: id[, id...]`.

## timing_repeated

Usa esta tarjeta cuando el examen pida construir datos de tiempo con
`RepeatedTiming` y dibujarlos con `ListLinePlot`. Cada método se mide en una
`Table`; conserva el orden de los métodos y el rango, inicio e incremento que
aparezcan en la captura:

```wl
data = Table[{n, RepeatedTiming[f[n]][[1]]}, {n, first, last, step}];
ListLinePlot[{data1, data2}, PlotLabels -> {"f", "g"}]
```

Adapta la cantidad de métodos y nombres a la captura. No sustituyas esta
medición por `PruebaADAGrafica`: son procedimientos de cursos/exámenes
distintos.

## timing_graphica

Usa esta tarjeta cuando la captura pida el experimento de la biblioteca del
curso. Llama a `PruebaADAGrafica` con las funciones, máximo, inicio y paso que
muestre la captura:

```wl
PruebaADAGrafica[{f, g}, max, first, step]
```

Algunos exámenes usan tres argumentos después de la lista y otros solo los
parámetros que muestra la pregunta. Copia esos operadores y argumentos sin
inventar una firma distinta. Esta tarjeta no reemplaza `timing_repeated`.

## asymptotic_sum

Para una sumatoria asintótica, construye la expresión con `Sum` y compara su
cociente con cada candidato mediante `Limit` cuando `n -> Infinity`:

```wl
Table[Limit[Sum[term, {i, lo, hi}]/candidate, n -> Infinity],
  {candidate, candidates}]
```

Usa la forma de la sumatoria, candidatos y notación (`Theta`, `O` u otra) que
correspondan a la captura. La tarjeta no da el candidato correcto.

## asymptotic_product

Para un producto asintótico, conserva `Product` para la expresión y usa
`Limit` sobre el cociente contra los candidatos o la forma propuesta:

```wl
Limit[Product[f[i], {i, lo, hi}]/candidate, n -> Infinity]
```

Copia literalmente los operadores de la captura, incluidos límites y
paréntesis. No conviertas el producto en una respuesta memorizada.

## comp_limit

Cuando la pregunta compare dos expresiones con el helper de la biblioteca,
usa `CompLimit` con ambas expresiones en el mismo orden:

```wl
CompLimit[{f, g}]
```

Sustituye `f` y `g` por las expresiones de la captura y determina el parámetro
solicitado a partir de esa comparación. La tarjeta no contiene valores de
parámetros ni respuestas.

## loop_count

Para contar ciclos, representa cada iteración relevante con una suma anidada
`Sum`. Si ayuda a obtener una fórmula cerrada, puedes construir una tabla de
conteos y pasarla a `FindSequenceFunction`; la suma sigue siendo obligatoria:

```wl
Sum[Sum[1, {j, 1, inner}], {i, 1, outer}]
```

Respeta los cambios de contador y los límites de la implementación que se ve
en la captura. Da por separado la sumatoria y el orden solicitado.

## numeric_compare

Cuando la captura pida comparar el valor concreto de varios métodos, incluye
una evaluación Wolfram con la entrada exacta de la pregunta, por ejemplo:

```wl
{f[input], g[input]} // N
```

No sustituyas la evaluación concreta por una descripción. Si la misma captura
también pide un experimento, declara además `timing_repeated` o
`timing_graphica` y ejecuta el procedimiento de tiempos correspondiente.
