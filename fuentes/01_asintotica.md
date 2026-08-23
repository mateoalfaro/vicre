# Entrenamiento - Notación asintótica

Fuente exclusiva: `Compilación #1 Exámenes Discretas(2).pdf`, sección **II EXAMEN**, páginas 3-6.

## Ejemplo 1 - Sumatoria con término exponencial dominante

**Pregunta 1**

Hallar la notación asintótica que mejor se ajusta a

$$
\sum_{i=2}^{n-1}\left(-13i^3-14^{-7i}+7^{10i}\right).
$$

**Respuesta respaldada por el examen**

$$
\Theta\left(7^{10n}\right).
$$

El propio examen compara la expresión contra una lista de funciones mediante límites. Para $7^{10n}$ el cociente produce un límite finito y no nulo (`1/282475248`), mientras que las alternativas polinomiales mostradas producen infinito.

---

## Ejemplo 2 - Producto y cota superior

**Pregunta 2**

Elegir la notación asintótica que mejor se ajusta a

$$
\prod_{i=2}^{n-1}\frac{2^i}{16i^2}.
$$

Entre las opciones se compara contra

$$
\frac{2^{n^2}}{n!}.
$$

**Respuesta marcada como correcta en el examen**

$$
O\left(\frac{2^{n^2}}{n!}\right).
$$

El procedimiento mostrado es:

```wl
Limit[Product[2^i/(16 i^2), {i, 2, -1 + n}]/(2^n^2/n!), n -> Infinity]
```

Salida mostrada:

```text
0
```

---

## Ejemplo 3 - Igualdad asintótica con parámetro entero

**Pregunta 4**

Sean

$$
f(n)=\frac{15n^4+17n^3+20n^2-4n+16}{6n^4+13n^3+19n^2+17n+16}
$$

y

$$
g(n)=\frac{15n^j+10n^2+3n+19}{8n^4-14n^3+19n^2-9n+11},
$$

donde $j$ es entero y $1\le j\le100$. Hallar $j$ para que

$$
f(n)=\Theta(g(n)).
$$

**Respuesta derivada directamente de las expresiones del examen**

$$
j=4.
$$

La primera función tiene grados 4/4 y por tanto conserva orden constante. Para que la segunda tenga el mismo orden, su numerador debe tener también grado 4 frente al denominador de grado 4; eso ocurre con $j=4$.

El examen muestra además la llamada:

```wl
CompLimit[{
 (16 - 4 n + 20 n^2 + 17 n^3 + 15 n^4)/(16 + 17 n + 19 n^2 + 13 n^3 + 6 n^4),
 (19 + 3 n + 10 n^2 + 15 n^j)/(11 - 9 n + 19 n^2 - 14 n^3 + 8 n^4)
}]
```

---

## Ejemplo 4 - Producto de dos expresiones

**Pregunta 7**

El examen pide la notación asintótica de

$$
\left(
17n^4-18n^3+7n^2+7n-36^{-3n-8}+18^{15n+2}
-\frac{6\ln(2(n+1))}{\ln(4)}-16
\right)
$$

multiplicado por

$$
\left(
-8n^5+16n^4-16n^3+17n^2-13n-2^{20n+7}
-3\ln(9-17n)-\frac{17\ln(18n+6)}{\ln(8)}
\right).
$$

**Respuesta mostrada por el examen**

$$
\Theta\left(-18^{15n}2^{20n}\right).
$$

Se conserva aquí exactamente el signo y la forma usados por el examen.

---

## Ejemplo 5 - Expresión dominada por un polinomio

**Pregunta 8**

Hallar la notación asintótica que mejor se ajusta a

$$
-7n^4+12n^3+2n^2+18n+18^{-11(n-1)}+8^{-2n-13}
+\frac{12\ln(13-11n)}{\ln(3)}+11.
$$

**Respuesta mostrada por el examen**

$$
\Theta(-n^4).
$$

El procedimiento de comparación mostrado usa las opciones `-n^4`, `-18^(-11 n)`, `8^(-2 n)`, `n!` y `-Log[-11 n]` y evalúa límites contra cada una.
