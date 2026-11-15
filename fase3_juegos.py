"""Fase 3: dos juegos contra la CPU, donde cada rival se mueve con un algoritmo de búsqueda.

Modos de juego:
1. Atrapa gemas: cada competidor corre en su propio tablero, idéntico a los demás,
   y recoge la misma secuencia de gemas. Gana quien termine primero.
2. Captura la bandera: roba la bandera de la CPU y llévala a la tuya, tres veces.

En los dos modos el terreno cambia durante la partida: los muros se mueven, crecen
árboles o se los traga la tierra, y el agua aparece y desaparece. Esos cambios son
iguales para todos (la misma secuencia en atrapa gemas, en espejo en captura la
bandera), así que la única diferencia entre competidores es el algoritmo.

El terreno frena a todos por igual: llano 1, bosque 3 y agua 5.

Requiere pygame-ce:   pip install pygame-ce==2.5.8
Ejecutar:             python fase3_juegos.py
Controles:            flechas o WASD para moverse, R reinicia, Esc vuelve al menú
"""

import heapq
import math
import random
from collections import deque

import pygame

# ---------------------------------------------------------------------------
# Mapa y algoritmos de búsqueda: los mismos de la fase 1
# ---------------------------------------------------------------------------

COSTOS = {".": 1, "b": 3, "a": 5}


def leer_mapa(texto):
    """Convierte el texto de un mapa en cuadrícula de terreno y puntos especiales.

    Los símbolos de terreno son '.', 'b', 'a', '#' y '_' (vacío: ahí no hay
    tablero). Cualquier otro símbolo marca un punto especial sobre llano.
    Devuelve la cuadrícula y un diccionario símbolo -> lista de posiciones.
    """
    filas = [linea.strip() for linea in texto.strip().splitlines()]
    ancho = max(len(fila) for fila in filas)
    cuadricula, puntos = [], {}
    for f, fila in enumerate(filas):
        terreno = ""
        for c, simbolo in enumerate(fila.ljust(ancho, "#")):
            if simbolo in COSTOS or simbolo in "#_":
                terreno += simbolo
            else:
                puntos.setdefault(simbolo, []).append((f, c))
                terreno += "."
        cuadricula.append(terreno)
    return cuadricula, puntos


def vecinos(cuadricula, casilla):
    """Genera pares (vecino, peso) con las casillas contiguas transitables."""
    f, c = casilla
    for nf, nc in ((f - 1, c), (f, c + 1), (f + 1, c), (f, c - 1)):
        dentro = 0 <= nf < len(cuadricula) and 0 <= nc < len(cuadricula[0])
        if dentro and cuadricula[nf][nc] in COSTOS:
            yield (nf, nc), COSTOS[cuadricula[nf][nc]]


def reconstruir(padres, meta):
    """Arma la ruta siguiendo los padres desde la meta hasta el inicio."""
    ruta = []
    while meta is not None:
        ruta.append(meta)
        meta = padres[meta]
    return ruta[::-1]


