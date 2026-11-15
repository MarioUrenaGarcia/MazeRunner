"""Fase 2: interfaz gráfica para comparar algoritmos de búsqueda en un mapa editable.

El mapa se pinta con el ratón y los cinco algoritmos se recalculan en cada
cambio, así que la tabla de la derecha siempre muestra cuál encuentra la ruta
más barata y cuál explora menos casillas.

Requiere pygame-ce:   pip install pygame-ce==2.5.8
Ejecutar:             python fase2_interfaz.py
"""

import heapq
import math
from collections import deque
from itertools import permutations

import pygame

# ---------------------------------------------------------------------------
# Algoritmos: los mismos de la fase 1
# ---------------------------------------------------------------------------

COSTOS = {".": 1, "b": 3, "a": 5}


def vecinos(cuadricula, casilla):
    """Genera pares (vecino, peso) con las casillas contiguas que no son muro."""
    f, c = casilla
    for nf, nc in ((f - 1, c), (f, c + 1), (f + 1, c), (f, c - 1)):
        dentro = 0 <= nf < len(cuadricula) and 0 <= nc < len(cuadricula[0])
        if dentro and cuadricula[nf][nc] != "#":
            yield (nf, nc), COSTOS[cuadricula[nf][nc]]


def costo_de(cuadricula, ruta):
    """Suma el costo de entrar a cada casilla de la ruta. Sin ruta es infinito."""
    if ruta is None:
        return math.inf
    return sum(COSTOS[cuadricula[f][c]] for f, c in ruta[1:])


def reconstruir(padres, meta):
    """Arma la ruta siguiendo los padres desde la meta hasta el inicio."""
    ruta = []
    while meta is not None:
        ruta.append(meta)
        meta = padres[meta]
    return ruta[::-1]


def bfs(cuadricula, inicio, meta):
    """Búsqueda en anchura: la frontera es una cola."""
    frontera = deque([inicio])
    padres = {inicio: None}
    explorados = []
    while frontera:
        actual = frontera.popleft()
        explorados.append(actual)
        if actual == meta:
            return reconstruir(padres, meta), explorados
        for vecino, _ in vecinos(cuadricula, actual):
            if vecino not in padres:
                padres[vecino] = actual
                frontera.append(vecino)
    return None, explorados


def dfs(cuadricula, inicio, meta):
    """Búsqueda en profundidad: la frontera es una pila."""
    frontera = [inicio]
    padres = {inicio: None}
    explorados = []
    while frontera:
        actual = frontera.pop()
        if actual in explorados:
            continue
        explorados.append(actual)
        if actual == meta:
            return reconstruir(padres, meta), explorados
        for vecino, _ in vecinos(cuadricula, actual):
            if vecino not in explorados:
                padres[vecino] = actual
                frontera.append(vecino)
    return None, explorados


def dijkstra(cuadricula, inicio, meta):
    """Dijkstra: sale siempre la casilla con menor costo acumulado."""
    frontera = [(0, inicio)]
    costos = {inicio: 0}
    padres = {inicio: None}
    explorados = []
    while frontera:
        costo, actual = heapq.heappop(frontera)
        if costo > costos[actual]:
            continue
        explorados.append(actual)
        if actual == meta:
            return reconstruir(padres, meta), explorados
        for vecino, peso in vecinos(cuadricula, actual):
            nuevo = costo + peso
            if nuevo < costos.get(vecino, math.inf):
                costos[vecino] = nuevo
                padres[vecino] = actual
                heapq.heappush(frontera, (nuevo, vecino))
    return None, explorados


