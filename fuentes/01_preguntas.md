# Prueba - Examen 2 sin respuestas

Fuente exclusiva: `Compilación #2 Exámenes Discretas(1).pdf`, sección **Examen 2**, páginas 4-8.

**No use `test/02_clave.md` en el contexto del modelo durante esta prueba.**

## Pregunta 1

Halle la notación asintótica que mejor se ajuste a:

$$
\sum_{i=1}^{3n-1}\left(\left(\frac12\right)^i+\left(i+\frac12\right)^6+100\right)^3.
$$

Responda en la forma `Theta(...)`.

---

## Pregunta 2

Considere cuatro algoritmos que realizan la misma tarea. Todos calculan la sucesión con condiciones iniciales

$$
a_0=4,\qquad a_1=7,\qquad a_2=6,
$$

y relación

$$
a_n=a_{n-1}-a_{n-2}+a_{n-3}.
$$

Las implementaciones son:

```wl
f1[n_] := f1[n - 1] - f1[n - 2] + f1[n - 3]
f1[0] = 4; f1[1] = 7; f1[2] = 6;

f2[n_] := Which[
  n == 0, 4,
  n == 1, 7,
  n == 2, 6,
  n > 2, f2[n - 1] - f2[n - 2] + f2[n - 3]
]

f3[n_] := Module[{g},
  g[i_, a_, ta_, tta_] := Which[
    n == 0, tta,
    n == 1, ta,
    n == 2, a,
    i == n, a - ta + tta,
    True, g[i + 1, a - ta + tta, a, ta]
  ];
  g[3, 6, 7, 4]
]

f4[n_] := Module[{i, s = 0},
  For[i = 1, i <= n, i++, s = s + i];
  Which[
    n == 0, 4,
    n == 1, 7,
    n == 2, 6,
    n > 2, f4[n - 1] - f4[n - 2] + f4[n - 3]
  ]
]
```

Se realiza un experimento para $n$ entre 5 y 20, con incremento 1. Ordene `f1`, `f2`, `f3`, `f4` desde el más rápido (1) hasta el más lento (4).

---

## Pregunta 3

Considere:

```wl
f[n_, s_: 0] := Module[{digito = Mod[n, 10], suma = s},
  If[n == 0,
    suma,
    If[Mod[digito, 2] == 0, suma = suma + digito];
    f[(n - digito)/10, suma]
  ]
]

g[n_] := Module[{s = 0, m = IntegerDigits[n], i},
  For[i = 1, i <= Length[m],
    If[Mod[m[[i]], 2] == 0, s = s + m[[i]]];
    i++
  ];
  s
]
```

Responda:

1. ¿Cuál es el valor de ambos métodos para $n=859745621$?
2. ¿Cuál usa recursividad de cola: `f`, `g` o ninguno?
3. En el experimento mostrado en el examen, usando valores de 1 a 200 con incremento 20, ¿cuál resulta más rápido: `f` o `g`?

---

## Pregunta 4

Elija la notación asintótica que mejor se ajusta a:

$$
\prod_{i=1}^{n-2}\frac{20\cdot 3^{2i}}{11i^5}.
$$

---

## Pregunta 5

Halle la notación asintótica que mejor se ajusta a:

$$
-7n^4+4n^2+5^n+\left(\frac1{11}\right)^{-n}.
$$

---

## Pregunta 6

Elija la notación asintótica que mejor se ajuste a:

$$
\left(5n^3+2n^2-10n-15^{7n-13}-7\ln(8-3n)+26\right)
$$

multiplicado por

$$
\left(-5n^5+n^4+26n^3-18n^2-2n+10\ln(-2(3n+7))-23\right).
$$

---

## Pregunta 7

Sean

$$
f(n)=\frac{2n^7+2n^2}{5n^j+3n^2+1},\qquad g(n)=n^j,
$$

donde $j$ es un entero. Determine el valor de $j$ para el cual

$$
f(n)=\Theta(g(n)).
$$

Si no existe un entero que cumpla, responda `No existe`.

---

## Pregunta 8

Considere el método:

```wl
f[n_] := Module[{p = 8000000, i, j},
  For[i = 1, i <= 2 n - 1,
    For[j = 1, j <= (i - 1)/3, p = p/8000; j++];
    i = i + 2
  ];
  Return[p]
]
```

1. Escriba la sumatoria que representa el tiempo empleado por los ciclos según la respuesta aceptada por el examen.
2. Indique $O(g(n))$ para el método.