def heuristica(a, b):
    """Distancia Manhattan: nunca sobrestima el costo real."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def bfs(cuadricula, inicio, meta):
    """Ruta con menos pasos. No toma en cuenta el costo del terreno."""
    frontera = deque([inicio])
    padres = {inicio: None}
    while frontera:
        actual = frontera.popleft()
        if actual == meta:
            return reconstruir(padres, meta)
        for vecino, _ in vecinos(cuadricula, actual):
            if vecino not in padres:
                padres[vecino] = actual
                frontera.append(vecino)
    return None


def voraz(cuadricula, inicio, meta):
    """Ruta que avanza siempre hacia la casilla que parece más cercana a la meta."""
    frontera = [(heuristica(inicio, meta), inicio)]
    padres = {inicio: None}
    while frontera:
        _, actual = heapq.heappop(frontera)
        if actual == meta:
            return reconstruir(padres, meta)
        for vecino, _ in vecinos(cuadricula, actual):
            if vecino not in padres:
                padres[vecino] = actual
                heapq.heappush(frontera, (heuristica(vecino, meta), vecino))
    return None


def a_estrella(cuadricula, inicio, meta):
    """Ruta de menor costo: combina el costo acumulado con el estimado restante."""
    h = heuristica(inicio, meta)
    frontera = [(h, h, inicio)]
    costos = {inicio: 0}
    padres = {inicio: None}
    cerrados = set()
    while frontera:
        _, _, actual = heapq.heappop(frontera)
        if actual in cerrados:
            continue
        cerrados.add(actual)
        if actual == meta:
            return reconstruir(padres, meta)
        for vecino, peso in vecinos(cuadricula, actual):
            nuevo = costos[actual] + peso
            if nuevo < costos.get(vecino, math.inf):
                costos[vecino] = nuevo
                padres[vecino] = actual
                h = heuristica(vecino, meta)
                heapq.heappush(frontera, (nuevo + h, h, vecino))
    return None


def alcanzables(cuadricula, inicio):
    """Recorrido en anchura completo: todas las casillas conectadas con el inicio.

    Sirve para comprobar que un cambio de terreno no deja a nadie encerrado.
    """
    vistos = {inicio}
    frontera = deque([inicio])
    while frontera:
        for vecino, _ in vecinos(cuadricula, frontera.popleft()):
            if vecino not in vistos:
                vistos.add(vecino)
                frontera.append(vecino)
    return vistos


def con_muros(cuadricula, posiciones):
    """Copia de la cuadrícula con muros en las posiciones dadas."""
    filas = [list(fila) for fila in cuadricula]
    for f, c in posiciones:
        filas[f][c] = "#"
    return ["".join(fila) for fila in filas]


def terreno_al_azar(libres, cuantos, azar):
    """Reparte casillas libres entre muros, bosque y agua.

    Pone 'cuantos' de cada tipo, en manchas de dos casillas contiguas para que
    no queden como puntos sueltos. Devuelve una lista de pares (tipo, posición).
    """
    usadas, piezas = set(), []
    for tipo in "#ba":
        puestos = 0
        for semilla in azar.sample(libres, len(libres)):
            if puestos >= cuantos:
                break
            if semilla in usadas:
                continue
            contiguas = [x for x in libres if distancia(x, semilla) == 1 and x not in usadas]
            mancha = [semilla] + azar.sample(contiguas, min(1, len(contiguas)))
            for posicion in mancha[: cuantos - puestos]:
                usadas.add(posicion)
                piezas.append((tipo, posicion))
                puestos += 1
    return piezas


# Cada rival: nombre, algoritmo y color.
RIVALES = [
    ("BFS", bfs, (236, 140, 40)),
    ("Voraz", voraz, (170, 90, 220)),
    ("A*", a_estrella, (60, 60, 66)),
]

# ---------------------------------------------------------------------------
# Piezas comunes a los dos modos
# ---------------------------------------------------------------------------

ANCHO, ALTO = 1100, 720
ANCHO_TABLERO = 880                # el resto de la ventana es el panel de carrera
PANEL_X = 905
VELOCIDAD_JUGADOR = 5.0            # casillas de llano por segundo
VELOCIDAD_RIVAL = 4.4
CONTACTO = 0.6                     # distancia, en casillas, a la que dos personajes chocan
CUENTA_ATRAS = 3.0                 # segundos antes de la salida

CIELO = (28, 34, 48)
BLANCO = (245, 245, 245)
NEGRO = (20, 20, 22)
GRIS = (190, 196, 210)
ORO = (255, 210, 30)
ROJO = (215, 40, 47)
CARBON = (60, 60, 66)
SUELO = {".": ((134, 204, 88), (124, 194, 80)), "b": ((92, 164, 74), (86, 156, 70)), "a": ((70, 150, 222), (64, 142, 214))}
TIERRA = (104, 74, 50)
MURO_TOPE, MURO_FRENTE = (176, 178, 190), (104, 106, 122)

# Dirección en el mapa (fila, columna) que corresponde a cada tecla.
TECLAS = {
    pygame.K_UP: (-1, 0), pygame.K_w: (-1, 0),
    pygame.K_RIGHT: (0, 1), pygame.K_d: (0, 1),
    pygame.K_DOWN: (1, 0), pygame.K_s: (1, 0),
    pygame.K_LEFT: (0, -1), pygame.K_a: (0, -1),
}

_fuentes = {}


def fuente(tam, carrera=False):
    """Devuelve la fuente pedida. Cada una se crea una sola vez y se reutiliza."""
    if (tam, carrera) not in _fuentes:
        if carrera:
            # Letra de carreras: gruesa e inclinada.
            _fuentes[(tam, carrera)] = pygame.font.SysFont("arialblack,impact,arial", tam, bold=True, italic=True)
        else:
            _fuentes[(tam, carrera)] = pygame.font.SysFont("segoeui,arial", tam)
    return _fuentes[(tam, carrera)]


def escribir(pantalla, cadena, x, y, tam=18, color=BLANCO):
    """Texto normal, para las instrucciones."""
    pantalla.blit(fuente(tam).render(cadena, True, color), (x, y))


def letrero(pantalla, cadena, x, y, tam, color=BLANCO, ancla="izquierda"):
    """Texto de carreras con contorno negro. El ancla dice qué punto del texto queda en x."""
    letra = fuente(tam, carrera=True)
    imagen = letra.render(cadena, True, color)
    if ancla == "centro":
        x -= imagen.get_width() // 2
    elif ancla == "derecha":
        x -= imagen.get_width()
    # El contorno se logra dibujando el mismo texto en negro, corrido hacia todos lados.
    borde = letra.render(cadena, True, NEGRO)
    grosor = 2 if tam < 30 else 3 if tam < 70 else 5
    for dx in range(-grosor, grosor + 1):
        for dy in range(-grosor, grosor + 1):
            if dx or dy:
                pantalla.blit(borde, (x + dx, y + dy))
    pantalla.blit(imagen, (x, y))


def distancia(a, b):
    """Distancia Manhattan entre dos posiciones, que pueden tener decimales."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Personaje:
    """Cualquiera que camina por el mapa: el jugador o un rival."""

    def __init__(self, posicion, color, nombre, algoritmo, velocidad):
        self.posicion = posicion
        self.base = posicion
        self.color = color
        self.nombre = nombre
        self.algoritmo = algoritmo
        self.velocidad = velocidad
        self.camino = []      # casillas que le faltan por recorrer
        self.avance = 0.0     # fracción recorrida hacia la siguiente casilla
        self.puntos = 0

    def visual(self):
        """Posición interpolada mientras camina entre dos casillas."""
        f, c = self.posicion
        if self.camino:
            df, dc = self.camino[0][0] - f, self.camino[0][1] - c
            return (f + df * self.avance, c + dc * self.avance)
        return (f, c)

    def ir_a(self, cuadricula, objetivo):
        """Calcula con su algoritmo la ruta hacia una casilla."""
        # Si va a medio paso, primero termina de llegar a la casilla siguiente.
        origen = self.camino[0] if self.camino and self.avance > 0 else self.posicion
        ruta = self.algoritmo(cuadricula, origen, objetivo)
        resto = ruta[1:] if ruta else []
        self.camino = ([origen] if origen != self.posicion else []) + resto

    def avanzar(self, dt, cuadricula):
        """Camina por su ruta. Devuelve True cuando acaba de llegar a una casilla."""
        if not self.camino:
            return False
        f, c = self.camino[0]
        # El terreno caro se cruza más despacio.
        self.avance += dt * self.velocidad / COSTOS[cuadricula[f][c]]
        if self.avance < 1:
            return False
        self.avance = 0.0
        self.posicion = self.camino.pop(0)
        return True

    def regresar(self):
        """Lo devuelve de golpe a su casilla de salida."""
        self.posicion, self.camino, self.avance = self.base, [], 0.0