def heuristica(a, b):
    """Distancia Manhattan: nunca sobrestima el costo real."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def voraz(cuadricula, inicio, meta):
    """Búsqueda voraz: sale la casilla que parece más cercana a la meta."""
    frontera = [(heuristica(inicio, meta), inicio)]
    padres = {inicio: None}
    explorados = []
    while frontera:
        _, actual = heapq.heappop(frontera)
        explorados.append(actual)
        if actual == meta:
            return reconstruir(padres, meta), explorados
        for vecino, _ in vecinos(cuadricula, actual):
            if vecino not in padres:
                padres[vecino] = actual
                heapq.heappush(frontera, (heuristica(vecino, meta), vecino))
    return None, explorados


def a_estrella(cuadricula, inicio, meta):
    """A*: la prioridad es el costo acumulado más el costo estimado restante."""
    h = heuristica(inicio, meta)
    frontera = [(h, h, inicio)]
    costos = {inicio: 0}
    padres = {inicio: None}
    explorados = []
    cerrados = set()
    while frontera:
        _, _, actual = heapq.heappop(frontera)
        if actual in cerrados:
            continue
        cerrados.add(actual)
        explorados.append(actual)
        if actual == meta:
            return reconstruir(padres, meta), explorados
        for vecino, peso in vecinos(cuadricula, actual):
            nuevo = costos[actual] + peso
            if nuevo < costos.get(vecino, math.inf):
                costos[vecino] = nuevo
                padres[vecino] = actual
                h = heuristica(vecino, meta)
                heapq.heappush(frontera, (nuevo + h, h, vecino))
    return None, explorados


ALGORITMOS = {"BFS": bfs, "DFS": dfs, "Dijkstra": dijkstra, "Voraz": voraz, "A*": a_estrella}


def mejor_orden(cuadricula, inicio, items, meta):
    """Orden de visita de menor costo, probando todas las permutaciones de los items.

    Devuelve la lista [inicio, items en orden, meta], o None si algún punto
    no se puede alcanzar.
    """
    puntos = [inicio, *items, meta]
    distancia = {
        (a, b): costo_de(cuadricula, dijkstra(cuadricula, a, b)[0])
        for a in puntos for b in puntos if a != b
    }
    ordenes = [[inicio, *p, meta] for p in permutations(items)]
    mejor = min(ordenes, key=lambda o: sum(distancia[par] for par in zip(o, o[1:])))
    if math.isinf(sum(distancia[par] for par in zip(mejor, mejor[1:]))):
        return None
    return mejor


def buscar_por_tramos(algoritmo, cuadricula, orden):
    """Recorre los puntos del orden con un algoritmo, tramo por tramo.

    Devuelve la ruta completa y todas las casillas exploradas.
    """
    ruta = [orden[0]]
    explorados = []
    for a, b in zip(orden, orden[1:]):
        tramo, vistos = algoritmo(cuadricula, a, b)
        explorados += vistos
        ruta += tramo[1:]
    return ruta, explorados


# ---------------------------------------------------------------------------
# Interfaz
# ---------------------------------------------------------------------------

FILAS, COLUMNAS, CELDA = 16, 24, 30
ORIGEN_X, ORIGEN_Y = 20, 64
ANCHO, ALTO = 1180, 700
PANEL_X = ORIGEN_X + COLUMNAS * CELDA + 30
MAX_ITEMS = 6

FONDO = (244, 241, 232)
TINTA = (34, 34, 34)
TENUE = (110, 110, 110)
BORDE = (190, 186, 172)
RESALTE = (255, 233, 184)
COLORES = {".": (239, 233, 208), "b": (106, 165, 106), "a": (111, 168, 220), "#": (43, 43, 43)}
MORADO = (123, 44, 191, 105)
ROJO = (208, 0, 0)
VERDE = (56, 176, 0)
NARANJA = (255, 123, 0)
AMARILLO = (255, 195, 0)

HERRAMIENTAS = [
    ("Llano", "."), ("Bosque", "b"), ("Agua", "a"), ("Muro", "#"),
    ("Inicio", "I"), ("Meta", "M"), ("Item", "*"),
]

EJEMPLO = """
........................
.I....bbbbbb............
......bbbbbb....###.....
......bbbbbb....#.......
..#####bbbbb....#..aaa..
......#.........#..aaa..
......#...aaaaaa#.......
......#...aaaaaa####....
..........aaaaaa......M.
......#...aaaaaa........
......#.................
........................
"""


class Interfaz:
    """Estado del editor y dibujo de la ventana."""

    def __init__(self):
        self.fuente = pygame.font.SysFont("segoeui,arial", 17)
        self.negrita = pygame.font.SysFont("segoeui,arial", 17, bold=True)
        self.titulo = pygame.font.SysFont("segoeui,arial", 24, bold=True)
        self.herramienta = "#"
        self.algoritmo = "A*"
        self.animacion = None
        self.botones = []
        self.cargar(EJEMPLO)

    # -- Mapa ---------------------------------------------------------------

    def limpiar(self):
        """Deja el mapa todo de llano, con el inicio y la meta en los extremos."""
        self.cuadricula = [["."] * COLUMNAS for _ in range(FILAS)]
        self.inicio = (FILAS // 2, 1)
        self.meta = (FILAS // 2, COLUMNAS - 2)
        self.items = []
        self.recalcular()

    def cargar(self, texto):
        """Carga un mapa escrito como texto; lo que no cubra queda como llano."""
        self.limpiar()
        for f, linea in enumerate(texto.strip().splitlines()[:FILAS]):
            for c, simbolo in enumerate(linea.strip()[:COLUMNAS]):
                if simbolo == "I":
                    self.inicio = (f, c)
                elif simbolo == "M":
                    self.meta = (f, c)
                elif simbolo == "*":
                    self.items.append((f, c))
                elif simbolo in COLORES:
                    self.cuadricula[f][c] = simbolo
        self.recalcular()

    def recalcular(self):
        """Vuelve a correr los cinco algoritmos sobre el mapa actual."""
        orden = mejor_orden(self.cuadricula, self.inicio, self.items, self.meta)
        self.resultados = {}
        for nombre, algoritmo in ALGORITMOS.items():
            if orden is None:
                # Sin ruta posible: se muestra lo que explora buscando la meta.
                ruta, explorados = None, algoritmo(self.cuadricula, self.inicio, self.meta)[1]
            else:
                ruta, explorados = buscar_por_tramos(algoritmo, self.cuadricula, orden)
            self.resultados[nombre] = (ruta, explorados, costo_de(self.cuadricula, ruta))
        # Dijkstra siempre da el costo mínimo: es la referencia de optimalidad.
        self.optimo = self.resultados["Dijkstra"][2]
        self.animacion = None

    def casilla_en(self, posicion):
        """Casilla del mapa que está bajo un punto de la ventana, o None."""
        c = (posicion[0] - ORIGEN_X) // CELDA
        f = (posicion[1] - ORIGEN_Y) // CELDA
        if 0 <= f < FILAS and 0 <= c < COLUMNAS:
            return (f, c)
        return None

    def pintar(self, casilla, borrar=False):
        """Aplica la herramienta elegida a una casilla. Devuelve True si algo cambió."""
        f, c = casilla
        herramienta = "." if borrar else self.herramienta
        especial = casilla in (self.inicio, self.meta)
        if herramienta in COLORES:
            if borrar and casilla in self.items:
                self.items.remove(casilla)
                return True
            # El inicio, la meta y los items siempre están sobre llano.
            if especial or casilla in self.items or self.cuadricula[f][c] == herramienta:
                return False
            self.cuadricula[f][c] = herramienta
            return True
        if especial or casilla in self.items:
            return False
        if herramienta == "*" and len(self.items) >= MAX_ITEMS:
            return False
        self.cuadricula[f][c] = "."
        if herramienta == "I":
            self.inicio = casilla
        elif herramienta == "M":
            self.meta = casilla
        else:
            self.items.append(casilla)
        return True

    # -- Eventos ------------------------------------------------------------

    def clic(self, posicion, boton=1):
        """Atiende un clic: primero los botones y después el mapa."""
        if boton == 1:
            for rectangulo, accion in self.botones:
                if rectangulo.collidepoint(posicion):
                    accion()
                    return
        self.arrastrar(posicion, boton)

    def arrastrar(self, posicion, boton=1):
        """Pinta la casilla bajo el ratón. El botón derecho borra."""
        casilla = self.casilla_en(posicion)
        if casilla and self.pintar(casilla, borrar=(boton == 3)):
            self.recalcular()

    def elegir_algoritmo(self, nombre):
        self.algoritmo = nombre
        self.animacion = 0

    def actualizar(self):
        """Avanza la animación de la exploración."""
        if self.animacion is None:
            return
        total = len(self.resultados[self.algoritmo][1])
        # El paso crece con el tamaño para que ninguna animación dure demasiado.
        self.animacion += max(1, total // 150)
        if self.animacion >= total:
            self.animacion = None

    # -- Dibujo -------------------------------------------------------------

    def texto(self, pantalla, cadena, x, y, fuente=None, color=TINTA):
        imagen = (fuente or self.fuente).render(cadena, True, color)
        pantalla.blit(imagen, (x, y))
        return imagen.get_width()

    def boton(self, pantalla, rectangulo, etiqueta, accion, activo=False, muestra=None):
        """Dibuja un botón y lo registra para que responda a los clics."""
        pygame.draw.rect(pantalla, RESALTE if activo else (255, 255, 255), rectangulo, border_radius=6)
        pygame.draw.rect(pantalla, TINTA if activo else BORDE, rectangulo, 2 if activo else 1, border_radius=6)
        x = rectangulo.x + 8
        if muestra:
            pygame.draw.rect(pantalla, muestra, (x, rectangulo.centery - 7, 14, 14))
            pygame.draw.rect(pantalla, TINTA, (x, rectangulo.centery - 7, 14, 14), 1)
            x += 20
        self.texto(pantalla, etiqueta, x, rectangulo.centery - 11, self.negrita if activo else None)
        self.botones.append((rectangulo, accion))

    def centro(self, casilla):
        return (ORIGEN_X + casilla[1] * CELDA + CELDA // 2, ORIGEN_Y + casilla[0] * CELDA + CELDA // 2)

    def dibujar_mapa(self, pantalla):
        ruta, explorados, _ = self.resultados[self.algoritmo]
        if self.animacion is not None:
            explorados, ruta = explorados[: self.animacion], None
        for f in range(FILAS):
            for c in range(COLUMNAS):
                rectangulo = (ORIGEN_X + c * CELDA, ORIGEN_Y + f * CELDA, CELDA, CELDA)
                pygame.draw.rect(pantalla, COLORES[self.cuadricula[f][c]], rectangulo)
        # Las casillas exploradas van en una capa transparente encima del terreno.
        capa = pygame.Surface((COLUMNAS * CELDA, FILAS * CELDA), pygame.SRCALPHA)
        for f, c in set(explorados):
            capa.fill(MORADO, (c * CELDA, f * CELDA, CELDA, CELDA))
        pantalla.blit(capa, (ORIGEN_X, ORIGEN_Y))
        for i in range(COLUMNAS + 1):
            x = ORIGEN_X + i * CELDA
            pygame.draw.line(pantalla, (140, 140, 140), (x, ORIGEN_Y), (x, ORIGEN_Y + FILAS * CELDA))
        for i in range(FILAS + 1):
            y = ORIGEN_Y + i * CELDA
            pygame.draw.line(pantalla, (140, 140, 140), (ORIGEN_X, y), (ORIGEN_X + COLUMNAS * CELDA, y))
        if ruta and len(ruta) > 1:
            pygame.draw.lines(pantalla, ROJO, False, [self.centro(p) for p in ruta], 4)
        for item in self.items:
            x, y = self.centro(item)
            puntos = [(x, y - 9), (x + 9, y), (x, y + 9), (x - 9, y)]
            pygame.draw.polygon(pantalla, AMARILLO, puntos)
            pygame.draw.polygon(pantalla, TINTA, puntos, 1)
        pygame.draw.circle(pantalla, VERDE, self.centro(self.inicio), 9)
        pygame.draw.circle(pantalla, TINTA, self.centro(self.inicio), 9, 1)
        x, y = self.centro(self.meta)
        estrella = [
            (x + r * math.cos(-math.pi / 2 + i * math.pi / 5), y + r * math.sin(-math.pi / 2 + i * math.pi / 5))
            for i, r in zip(range(10), [12, 5] * 5)
        ]
        pygame.draw.polygon(pantalla, NARANJA, estrella)
        pygame.draw.polygon(pantalla, TINTA, estrella, 1)

    def dibujar_tabla(self, pantalla):
        """Una fila por algoritmo: costo, si es óptima y barra de casillas exploradas."""
        x, y = PANEL_X, ORIGEN_Y
        self.texto(pantalla, "Algoritmo", x + 10, y, self.negrita)
        self.texto(pantalla, "Costo", x + 120, y, self.negrita)
        self.texto(pantalla, "Casillas exploradas", x + 190, y, self.negrita)
        mayor = max(len(r[1]) for r in self.resultados.values()) or 1
        for i, nombre in enumerate(ALGORITMOS):
            ruta, explorados, costo = self.resultados[nombre]
            fila = pygame.Rect(x, y + 28 + i * 46, 380, 40)
            self.boton(pantalla, fila, nombre, lambda n=nombre: self.elegir_algoritmo(n), nombre == self.algoritmo)
            if ruta is None:
                self.texto(pantalla, "sin ruta", x + 120, fila.y + 9, color=TENUE)
            else:
                optima = costo == self.optimo
                self.texto(pantalla, str(costo), x + 120, fila.y + 2, self.negrita)
                self.texto(pantalla, "óptima" if optima else "más cara", x + 120, fila.y + 19,
                           pygame.font.SysFont("segoeui,arial", 13), (20, 112, 60) if optima else ROJO)
            largo = int(140 * len(explorados) / mayor)
            pygame.draw.rect(pantalla, (123, 44, 191), (x + 190, fila.y + 11, max(2, largo), 18))
            self.texto(pantalla, str(len(explorados)), x + 196 + largo, fila.y + 9)

    def veredicto(self):
        """Frase que resume cuál algoritmo conviene en el mapa actual."""
        if math.isinf(self.optimo):
            return ["No hay ruta: la meta o algún item quedó encerrado."]
        optimos = [n for n, r in self.resultados.items() if r[2] == self.optimo]
        mejor = min(optimos, key=lambda n: len(self.resultados[n][1]))
        lineas = [f"La ruta más barata cuesta {self.optimo}."]
        lineas.append(f"La encuentran: {', '.join(optimos)}.")
        lineas.append(f"De ellos, {mejor} es el que menos explora ({len(self.resultados[mejor][1])} casillas).")
        return lineas

    def dibujar(self, pantalla):
        self.botones = []
        pantalla.fill(FONDO)
        self.texto(pantalla, "Comparador de algoritmos de búsqueda", ORIGEN_X, 16, self.titulo)
        self.dibujar_mapa(pantalla)

        y = ORIGEN_Y + FILAS * CELDA + 14
        self.texto(pantalla, "Pintar:", ORIGEN_X, y + 8, self.negrita)
        colores = {"I": VERDE, "M": NARANJA, "*": AMARILLO}
        for i, (nombre, simbolo) in enumerate(HERRAMIENTAS):
            rectangulo = pygame.Rect(ORIGEN_X + 62 + i * 94, y, 90, 36)
            self.boton(pantalla, rectangulo, nombre, lambda s=simbolo: setattr(self, "herramienta", s),
                       simbolo == self.herramienta, COLORES.get(simbolo) or colores[simbolo])
        self.texto(pantalla, "Clic izquierdo o arrastrar: pintar.   Clic derecho: borrar.   "
                             f"Costos: llano 1, bosque 3, agua 5.   Máximo {MAX_ITEMS} items.",
                   ORIGEN_X, y + 46, color=TENUE)
        self.texto(pantalla, "Morado: casillas exploradas.   Línea roja: ruta encontrada.   "
                             "Con items, la ruta pasa por todos antes de llegar a la meta.",
                   ORIGEN_X, y + 68, color=TENUE)

        self.dibujar_tabla(pantalla)
        y = ORIGEN_Y + 28 + len(ALGORITMOS) * 46 + 14
        for i, linea in enumerate(self.veredicto()):
            self.texto(pantalla, linea, PANEL_X, y + i * 24, self.negrita if i == 2 else None)
        y += 90
        self.boton(pantalla, pygame.Rect(PANEL_X, y, 380, 40), "Repetir la animación del algoritmo elegido",
                   lambda: self.elegir_algoritmo(self.algoritmo))
        self.boton(pantalla, pygame.Rect(PANEL_X, y + 50, 185, 40), "Mapa de ejemplo", lambda: self.cargar(EJEMPLO))
        self.boton(pantalla, pygame.Rect(PANEL_X + 195, y + 50, 185, 40), "Limpiar mapa", self.limpiar)
        self.texto(pantalla, "Haz clic en un algoritmo para ver cómo explora.", PANEL_X, y + 104, color=TENUE)


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("MazeRunner: comparador de algoritmos")
    interfaz = Interfaz()
    reloj = pygame.time.Clock()
    activo = True
    while activo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                activo = False
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button in (1, 3):
                interfaz.clic(evento.pos, evento.button)
            elif evento.type == pygame.MOUSEMOTION and (evento.buttons[0] or evento.buttons[2]):
                # Arrastrar solo pinta terreno: mover el inicio o poner items pide un clic.
                if interfaz.herramienta in COLORES or evento.buttons[2]:
                    interfaz.arrastrar(evento.pos, 1 if evento.buttons[0] else 3)
        interfaz.actualizar()
        interfaz.dibujar(pantalla)
        pygame.display.flip()
        reloj.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
