# MazeLab — Avance 1: BFS

## Abrir
En esta carpeta ejecutar `python main.py` (o `py main.py`). Requiere Python 3 con Tkinter; no usa paquetes externos. Cerrar la ventana anterior antes de volver a ejecutar.

Este avance incluye un ejemplo fijo con varias rutas, un inicio y una salida, edición de muros, BFS, animación, pausa y avance paso a paso. Se retiraron del avance actual DFS, Dijkstra, arena y generación aleatoria para concentrarnos en una sola búsqueda. La versión anterior se conserva como respaldo de trabajo.

## Orden para estudiar
1. Leer esta guía.
2. Leer `algorithms.py`: vecinos y BFS.
3. Ejecutar y pulsar Paso varias veces para observar la cola.
4. Leer `main.py`: primero avanzar, paso y animar; después la edición y el dibujo.

## Los tres algoritmos
| Algoritmo | Cómo elige el siguiente nodo | Garantía |
|---|---|---|
| BFS | Primero que entró a la cola (FIFO) | Menos aristas; menor costo si todas cuestan lo mismo |
| DFS | Último que entró a la pila (LIFO) | Encuentra un camino alcanzable, sin garantizar el más corto |
| Dijkstra | Menor costo acumulado en cola de prioridad | Menor costo con pesos no negativos; la presentación usa positivos |

BFS no es un personaje que camina de una casilla azul a la siguiente: procesa candidatos de distintas ramas. El orden de exploración y el camino final son cosas diferentes.

## BFS y las diapositivas
Fuente: presentación compartida por el equipo, “Algoritmos de búsqueda de caminos”, Jesús Manuel Mager Hois. Páginas 21–29, especialmente pseudocódigo de la 22.

- Q es `cola`, creada con `deque`.
- Descubierto es `descubierto`, un conjunto. No pertenecer equivale a falso.
- Memoria es `memoria`, un diccionario de antecesores.
- n_s es `inicio`; la prueba de meta es `actual == salida`.
- Γ(n) se obtiene con `vecinos`.
- Agregar al final es `append`; tomar el primero es `popleft`.
- Marcar al encolar evita meter dos veces el mismo vértice.
- Se prueba la meta al extraerla, antes de expandir sus vecinos.
- Si la cola se agota sin encontrar la meta, se informa fracaso.

Para la malla usamos (fila, columna), desde cero. El orden de vecinos es arriba, derecha, abajo, izquierda. La presentación ordena alfabéticamente los vecinos del ejemplo con letras; nuestra regla cumple el mismo papel. Puede haber varias rutas mínimas y el orden decide cuál se devuelve.

## Ejemplo manual del profesor
Las páginas 23–29 muestran este comportamiento:

| Nodo extraído | Cola después de procesarlo |
|---|---|
| A | B, C |
| B | C, D, G |
| C | D, G, E |
| D | G, E, F |
| G (meta) | E, F; se termina |

Memoria[G] = B y Memoria[B] = A. Al reconstruir desde G obtenemos G, B, A; lo invertimos y queda A, B, G. Son 2 aristas, aunque se extrajeron 5 nodos.

## Python para quien conoce C
| Python | Significado aproximado |
|---|---|
| `def bfs(...):` | Definir una función; no declaramos tipos aquí |
| Sangría | Delimita bloques, como las llaves en C |
| `if`, `while`, `for` | Condición y ciclos; `for` recorre elementos |
| `None` | Ausencia de valor; parecido conceptualmente a NULL |
| `(fila, columna)` | Tupla: pareja de coordenadas |
| `[]` | Lista que puede crecer |
| `{inicio}` y `set()` | Conjuntos sin repetidos |
| `{inicio: None}` | Diccionario: relaciona una clave con un valor |
| `in` / `not in` | Comprobar pertenencia |
| `append` | Agregar al final |
| `len(lista)` | Obtener cantidad de elementos |
| `yield estado` | Entregar un estado y suspender la función |
| `next(busqueda)` | Continuar hasta el siguiente yield |
| `self` | Objeto al que pertenecen los datos y métodos |

El generador (`yield`) es una adaptación para animar: no modifica la regla de BFS. Cada clic Paso realiza una extracción y, si no es la meta, descubre y encola sus vecinos. No representa una sola línea del pseudocódigo.

## Cómo explicarlo al equipo
“Representamos cada casilla libre como un vértice y cada movimiento horizontal o vertical como una arista. BFS usa una cola: procesa primero los nodos que descubrió primero. Guarda el antecesor de cada nodo para reconstruir la ruta. Como todos los movimientos cuestan uno, la primera salida extraída tiene una ruta con el menor número de movimientos.”

Pulsa Paso, observa el nodo extraído y la cola amarilla. Luego Ejecutar BFS para continuar. El azul representa nodos extraídos; violeta, la ruta final. Inicio y salida conservan sus colores. La métrica cuenta extraídos e incluye inicio y meta, como la comparación de la página 30. La meta se extrae, pero no se expande.

Para demostrar fracaso, rodea la salida con muros. Reiniciar búsqueda conserva el tablero. Ejemplo restaura el mapa fijo. Editar cancela la búsqueda. Al terminar, Paso conserva el resultado; hay que reiniciar para repetir.

## Etapas siguientes
1. Entender, explicar y presentar BFS.
2. Incorporar DFS respetando la página 12: marca al extraer y permite duplicados pendientes. La versión anterior usaba una variante que evitaba duplicados al insertar; no era una transcripción de ese pseudocódigo.
3. Incorporar Dijkstra y pesos. La página 32 calcula distancias a todos los nodos y comienza con todos en la cola de prioridad. La versión anterior detenía la búsqueda al llegar a la salida y usaba inserciones sucesivas; era una variante orientada a una meta.
4. Recuperar generación aleatoria y comparación cuando el equipo domine lo anterior.
