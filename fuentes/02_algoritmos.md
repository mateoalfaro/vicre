# Entrenamiento - Análisis de algoritmos, ciclos y recursividad

Fuente exclusiva: `Compilación #1 Exámenes Discretas(2).pdf`, sección **II EXAMEN**, páginas 4-6.

## Ejemplo 1 - Traducir ciclos anidados a una suma

**Pregunta 3**

El método mostrado es, en esencia:

```wl
Programa[n_] := Module[{p = 1, i, j},
  For[i = 1, i <= n^3 + 2,
    For[j = 1, j <= i + 6, p = p - 2000; j++];
    i = i + 1
  ];
  Return[p]
]
```

El examen pregunta por la suma que representa el tiempo empleado en los ciclos.

**Respuesta marcada como correcta**

$$
\sum_{i=1}^{n^3+2}\left(\sum_{j=1}^{i+6}1\right).
$$

Luego pide un análisis O grande.

**Respuesta marcada como correcta**

$$
O(n^6).
$$

El examen muestra como apoyo:

```wl
Clear[cont, i]
FindSequenceFunction[
  Table[cont = 0; For[i = 1, i <= k^3 + 2, cont = cont + 1; i = i + 1]; cont, {k, 1, 30}],
  n
]
Sum[Sum[1, {j, 1, i + 6}], {i, 1, %}]
```

---

## Ejemplo 2 - Cuatro implementaciones y comparación experimental

**Pregunta 5**

El examen presenta cuatro programas que realizan la misma tarea:

```wl
Programa1[n_, valor_: 60/5846006549323611671624303190352640062064535163787] :=
  If[n == 6,
    valor,
    Programa1[n - 1,
      valor*(-((3 + 19 (-3 + n))/(-8^(18 (-3 + n)) + 13^(9 (-3 + n)) - 20^(7 (-3 + n)))))
    ]
  ]

Programa2[n_] :=
  If[n == 6,
    60/5846006549323611671624303190352640062064535163787,
    Programa2[n - 1]*(-((3 + 19 (-3 + n))/(-8^(18 (-3 + n)) + 13^(9 (-3 + n)) - 20^(7 (-3 + n)))))
  ]

Programa3[n_] := Module[{i, valor = 1},
  For[i = 3, i <= n - 3,
    valor = valor*(3 + 19 i)/(8^(18 i) - 13^(9 i) + 20^(7 i));
    i++
  ];
  valor
]

Programa4[n_] := Product[
  (3 + 19 i)/(8^(18 i) - 13^(9 i) + 20^(7 i)),
  {i, 3, n - 3}
]
```

La instrucción es ordenar los métodos de 1 (más rápido) a 4 (más lento) **mediante un experimento**.

El procedimiento mostrado es:

```wl
PruebaADAGrafica[{Programa1, Programa2, Programa3, Programa4}, 25, 6]
```

**Importante para el corpus:** la captura no muestra el resultado correcto del ranking; solamente muestra que la selección hecha por el estudiante fue incorrecta. Por fidelidad a la fuente, no se inventa un orden correcto en este archivo.

---

## Ejemplo 3 - Recursividad de cola frente a recursividad de pila

**Pregunta 6**

El examen compara:

```wl
Programa1[n_, valor_: 78124999/175781250] :=
  If[n == 1,
    valor,
    Programa1[n - 1,
      valor + ((5^(-10 n) (-1 + 2 5^(10 n) + 6 5^(10 n) n^3))/(2 (2 + 7 n^2)))
    ]
  ]

Programa2[n_] :=
  If[n == 1,
    78124999/175781250,
    Programa2[n - 1] + ((5^(-10 n) (-1 + 2 5^(10 n) + 6 5^(10 n) n^3))/(2 (2 + 7 n^2)))
  ]
```

El examen da tres resultados correctos:

1. Para $n=10$, ambos métodos producen en formato decimal:

```text
23.433
```

2. El método que usa **recursividad de pila** es:

```text
Programa2
```

3. En el experimento con valores de 1 a 200 e incremento de 20, el método más rápido es:

```text
Programa1
```

El procedimiento mostrado es:

```wl
{Programa1[10] // N, Programa2[10] // N}
PruebaADAGrafica[{Programa1, Programa2}, 200, 1, 20]
```