class Modo:
    """Base de los modos: mapa, terreno cambiante, dibujo de la escena y fin de partida."""

    titulo = ""
    resumen = ""
    ayuda = ""
    semilla = None      # con un número fijo la partida sale siempre igual; sirve para probar

    def __init__(self):
        self.tiempo = 0.0
        self.direccion = None     # dirección de la tecla que se mantiene pulsada
        self.cargar()

    def usar_mapa(self, texto):
        """Prepara un tablero vacío y reinicia el estado de la partida."""
        self.base, self.puntos = leer_mapa(texto)      # tablero vacío: solo llano
        self.cuadricula = list(self.base)              # tablero con el terreno del momento
        self.filas, self.columnas = len(self.base), len(self.base[0])
        self.azar = random.Random(self.semilla)
        # Las casillas se achican lo necesario para que el tablero quepa junto al panel.
        self.ancho_casilla = min(52, ANCHO_TABLERO // self.columnas)
        self.alto_casilla = round(self.ancho_casilla * 0.73)      # la cámara inclinada aplasta el suelo
        self.escala = self.ancho_casilla / 52
        self.origen_x = 12 + (ANCHO_TABLERO - self.columnas * self.ancho_casilla) // 2
        self.origen_y = 40 + (ALTO - 100 - self.filas * self.alto_casilla) // 2
        self.estado = "jugando"
        self.final = ("", "")
        self.espera = CUENTA_ATRAS      # cuenta regresiva: nadie se mueve hasta que llega a cero
        self.salida = None              # momento en que arrancó la partida

    def poner_terreno(self, piezas):
        """Coloca muros, árboles y agua sobre el tablero vacío. piezas: lista de (tipo, posición)."""
        filas = [list(fila) for fila in self.base]
        for tipo, (f, c) in piezas:
            filas[f][c] = tipo
        self.cuadricula = ["".join(fila) for fila in filas]

    def terminar(self, ganado, titulo, detalle=""):
        self.estado = "ganado" if ganado else "perdido"
        self.final = (titulo, detalle)

    def tecla(self, tecla):
        if tecla == pygame.K_r or (tecla in (pygame.K_SPACE, pygame.K_RETURN) and self.estado != "jugando"):
            self.cargar()

    def transitable(self, casilla):
        f, c = casilla
        return 0 <= f < self.filas and 0 <= c < self.columnas and self.cuadricula[f][c] in COSTOS

    def mover_jugador(self, jugador, dt):
        """Da un paso en la dirección pulsada. Devuelve True al llegar a una casilla."""
        if not jugador.camino and self.direccion:
            casilla = (jugador.posicion[0] + self.direccion[0], jugador.posicion[1] + self.direccion[1])
            if self.transitable(casilla):
                jugador.camino = [casilla]
        return jugador.avanzar(dt, self.cuadricula)

    # -- Dibujo -------------------------------------------------------------

    def px(self, valor):
        """Convierte una medida pensada para casillas grandes al tamaño real de las casillas."""
        return round(valor * self.escala)

    def a_pantalla(self, f, c):
        """Esquina superior izquierda de una casilla en la pantalla."""
        return (self.origen_x + c * self.ancho_casilla, self.origen_y + f * self.alto_casilla)

    def centro(self, f, c):
        x, y = self.a_pantalla(f, c)
        return (x + self.ancho_casilla / 2, y + self.alto_casilla / 2)

    def dibujar_suelo(self, pantalla):
        ancho, alto = self.ancho_casilla, self.alto_casilla
        for f in range(self.filas):
            for c in range(self.columnas):
                terreno = self.cuadricula[f][c]
                if terreno == "_":
                    continue      # vacío: ahí no hay tablero
                x, y = self.a_pantalla(f, c)
                # Borde frontal: se ve donde abajo ya no hay tablero.
                if f == self.filas - 1 or self.cuadricula[f + 1][c] == "_":
                    pygame.draw.rect(pantalla, TIERRA, (x, y + alto, ancho, self.px(12)))
                if terreno == "#":
                    continue
                pygame.draw.rect(pantalla, SUELO[terreno][(f + c) % 2], (x, y, ancho, alto))
                if terreno == "a":
                    # El agua está hundida: donde empieza se ve la orilla de tierra.
                    if f == 0 or self.cuadricula[f - 1][c] != "a":
                        pygame.draw.rect(pantalla, TIERRA, (x, y, ancho, self.px(6)))
                    onda = math.sin(self.tiempo * 2 + f + c) * self.px(5)
                    linea = y + alto * 0.62
                    pygame.draw.line(pantalla, (170, 215, 250), (x + ancho * 0.28 + onda, linea), (x + ancho * 0.6 + onda, linea), 2)

    def dibujar_bloque(self, pantalla, f, c):
        """Muro con cara superior y cara frontal, como se ve con la cámara inclinada."""
        x, y = self.a_pantalla(f, c)
        altura = self.px(12)
        pygame.draw.rect(pantalla, MURO_TOPE, (x, y - altura, self.ancho_casilla, self.alto_casilla))
        pygame.draw.rect(pantalla, MURO_FRENTE, (x, y - altura + self.alto_casilla, self.ancho_casilla, altura))

    def dibujar_arbol(self, pantalla, f, c):
        x, y = self.centro(f, c)
        p = self.px
        pygame.draw.rect(pantalla, (104, 72, 44), (x - p(3), y - p(2), p(6), p(14)))
        pygame.draw.circle(pantalla, (38, 110, 52), (x, y - p(10)), p(14))
        pygame.draw.circle(pantalla, (58, 138, 66), (x - p(3), y - p(14)), p(8))

    def dibujar_gema(self, pantalla, f, c):
        x, base = self.centro(f, c)
        p = self.px
        y = base - p(6) + math.sin(self.tiempo * 3 + f) * p(3)
        pygame.draw.ellipse(pantalla, (60, 110, 50), (x - p(8), base + p(8), p(16), p(6)))
        puntos = [(x, y - p(11)), (x + p(8), y), (x, y + p(11)), (x - p(8), y)]
        pygame.draw.polygon(pantalla, (255, 205, 40), puntos)
        pygame.draw.polygon(pantalla, (255, 245, 180), [(x, y - p(11)), (x + p(8), y), (x, y)])
        pygame.draw.polygon(pantalla, (120, 80, 0), puntos, 1)

    def dibujar_bandera(self, pantalla, f, c, color, marco=True):
        """Bandera clavada en una casilla. Con marco se resalta la casilla."""
        x, y = self.a_pantalla(f, c)
        cx, cy = self.centro(f, c)
        p = self.px
        if marco:
            pygame.draw.rect(pantalla, color, (x + 2, y + 2, self.ancho_casilla - 4, self.alto_casilla - 4), 3)
        pygame.draw.line(pantalla, NEGRO, (cx, cy + p(8)), (cx, cy - p(30)), 3)
        pygame.draw.polygon(pantalla, color, [(cx + 1, cy - p(30)), (cx + p(20), cy - p(23)), (cx + 1, cy - p(16))])
        pygame.draw.polygon(pantalla, NEGRO, [(cx + 1, cy - p(30)), (cx + p(20), cy - p(23)), (cx + 1, cy - p(16))], 1)

    def dibujar_personaje(self, pantalla, personaje):
        f, c = personaje.visual()
        x, y = self.centro(f, c)
        p = self.px
        borde = tuple(v // 2 for v in personaje.color)
        pygame.draw.ellipse(pantalla, (40, 70, 40), (x - p(12), y + p(5), p(24), p(10)))
        pygame.draw.ellipse(pantalla, personaje.color, (x - p(9), y - p(16), p(18), p(26)))
        pygame.draw.ellipse(pantalla, borde, (x - p(9), y - p(16), p(18), p(26)), 2)
        pygame.draw.circle(pantalla, (245, 205, 160), (x, y - p(21)), p(7))
        pygame.draw.circle(pantalla, (90, 60, 30), (x, y - p(21)), p(7), 1)
        imagen = fuente(max(11, p(14)), carrera=True).render(personaje.nombre, True, BLANCO)
        fondo = imagen.get_rect(center=(x, y - p(40))).inflate(8, 2)
        pygame.draw.rect(pantalla, borde, fondo, border_radius=4)
        pantalla.blit(imagen, imagen.get_rect(center=(x, y - p(40))))

    def dibujar_objetos(self, pantalla, extras=()):
        """Dibuja muros, árboles y los objetos del modo, ordenados por profundidad.

        extras es una lista de ternas (fila, prioridad, función que dibuja).
        """
        objetos = list(extras)
        for f in range(self.filas):
            for c in range(self.columnas):
                terreno = self.cuadricula[f][c]
                if terreno == "#":
                    objetos.append((f, 0, lambda f=f, c=c: self.dibujar_bloque(pantalla, f, c)))
                elif terreno == "b":
                    objetos.append((f, 1, lambda f=f, c=c: self.dibujar_arbol(pantalla, f, c)))
        # Las filas de abajo están más cerca de la cámara: se dibujan al final
        # para que un muro tape lo que tiene detrás.
        for _, _, dibujar in sorted(objetos, key=lambda o: (o[0], o[1])):
            dibujar()

    def dibujar_rutas(self, pantalla, personajes):
        """Marca con puntos la ruta que planea cada rival."""
        for personaje in personajes:
            for f, c in personaje.camino:
                pygame.draw.circle(pantalla, personaje.color, self.centro(f, c), max(2, self.px(4)))

    def dibujar_cuenta(self, pantalla):
        """Cuenta regresiva de salida, encima del tablero."""
        x = self.origen_x + self.columnas * self.ancho_casilla // 2
        if self.espera > 0:
            letrero(pantalla, str(math.ceil(self.espera)), x, ALTO // 2 - 110, 150, ORO, "centro")
        elif self.salida is not None and self.tiempo - self.salida < 0.8:
            letrero(pantalla, "¡YA!", x, ALTO // 2 - 110, 150, ORO, "centro")

    def dibujar_cierre(self, pantalla):
        if self.estado == "jugando":
            return
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((10, 14, 24, 150))
        pantalla.blit(velo, (0, 0))
        letrero(pantalla, self.final[0], ANCHO // 2, 220, 96, ORO, "centro")
        letrero(pantalla, self.final[1], ANCHO // 2, 350, 26, BLANCO, "centro")
        letrero(pantalla, "ESPACIO: OTRA VEZ     ESC: MENÚ", ANCHO // 2, 400, 22, BLANCO, "centro")


# ---------------------------------------------------------------------------
# Modo 1: atrapa gemas
# ---------------------------------------------------------------------------

# Tablero de un competidor: empieza vacío. En la partida hay cuatro copias idénticas.
MAPA_GEMAS = """
I..........
...........
...........
...........
...........
...........
...........
...........
...........
"""
PIEZAS_POR_TIPO = 6      # muros, árboles y charcos que hay en cada tablero


class AtrapaGemas(Modo):
    """Carrera en tableros separados e idénticos.

    Cada competidor recoge la misma secuencia de gemas en su propio tablero. Cada
    vez que alguien toma una gema, el terreno de su tablero cambia. Esa secuencia
    de terrenos también es común, así que todos enfrentan exactamente lo mismo y
    lo único que cambia es el algoritmo.
    """

    titulo = "ATRAPA GEMAS"
    resumen = "Mismo tablero, mismas gemas y mismo terreno cambiante para todos. Termina antes que BFS, voraz y A*."
    ayuda = "Flechas o WASD: moverte.   Tu tablero es el de arriba a la izquierda.   R: reiniciar.   Esc: menú."
    total = 8

    def cargar(self):
        base = MAPA_GEMAS.strip().splitlines()
        ancho = len(base[0])
        # Cuatro copias en dos filas, separadas por una franja vacía.
        doble = [fila + "_" + fila for fila in base]
        self.usar_mapa("\n".join(doble + ["_" * (2 * ancho + 1)] + doble))
        # Todo se sortea una vez, en coordenadas del tablero base, y vale para los cuatro.
        local, puntos = leer_mapa(MAPA_GEMAS)
        inicio = puntos["I"][0]
        llano = [(f, c) for f in range(len(local)) for c in range(ancho) if (f, c) != inicio]
        self.secuencia = []
        previo = inicio
        while len(self.secuencia) < self.total:
            # Cada gema aparece lejos de la anterior para que haya que recorrer el tablero.
            previo = self.azar.choice([x for x in llano if distancia(x, previo) >= 5])
            self.secuencia.append(previo)
        # etapas[k]: cómo está el terreno mientras se busca la gema k.
        self.etapas = [self.sortear_etapa(local, llano, inicio, k) for k in range(self.total)]
        quienes = [("Tú", a_estrella, ROJO, VELOCIDAD_JUGADOR)] + [(*rival, VELOCIDAD_RIVAL) for rival in RIVALES]
        self.todos = []
        for posicion, (nombre, algoritmo, color, velocidad) in zip(self.puntos["I"], quienes):
            personaje = Personaje(posicion, color, nombre, algoritmo, velocidad)
            # El desvío traslada las coordenadas del tablero base al tablero de este competidor.
            personaje.desvio = (posicion[0] - inicio[0], posicion[1] - inicio[1])
            personaje.tiempo_final = None
            self.todos.append(personaje)
        self.jugador, self.rivales = self.todos[0], self.todos[1:]
        self.reloj = 0.0
        self.llegadas = []
        self.colocar_terreno()
        for rival in self.rivales:
            rival.ir_a(self.cuadricula, self.gema_de(rival))

    def sortear_etapa(self, local, llano, inicio, k):
        """Terreno de la etapa k: no tapa la gema ni encierra al competidor."""
        origen = self.secuencia[k - 1] if k else inicio
        gema = self.secuencia[k]
        # Nada puede caer sobre la gema ni junto al competidor, que acaba de tomar la anterior.
        libres = [x for x in llano if distancia(x, origen) > 1 and x != gema]
        for _ in range(60):
            piezas = terreno_al_azar(libres, PIEZAS_POR_TIPO, self.azar)
            muros = [posicion for tipo, posicion in piezas if tipo == "#"]
            # Solo vale un terreno cuyos muros dejen camino hasta la gema.
            if a_estrella(con_muros(local, muros), origen, gema):
                return piezas
        return []

    def gema_de(self, personaje):
        """Gema que le toca ahora a un competidor, ya en su propio tablero. None si terminó."""
        if personaje.puntos >= self.total:
            return None
        f, c = self.secuencia[personaje.puntos]
        return (f + personaje.desvio[0], c + personaje.desvio[1])

    def colocar_terreno(self):
        """Cada tablero muestra el terreno de la etapa en la que va su competidor."""
        piezas = []
        for personaje in self.todos:
            df, dc = personaje.desvio
            for tipo, (f, c) in self.etapas[min(personaje.puntos, self.total - 1)]:
                piezas.append((tipo, (f + df, c + dc)))
        self.poner_terreno(piezas)

    def actualizar(self, dt):
        self.reloj += dt
        self.mover_jugador(self.jugador, dt)
        for rival in self.rivales:
            rival.avanzar(dt, self.cuadricula)
        for personaje in self.todos:
            gema = self.gema_de(personaje)
            if gema is None or distancia(personaje.visual(), gema) >= 0.5:
                continue
            personaje.puntos += 1
            if personaje.puntos == self.total:
                personaje.tiempo_final = self.reloj
                self.llegadas.append(personaje)
                if personaje is self.jugador:
                    self.cerrar()
                    return
                continue
            # Al tomar la gema cambia el terreno de su tablero y hay que volver a planear la ruta.
            self.colocar_terreno()
            if personaje is not self.jugador:
                personaje.ir_a(self.cuadricula, self.gema_de(personaje))

    def orden(self):
        """Clasificación: quien ya terminó, luego quien lleva más gemas, luego quien está más cerca de la siguiente."""
        def clave(personaje):
            gema = self.gema_de(personaje)
            falta = distancia(personaje.visual(), gema) if gema else 0
            terminado = personaje.tiempo_final if personaje.tiempo_final is not None else math.inf
            return (terminado, -personaje.puntos, falta)
        return sorted(self.todos, key=clave)

    def cerrar(self):
        lugar = self.llegadas.index(self.jugador) + 1
        tabla = "     ".join(f"{i + 1}. {p.nombre} {p.tiempo_final:.1f} s" for i, p in enumerate(self.llegadas))
        self.terminar(lugar == 1, "¡GANASTE!" if lugar == 1 else f"LUGAR {lugar}", tabla)

    def dibujar_panel(self, pantalla):
        """Panel de carrera: contador de gemas, tiempo, clasificación y lugar del jugador."""
        orden = self.orden()
        derecha = ANCHO - 18
        letrero(pantalla, "GEMAS", derecha, 14, 22, ORO, "derecha")
        letrero(pantalla, f"{self.jugador.puntos}/{self.total}", derecha, 40, 62, BLANCO, "derecha")
        minutos, segundos = divmod(self.reloj, 60)
        letrero(pantalla, f"{int(minutos)}:{segundos:04.1f}", derecha, 124, 26, BLANCO, "derecha")
        for i, personaje in enumerate(orden):
            y = 190 + i * 50
            letrero(pantalla, str(i + 1), PANEL_X, y, 30, ORO)
            pygame.draw.circle(pantalla, BLANCO, (PANEL_X + 48, y + 22), 15)
            pygame.draw.circle(pantalla, NEGRO, (PANEL_X + 48, y + 22), 13)
            pygame.draw.circle(pantalla, personaje.color, (PANEL_X + 48, y + 22), 10)
            letrero(pantalla, personaje.nombre.upper(), PANEL_X + 70, y - 2, 18, ORO if personaje is self.jugador else BLANCO)
            if personaje.tiempo_final is not None:
                letrero(pantalla, f"{personaje.tiempo_final:.1f} s", PANEL_X + 70, y + 20, 15, (124, 255, 138))
            else:
                letrero(pantalla, f"{personaje.puntos}/{self.total}", PANEL_X + 70, y + 20, 15, ORO)
        lugar = orden.index(self.jugador) + 1
        letrero(pantalla, f"{lugar}º", PANEL_X + 10, 470, 120, ORO if lugar == 1 else BLANCO)

    def dibujar(self, pantalla):
        self.dibujar_suelo(pantalla)
        self.dibujar_rutas(pantalla, self.rivales)
        extras = []
        for personaje in self.todos:
            gema = self.gema_de(personaje)
            if gema:
                extras.append((gema[0], 2, lambda g=gema: self.dibujar_gema(pantalla, *g)))
            extras.append((personaje.visual()[0], 3, lambda p=personaje: self.dibujar_personaje(pantalla, p)))
        self.dibujar_objetos(pantalla, extras)
        self.dibujar_panel(pantalla)


# ---------------------------------------------------------------------------
# Modo 2: captura la bandera
# ---------------------------------------------------------------------------

# I y 3 son las salidas del jugador y de la CPU. El tablero empieza vacío.
MAPA_BANDERA = """
.................
.................
.................
.................
.................
I...............3
.................
.................
.................
.................
.................
"""
PIEZAS_POR_LADO = 5      # muros, árboles y charcos en cada mitad del mapa


class Bandera(Modo):
    """Robar la bandera rival y llevarla a la propia, tres veces.

    Las banderas cambian de lugar tras cada punto, y el terreno cambia cada vez
    que alguien toma una bandera, anota o choca. Todo se coloca en espejo, así
    que los dos lados enfrentan lo mismo.
    """

    titulo = "CAPTURA LA BANDERA"
    resumen = "Roba la bandera de la CPU y llévala a la tuya. Banderas y terreno cambian, siempre en espejo."
    ayuda = "Flechas o WASD: moverte.   Si hay choque con una bandera en juego, los dos vuelven a su salida.   R: reiniciar.   Esc: menú."
    meta = 3

    def cargar(self):
        self.usar_mapa(MAPA_BANDERA)
        self.jugador = Personaje(self.puntos["I"][0], ROJO, "Tú", a_estrella, VELOCIDAD_JUGADOR)
        self.cpu = Personaje(self.puntos["3"][0], CARBON, "A*", a_estrella, 4.3)
        self.jugador.lleva = self.cpu.lleva = False
        self.mitad = self.columnas // 2
        # Se sortea una sola secuencia de posiciones, en la mitad del jugador. La bandera
        # de la CPU usa siempre la casilla espejo.
        candidatas = [
            (f, c) for f in range(self.filas) for c in range(self.mitad - 1)
            if distancia((f, c), self.jugador.base) >= 3
        ]
        self.secuencia = self.azar.sample(candidatas, 2 * self.meta - 1)
        self.ronda = 0
        self.colocar_banderas()
        self.cambiar_mapa()

    def espejo(self, casilla):
        return (casilla[0], self.columnas - 1 - casilla[1])

    def colocar_banderas(self):
        posicion = self.secuencia[self.ronda % len(self.secuencia)]
        self.jugador.bandera = posicion
        self.cpu.bandera = self.espejo(posicion)

    def cambiar_mapa(self):
        """Sortea terreno nuevo en la mitad izquierda y lo repite en espejo en la derecha."""
        claves = [self.jugador.base, self.cpu.base, self.jugador.bandera, self.cpu.bandera]
        cerca = []
        for personaje in (self.jugador, self.cpu):
            cerca.append(personaje.posicion)
            if personaje.camino:
                cerca.append(personaje.camino[0])

        def prohibida(casilla):
            # Nada puede caer sobre una base o una bandera, ni encima o al lado de un personaje.
            return casilla in claves or any(distancia(k, casilla) <= 1 for k in cerca)

        libres = [
            (f, c) for f in range(self.filas) for c in range(self.mitad)
            if not prohibida((f, c)) and not prohibida(self.espejo((f, c)))
        ]
        for _ in range(40):
            izquierda = terreno_al_azar(libres, PIEZAS_POR_LADO, self.azar)
            piezas = izquierda + [(tipo, self.espejo(posicion)) for tipo, posicion in izquierda]
            # Se acepta solo si bases, banderas y personajes siguen conectados entre sí.
            muros = [posicion for tipo, posicion in piezas if tipo == "#"]
            zona = alcanzables(con_muros(self.base, muros), self.jugador.base)
            if all(k in zona for k in claves + cerca):
                self.poner_terreno(piezas)
                return

    def objetivo_cpu(self):
        """Decide a dónde va la CPU según quién lleva qué bandera."""
        if self.cpu.lleva:
            return self.cpu.bandera              # ya la tiene: a casa
        if self.jugador.lleva:
            return self.jugador.posicion         # le robaron: a perseguir
        return self.jugador.bandera              # nada en juego: a robar

    def revisar(self, personaje, rival):
        """Toma la bandera rival al pisarla y anota al llegar con ella a la propia."""
        if personaje.posicion == rival.bandera and not personaje.lleva:
            personaje.lleva = True
            self.cambiar_mapa()
        elif personaje.posicion == personaje.bandera and personaje.lleva:
            personaje.puntos += 1
            # Tras cada punto las dos banderas saltan a la siguiente posición. Quien cargaba una la pierde.
            personaje.lleva = rival.lleva = False
            self.ronda += 1
            self.colocar_banderas()
            self.cambiar_mapa()

    def choque(self):
        """Al chocar, los dos vuelven a su salida, sueltan lo que cargaban y el mapa cambia."""
        for personaje in (self.jugador, self.cpu):
            personaje.regresar()
            personaje.lleva = False
        self.cambiar_mapa()

    def actualizar(self, dt):
        jugador, cpu = self.jugador, self.cpu
        self.mover_jugador(jugador, dt)
        cpu.avanzar(dt, self.cuadricula)
        # La CPU vuelve a planear en cada casilla: el objetivo y el terreno cambian.
        if not cpu.camino or cpu.avance == 0:
            cpu.ir_a(self.cuadricula, self.objetivo_cpu())
        if not jugador.camino or jugador.avance == 0:
            self.revisar(jugador, cpu)
        if not cpu.camino or cpu.avance == 0:
            self.revisar(cpu, jugador)
        # El choque solo cuenta cuando alguien lleva una bandera: así se defiende la propia.
        if distancia(jugador.visual(), cpu.visual()) < CONTACTO and (jugador.lleva or cpu.lleva):
            self.choque()
        if jugador.puntos == self.meta:
            self.terminar(True, "¡GANASTE!", f"{jugador.puntos} A {cpu.puntos}")
        elif cpu.puntos == self.meta:
            self.terminar(False, "GANÓ LA CPU", f"{cpu.puntos} A {jugador.puntos}")

    def dibujar_panel(self, pantalla):
        """Marcador del duelo y aviso de quién lleva bandera."""
        letrero(pantalla, f"PRIMERO A {self.meta}", PANEL_X, 22, 19, ORO)
        for i, (nombre, personaje) in enumerate((("TÚ", self.jugador), ("CPU A*", self.cpu))):
            caja = pygame.Rect(PANEL_X, 70 + i * 130, 180, 110)
            pygame.draw.rect(pantalla, NEGRO, caja.move(5, 5), border_radius=14)
            pygame.draw.rect(pantalla, personaje.color, caja, border_radius=14)
            pygame.draw.rect(pantalla, NEGRO, caja, 5, border_radius=14)
            letrero(pantalla, nombre, caja.x + 14, caja.y + 10, 20)
            letrero(pantalla, str(personaje.puntos), caja.right - 16, caja.y + 28, 64, BLANCO, "derecha")
        if self.jugador.lleva and self.cpu.lleva:
            aviso = ["¡LOS DOS", "LLEVAN", "BANDERA!"]
        elif self.jugador.lleva:
            aviso = ["¡LLEVAS", "SU BANDERA!"]
        elif self.cpu.lleva:
            aviso = ["¡TE ROBARON", "LA BANDERA!"]
        else:
            aviso = []
        for i, linea in enumerate(aviso):
            letrero(pantalla, linea, PANEL_X, 350 + i * 28, 17, ORO)

    def dibujar(self, pantalla):
        self.dibujar_suelo(pantalla)
        # Línea que separa las dos mitades del mapa.
        x = self.origen_x + self.mitad * self.ancho_casilla + self.ancho_casilla // 2
        pygame.draw.line(pantalla, BLANCO, (x, self.origen_y), (x, self.origen_y + self.filas * self.alto_casilla), 2)
        self.dibujar_rutas(pantalla, [self.cpu])
        extras = []
        for dueno, ladron in ((self.jugador, self.cpu), (self.cpu, self.jugador)):
            f, c = dueno.bandera
            if ladron.lleva:
                # La casilla queda marcada y la bandera se dibuja sobre quien la carga.
                x, y = self.a_pantalla(f, c)
                pygame.draw.rect(pantalla, dueno.color, (x + 2, y + 2, self.ancho_casilla - 4, self.alto_casilla - 4), 3)
                lf, lc = ladron.visual()
                extras.append((lf, 6, lambda lf=lf, lc=lc, d=dueno: self.dibujar_bandera(pantalla, lf, lc, d.color, marco=False)))
            else:
                extras.append((f, 1, lambda f=f, c=c, d=dueno: self.dibujar_bandera(pantalla, f, c, d.color)))
        for personaje in (self.cpu, self.jugador):
            extras.append((personaje.visual()[0], 3, lambda p=personaje: self.dibujar_personaje(pantalla, p)))
        self.dibujar_objetos(pantalla, extras)
        self.dibujar_panel(pantalla)


# ---------------------------------------------------------------------------
# Menú y ciclo principal
# ---------------------------------------------------------------------------

MODOS = [AtrapaGemas, Bandera]


def rectangulo_del_menu(i):
    return pygame.Rect(ANCHO // 2 - 430, 250 + i * 150, 860, 120)


def dibujar_menu(pantalla):
    letrero(pantalla, "MAZERUNNER", ANCHO // 2, 50, 84, BLANCO, "centro")
    letrero(pantalla, "ELIGE UN MODO", ANCHO // 2, 170, 30, ORO, "centro")
    for i, modo in enumerate(MODOS):
        caja = rectangulo_del_menu(i)
        pygame.draw.rect(pantalla, NEGRO, caja.move(7, 7), border_radius=16)
        pygame.draw.rect(pantalla, BLANCO, caja, border_radius=16)
        pygame.draw.rect(pantalla, NEGRO, caja, 5, border_radius=16)
        pantalla.blit(fuente(34, carrera=True).render(f"{i + 1}. {modo.titulo}", True, ROJO), (caja.x + 24, caja.y + 14))
        escribir(pantalla, modo.resumen, caja.x + 26, caja.y + 72, 17, NEGRO)
    letrero(pantalla, "CLIC O TECLAS 1 Y 2", ANCHO // 2, ALTO - 70, 22, ORO, "centro")


def avanzar(modo, dt):
    """Un instante de juego: cuenta regresiva y lógica del modo."""
    modo.tiempo += dt
    if modo.espera > 0:
        # Durante la cuenta regresiva nadie se mueve, así todos salen a la vez.
        modo.espera -= dt
        if modo.espera <= 0:
            modo.salida = modo.tiempo
    elif modo.estado == "jugando":
        modo.actualizar(dt)


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("MazeRunner")
    reloj = pygame.time.Clock()
    modo = None      # None significa que se está en el menú
    activo = True
    while activo:
        # Se limita dt para que una pausa de la ventana no haga saltar a nadie.
        dt = min(reloj.tick(60) / 1000, 0.05)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                activo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    modo = None
                elif modo is None and pygame.K_1 <= evento.key < pygame.K_1 + len(MODOS):
                    modo = MODOS[evento.key - pygame.K_1]()
                elif modo is not None:
                    modo.tecla(evento.key)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and modo is None:
                for i, clase in enumerate(MODOS):
                    if rectangulo_del_menu(i).collidepoint(evento.pos):
                        modo = clase()
        pantalla.fill(CIELO)
        if modo is None:
            dibujar_menu(pantalla)
        else:
            # La dirección sale de la tecla que esté pulsada en este momento.
            pulsadas = pygame.key.get_pressed()
            modo.direccion = next((d for tecla, d in TECLAS.items() if pulsadas[tecla]), None)
            avanzar(modo, dt)
            modo.dibujar(pantalla)
            modo.dibujar_cuenta(pantalla)
            escribir(pantalla, modo.ayuda, 14, ALTO - 30, 15, GRIS)
            modo.dibujar_cierre(pantalla)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
