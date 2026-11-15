<p align="center">
  <img src="portada.svg" alt="MazeRunner: BFS y A* buscan la misma meta en el mismo mapa. BFS explora 116 casillas y A* solo 51." width="900">
</p>

# MazeRunner

Proyecto de Matemáticas Discretas. Un mapa de cuadrícula es un grafo: cada casilla es un vértice, cada par de casillas vecinas es una arista y el terreno le pone peso a cada paso. Sobre ese grafo se comparan cinco algoritmos de búsqueda, primero midiéndolos y después jugando contra ellos.

En la animación de arriba los dos buscan la misma meta y encuentran una ruta igual de corta. La diferencia está en cuánto tuvieron que explorar para encontrarla.

## Los cinco algoritmos

| Algoritmo | Estructura de datos | Qué saca primero | Qué garantiza |
|---|---|---|---|
| BFS | Cola (FIFO) | La casilla que lleva más tiempo esperando | La ruta con menos pasos |
| DFS | Pila (LIFO) | La última casilla que entró | Solo que llega, casi siempre dando vueltas |
| Dijkstra | Cola de prioridad | La de menor costo acumulado `g` | La ruta de menor costo |
| Voraz | Cola de prioridad | La que parece más cerca de la meta, `h` | Nada: es rápido pero se deja engañar |
| A* | Cola de prioridad | La de menor `f = g + h` | La ruta de menor costo, explorando menos |

El costo de entrar a una casilla es 1 en llano, 3 en bosque y 5 en agua. Los muros no se pueden cruzar. La heurística `h` es la distancia Manhattan hasta la meta.

## Qué hay en el repositorio

| Archivo | Qué es | Cómo se abre |
|---|---|---|
| `fase1.ipynb` | Investigación: los algoritmos, el mapa como grafo y la comparación con tablas y figuras | Jupyter |
| `visualizador-funciones.html` | Cada función del cuaderno explicada paso a paso, con sus entradas y salidas | Doble clic, en el navegador |
| `fase2_interfaz.py` | Mapa editable con el ratón y tabla en vivo de los cinco algoritmos | `python fase2_interfaz.py` |
| `fase3_juegos.py` | Dos juegos contra la CPU en 2D | `python fase3_juegos.py` |
| `juego3d.html` | La versión completa en 3D, con siete modos | Doble clic, en el navegador |
| `MazeLab/` | Laboratorio de laberintos independiente | Ver su [README](MazeLab/README.md) |

## Cómo ejecutarlo

Hace falta Python 3.10 o posterior.

```bash
pip install pygame-ce==2.5.8 matplotlib==3.10.0 networkx==3.4.2 notebook==7.5.5
```

```bash
jupyter notebook fase1.ipynb
```

```bash
python fase2_interfaz.py
```

```bash
python fase3_juegos.py
```

Los dos archivos `.html` no necesitan instalación: se abren directamente en el navegador. `juego3d.html` descarga la biblioteca three.js al cargar, así que necesita conexión a internet.

## La versión 3D

| Modo | De qué trata |
|---|---|
| Atrapa gemas | Seis tableros idénticos, la misma secuencia de gemas. Gana quien termine primero |
| Captura la bandera | Roba la bandera rival y llévala a tu base tres veces. Tú eliges contra qué algoritmo |
| Maze Runner | Un laberinto gigante para todos, con pasillos que se cierran y se abren cada tres segundos |
| Ver: los tres anteriores | Los mismos modos sin jugador, con cámara libre para mirar competir a los algoritmos |
| Aprender | Cada algoritmo paso a paso: el código que sigue, su cola o su pila en cada momento y por qué gana o pierde en cada mapa |

Para que la competencia sea justa, todos enfrentan el mismo tablero y los mismos cambios de terreno, y cada rival se queda quieto un instante por cada casilla que explora al planear su ruta. Así un algoritmo que revisa medio mapa pierde tiempo frente a uno que va al grano.

Controles: flechas o WASD para moverse, `C` acerca la cámara, `R` reinicia y `Esc` regresa al menú. En los modos de ver, la rueda del ratón acerca y arrastrar gira la cámara.

## Lo que se aprende comparando

Estos números salen del modo Aprender. Los dos mapas miden 13 columnas; el inicio y la meta están en lados opuestos.

**Pantano:** entre el inicio y la meta hay una franja de agua que se puede rodear.

| Algoritmo | Casillas exploradas | Pasos | Costo de la ruta |
|---|---:|---:|---:|
| BFS | 93 | 12 | 32 |
| DFS | 65 | 64 | 124 |
| Dijkstra | 109 | 18 | **18** |
| Voraz | **13** | 12 | 32 |
| A* | 36 | 18 | **18** |

BFS y Voraz cruzan el agua porque son menos pasos, y pagan casi el doble. Dijkstra y A* la rodean. Los dos llegan a la ruta más barata, pero A* explora la tercera parte.

**Trampa:** la meta está justo detrás de una pared, con un lado corto y un lado largo para rodearla.

| Algoritmo | Casillas exploradas | Pasos | Costo de la ruta |
|---|---:|---:|---:|
| BFS | 69 | 9 | **9** |
| DFS | 45 | 39 | 39 |
| Dijkstra | 69 | 9 | **9** |
| Voraz | **25** | 13 | 13 |
| A* | **25** | 9 | **9** |

Voraz corre hacia donde la meta parece más cerca y rodea por el lado largo. A* explora lo mismo, pero como también cuenta lo que ya gastó, sale por el lado corto. Esa es la diferencia entre mirar solo `h` y mirar `g + h`.

Y cuando no existe ruta, ninguno se salva: los cinco tienen que explorar todas las casillas alcanzables antes de poder decirlo.
