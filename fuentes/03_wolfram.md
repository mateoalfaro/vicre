# Entrenamiento - Patrones de Wolfram Language vistos en el II examen

Fuente exclusiva: `Compilación #1 Exámenes Discretas(2).pdf`, sección **II EXAMEN**.

Este archivo no introduce comandos ajenos al examen. Resume los procedimientos que aparecen explícitamente en las capturas.

## 1. Comparar una expresión con funciones candidatas mediante límites

Patrón observado en las preguntas de notación asintótica:

```wl
funciones = {candidato1, candidato2, candidato3, ...};
Table[
  Limit[expresion/candidato, n -> Infinity],
  {candidato, funciones}
]
```

En la Pregunta 1 se usan candidatos como:

```wl
{7^(10 n), n 7^(10 n), n^9, n^8, n^7, n^6, n^5, n^4, n^3, n^2, n, 1}
```

La idea operativa mostrada por el examen es comparar el cociente `expresion/candidato` cuando `n -> Infinity`.

## 2. Producto y `Limit`

En la Pregunta 2 aparece:

```wl
Limit[
  Product[2^i/(16 i^2), {i, 2, -1 + n}]/(2^n^2/n!),
  n -> Infinity
]
```

Salida mostrada:

```text
0
```

## 3. Contar iteraciones con `Table` y `FindSequenceFunction`

En la Pregunta 3 aparece el patrón:

```wl
Clear[cont, i]
FindSequenceFunction[
  Table[
    cont = 0;
    For[i = 1, i <= k^3 + 2, cont = cont + 1; i = i + 1];
    cont,
    {k, 1, 30}
  ],
  n
]
```

Después se representa el trabajo interno con una suma:

```wl
Sum[Sum[1, {j, 1, i + 6}], {i, 1, %}]
```

## 4. Comparar dos funciones con un helper llamado `CompLimit`

La Pregunta 4 muestra una llamada del tipo:

```wl
CompLimit[{f, g}]
```

La definición de `CompLimit` **no aparece en la captura**, por lo que este corpus no inventa su implementación.

## 5. Comparación experimental con `PruebaADAGrafica`

Las preguntas 5 y 6 muestran:

```wl
PruebaADAGrafica[{Programa1, Programa2, Programa3, Programa4}, 25, 6]
```

y

```wl
PruebaADAGrafica[{Programa1, Programa2}, 200, 1, 20]
```

La definición de `PruebaADAGrafica` **no aparece en la captura**. El examen la usa para comparar tiempos experimentalmente.

## 6. Evaluación numérica

En la Pregunta 6 se fuerza formato decimal con:

```wl
{Programa1[10] // N, Programa2[10] // N}
```
