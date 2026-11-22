"""MazeRunner, fase 2: mapa editable.

Una ventana con un mapa que se pinta con el ratón y, a un lado, una tabla que
compara los cinco algoritmos de búsqueda. La tabla se vuelve a calcular con
cada cambio del mapa. También se puede ver, animada, la forma en que explora
el algoritmo que se elija.

El mapa se puede ver y editar de dos formas, que comparten los mismos datos:
    Cuadrícula   cada casilla es un cuadro del color de su terreno
    Grafo        cada casilla transitable es un vértice y cada par de casillas
                 vecinas es una arista; los muros no aparecen

Cómo se usa:
    Clic izquierdo (o arrastrar)   pinta con el pincel elegido
    Clic derecho (o arrastrar)     borra: deja llano y quita objetos
    En la vista de grafo, un clic con el pincel de muro sobre el hueco de un
    muro lo quita
    Teclas 1 a 7                   eligen el pincel
    Clic en un renglón de la tabla elige el algoritmo que se muestra
    Espacio                        anima la exploración del algoritmo elegido
    V                              cambia la velocidad de la animación
    G                              cambia entre la vista de cuadrícula y la de grafo
    L                              limpia el mapa
    R                              vuelve al mapa de ejemplo

Para ejecutarlo:  python fase2_editor.py
"""

import heapq                              # cola de prioridad: siempre entrega el elemento más pequeño
from collections import deque             # cola: se saca por un extremo y se mete por el otro
from itertools import permutations        # genera todos los órdenes posibles de una lista
from math import cos, pi, sin             # para calcular las puntas de la estrella

import pygame                             # ventana, dibujo, ratón y teclado


# ============================================================================
# 1. EL MAPA Y LOS ALGORITMOS
# Es la misma lógica del notebook de la fase 1.
# ============================================================================

# Costo de entrar a cada tipo de terreno. Los muros no aparecen porque no se pueden pisar.
COSTOS = {'.': 1, 'B': 3, 'A': 5}

# Los 4 movimientos permitidos como (cambio de fila, cambio de columna).
MOVIMIENTOS = [(-1, 0), (0, 1), (1, 0), (0, -1)]   # arriba, derecha, abajo, izquierda

# Con más objetos, probar todos los órdenes tardaría demasiado para recalcular en cada cambio.
MAXIMO_DE_OBJETOS = 6

MAPA_DE_EJEMPLO = """
......................
.I.....#..............
.......#....BBBB......
.......#....BBBB...O..
...AAA.#....BBBB......
...AAA.#..............
...AAA.....####.......
...AAA.....#..........
...........#....AAAA..
.O.....BBB.#....AAAA..
.......BBB.#....AAAA..
.......BBB.#..........
...........#########..
......................
....................M.
......................
"""


def leer_mapa(texto):
    """Convierte el texto de un mapa en un diccionario fácil de consultar.

    Entrada:
        texto: el mapa escrito con un carácter por casilla y un renglón por fila.
               '.' llano, 'B' bosque, 'A' agua, '#' muro, 'I' inicio, 'M' meta, 'O' objeto.

    Salida: un diccionario con
        'terreno':  diccionario {(fila, columna): carácter del terreno}
        'filas':    número de filas
        'columnas': número de columnas (el de la fila más larga)
        'inicio':   casilla de inicio
        'meta':     casilla de meta
        'objetos':  lista con las casillas de los objetos, en orden de lectura
    """
    lineas = texto.strip('\n').split('\n')          # quita renglones vacíos de las orillas y separa por fila
    filas = len(lineas)
    columnas = max(len(linea) for linea in lineas)  # la fila más larga define el ancho

    terreno = {}
    inicio = None
    meta = None
    objetos = []

    for f, linea in enumerate(lineas):
        linea = linea.ljust(columnas, '#')          # lo que le falta a una fila corta se rellena con muro
        for c, caracter in enumerate(linea):
            if caracter == ' ':                     # un espacio también es muro
                caracter = '#'
            elif caracter == 'I':
                inicio = (f, c)
                caracter = '.'                      # el inicio se pisa como llano
            elif caracter == 'M':
                meta = (f, c)
                caracter = '.'                      # la meta se pisa como llano
            elif caracter == 'O':
                objetos.append((f, c))
                caracter = '.'                      # los objetos están sobre llano
            elif caracter not in ('.', 'B', 'A', '#'):
                raise ValueError(f'Carácter desconocido en el mapa: {caracter!r}')
            terreno[(f, c)] = caracter

    if inicio is None or meta is None:
        raise ValueError('El mapa necesita un inicio (I) y una meta (M).')

    return {'terreno': terreno, 'filas': filas, 'columnas': columnas,
            'inicio': inicio, 'meta': meta, 'objetos': objetos}


def vecinos(mapa, casilla):
    """Da las casillas a las que se puede pasar desde una casilla. Son las aristas del grafo.

    Entradas:
        mapa:    el diccionario que devuelve leer_mapa
        casilla: la posición (fila, columna)

    Salida: lista de pares (vecina, costo de entrar a ella), en el orden
            arriba, derecha, abajo, izquierda. Los muros y lo que queda
            fuera del mapa no aparecen.
    """
    f, c = casilla
    resultado = []
    for df, dc in MOVIMIENTOS:
        vecina = (f + df, c + dc)
        terreno = mapa['terreno'].get(vecina, '#')   # fuera del mapa cuenta como muro
        if terreno != '#':
            resultado.append((vecina, COSTOS[terreno]))
    return resultado


def reconstruir_ruta(padres, meta):
    """Arma la ruta caminando hacia atrás desde la meta.

    Entradas:
        padres: diccionario {casilla: casilla desde la que se llegó a ella}.
                El inicio tiene como padre None.
        meta:   la casilla donde termina la ruta

    Salida: lista de casillas desde el inicio hasta la meta.
    """
    ruta = []
    casilla = meta
    while casilla is not None:        # el padre del inicio es None: ahí se detiene
        ruta.append(casilla)
        casilla = padres[casilla]     # se retrocede a la casilla desde la que se llegó
    ruta.reverse()                    # se armó de la meta al inicio; se voltea
    return ruta


def estimacion(casilla, meta):
    """Estima cuánto falta para llegar a la meta: la distancia en casillas, sin diagonales.

    Entradas:
        casilla: la posición (fila, columna) desde la que se mide
        meta:    la posición (fila, columna) de la meta

    Salida: cuántas filas faltan más cuántas columnas faltan.
    """
    return abs(casilla[0] - meta[0]) + abs(casilla[1] - meta[1])


def bfs(mapa, inicio, meta):
    """Búsqueda en anchura (BFS): explora por capas alrededor del inicio.

    Entradas: el mapa, la casilla de inicio y la casilla de meta.
    Salida:   el par (ruta, exploradas). La ruta es None si no hay camino.
    Garantía: la ruta tiene la menor cantidad de pasos posible. No toma en cuenta los costos.
    """
    cola = deque([inicio])               # casillas pendientes, en orden de llegada
    padres = {inicio: None}              # desde dónde se llegó a cada casilla
    exploradas = []

    while cola:
        actual = cola.popleft()          # sale la que lleva más tiempo esperando
        exploradas.append(actual)
        if actual == meta:
            return reconstruir_ruta(padres, meta), exploradas
        for vecina, costo in vecinos(mapa, actual):
            if vecina not in padres:     # solo las que no se habían descubierto
                padres[vecina] = actual
                cola.append(vecina)      # entra al final de la cola

    return None, exploradas              # la cola se vació sin llegar a la meta: no hay camino


def dfs(mapa, inicio, meta):
    """Búsqueda en profundidad (DFS): sigue un camino hasta el fondo antes de probar otro.

    Entradas: el mapa, la casilla de inicio y la casilla de meta.
    Salida:   el par (ruta, exploradas). La ruta es None si no hay camino.
    Garantía: ninguna sobre la ruta. Si hay camino lo encuentra, pero puede ser largo y caro.
    """
    pila = [inicio]                      # casillas pendientes; la última de la lista es la de arriba
    padres = {inicio: None}
    exploradas = []
    vistas = set()                       # casillas ya exploradas

    while pila:
        actual = pila.pop()              # sale la última que entró
        if actual in vistas:             # una casilla puede estar repetida en la pila: se ignora
            continue
        vistas.add(actual)
        exploradas.append(actual)
        if actual == meta:
            return reconstruir_ruta(padres, meta), exploradas
        # Se meten al revés para que la primera en salir sea la de arriba,
        # luego derecha, abajo e izquierda.
        for vecina, costo in reversed(vecinos(mapa, actual)):
            if vecina not in vistas:
                padres[vecina] = actual
                pila.append(vecina)      # entra arriba de la pila

    return None, exploradas


def dijkstra(mapa, inicio, meta):
    """Algoritmo de Dijkstra: explora siempre la casilla más barata de alcanzar desde el inicio.

    Entradas: el mapa, la casilla de inicio y la casilla de meta.
    Salida:   el par (ruta, exploradas). La ruta es None si no hay camino.
    Garantía: la ruta tiene el menor costo posible.
    """
    cola = [(0, inicio)]                 # cola de prioridad con pares (costo acumulado, casilla)
    costos = {inicio: 0}                 # el menor costo conocido para llegar a cada casilla
    padres = {inicio: None}
    exploradas = []
    vistas = set()

    while cola:
        costo, actual = heapq.heappop(cola)      # sale la de menor costo acumulado
        if actual in vistas:                     # ya se había explorado con un costo menor: se ignora
            continue
        vistas.add(actual)
        exploradas.append(actual)
        if actual == meta:
            return reconstruir_ruta(padres, meta), exploradas
        for vecina, paso in vecinos(mapa, actual):
            nuevo = costo + paso                 # costo de llegar a la vecina pasando por la actual
            if vecina not in costos or nuevo < costos[vecina]:
                costos[vecina] = nuevo           # es la forma más barata de llegar que se conoce
                padres[vecina] = actual
                heapq.heappush(cola, (nuevo, vecina))

    return None, exploradas


def voraz(mapa, inicio, meta):
    """Búsqueda voraz: explora siempre la casilla que parece más cerca de la meta.

    Entradas: el mapa, la casilla de inicio y la casilla de meta.
    Salida:   el par (ruta, exploradas). La ruta es None si no hay camino.
    Garantía: ninguna sobre la ruta. Suele explorar muy poco, pero no toma en cuenta los costos.
    """
    cola = [(estimacion(inicio, meta), inicio)]  # cola de prioridad con pares (estimación, casilla)
    padres = {inicio: None}
    exploradas = []

    while cola:
        distancia, actual = heapq.heappop(cola)  # sale la que parece más cerca de la meta
        exploradas.append(actual)
        if actual == meta:
            return reconstruir_ruta(padres, meta), exploradas
        for vecina, costo in vecinos(mapa, actual):
            if vecina not in padres:
                padres[vecina] = actual
                # La prioridad es solo la estimación: el costo del terreno no se usa para nada.
                heapq.heappush(cola, (estimacion(vecina, meta), vecina))

    return None, exploradas


def a_estrella(mapa, inicio, meta):
    """Algoritmo A*: explora la casilla con menor suma de lo ya gastado más lo que se estima que falta.

    Entradas: el mapa, la casilla de inicio y la casilla de meta.
    Salida:   el par (ruta, exploradas). La ruta es None si no hay camino.
    Garantía: la ruta tiene el menor costo posible, porque la estimación nunca se pasa del costo real.
    """
    distancia = estimacion(inicio, meta)
    cola = [(distancia, distancia, inicio)]      # (costo acumulado + estimación, estimación, casilla)
    costos = {inicio: 0}
    padres = {inicio: None}
    exploradas = []
    vistas = set()

    while cola:
        prioridad, distancia, actual = heapq.heappop(cola)   # sale la de menor prioridad
        if actual in vistas:
            continue
        vistas.add(actual)
        exploradas.append(actual)
        if actual == meta:
            return reconstruir_ruta(padres, meta), exploradas
        for vecina, paso in vecinos(mapa, actual):
            nuevo = costos[actual] + paso        # lo gastado para llegar a la vecina pasando por la actual
            if vecina not in costos or nuevo < costos[vecina]:
                costos[vecina] = nuevo
                padres[vecina] = actual
                distancia = estimacion(vecina, meta)         # lo que se cree que falta desde la vecina
                # Prioridad = lo gastado + lo que falta. La estimación sola va después para los empates.
                heapq.heappush(cola, (nuevo + distancia, distancia, vecina))

    return None, exploradas


# Los cinco algoritmos con su nombre, para poder recorrerlos todos con un ciclo.
ALGORITMOS = {'BFS': bfs, 'DFS': dfs, 'Dijkstra': dijkstra, 'Voraz': voraz, 'A*': a_estrella}


def medir(mapa, ruta):
    """Calcula los pasos y el costo de una ruta.

    Entradas: el mapa y la ruta (lista de casillas del inicio a la meta).
    Salida:   el par (pasos, costo). El inicio no se cobra porque no se entra a él.
    """
    pasos = len(ruta) - 1             # una ruta de n casillas tiene n - 1 movimientos
    costo = sum(COSTOS[mapa['terreno'][casilla]] for casilla in ruta[1:])
    return pasos, costo


def ordenar_objetos(mapa):
    """Decide en qué orden conviene recoger los objetos: el orden de menor costo total.

    Arma el grafo completo entre el inicio, los objetos y la meta (cada arista pesa
    el costo de la ruta más barata entre sus dos puntos) y prueba todos los órdenes.

    Entrada: el mapa.

    Salida: el par (orden, se_puede).
        orden:    lista de los objetos en el mejor orden de visita
        se_puede: False si hay algún punto al que no se puede llegar
    """
    objetos = mapa['objetos']
    if not objetos:
        return [], True

    puntos = [mapa['inicio']] + objetos + [mapa['meta']]

    # Pesos del grafo completo. Como todos los puntos están sobre llano, ir de a a b
    # cuesta lo mismo que regresar: basta calcular cada par una vez.
    costos = {}
    for i, a in enumerate(puntos):
        for b in puntos[i + 1:]:
            ruta, exploradas = dijkstra(mapa, a, b)
            if ruta is None:
                return list(objetos), False          # hay un punto aislado: no existe recorrido
            costos[(a, b)] = costos[(b, a)] = medir(mapa, ruta)[1]

    # Se prueba cada orden posible y se guarda el más barato.
    mejor_orden = None
    mejor_costo = None
    for orden in permutations(objetos):
        paradas = [mapa['inicio']] + list(orden) + [mapa['meta']]
        costo = sum(costos[(a, b)] for a, b in zip(paradas, paradas[1:]))
        if mejor_costo is None or costo < mejor_costo:
            mejor_orden, mejor_costo = list(orden), costo
    return mejor_orden, True


def recorrer(mapa, algoritmo, paradas):
    """Corre un algoritmo por tramos: de cada parada a la siguiente.

    Entradas:
        mapa:      el mapa
        algoritmo: una de las cinco funciones de búsqueda
        paradas:   lista de casillas por las que hay que pasar, en orden
                   (inicio, objetos y meta)

    Salida: el par (ruta, exploradas).
        ruta:       la ruta completa uniendo todos los tramos, o None si algún tramo no tiene camino
        exploradas: todas las casillas exploradas, tramo tras tramo, en orden
    """
    ruta_completa = [paradas[0]]
    exploradas = []
    for a, b in zip(paradas, paradas[1:]):           # cada parada con la que le sigue
        ruta, vistas = algoritmo(mapa, a, b)
        exploradas += vistas
        if ruta is None:
            return None, exploradas
        ruta_completa += ruta[1:]                    # sin la primera casilla, que ya está puesta
    return ruta_completa, exploradas


def comparar(mapa):
    """Corre los cinco algoritmos sobre el mapa y mide a cada uno.

    Si hay objetos, todos los algoritmos los visitan en el mismo orden (el de
    menor costo) y cada uno busca por su cuenta el camino de cada tramo.

    Entrada: el mapa.

    Salida: el par (resultados, orden).
        resultados: diccionario {nombre: {'ruta', 'exploradas', 'pasos', 'costo'}}.
                    Sin ruta, los pasos y el costo son None.
        orden:      los objetos en el orden en que se visitan
    """
    orden, se_puede = ordenar_objetos(mapa)
    paradas = [mapa['inicio']] + orden + [mapa['meta']]
    resultados = {}
    for nombre, algoritmo in ALGORITMOS.items():
        ruta, exploradas = recorrer(mapa, algoritmo, paradas)
        pasos, costo = medir(mapa, ruta) if ruta else (None, None)
        resultados[nombre] = {'ruta': ruta, 'exploradas': exploradas, 'pasos': pasos, 'costo': costo}
    return resultados, orden


# El costo se multiplica por este número para que quede en las cifras de la izquierda
# del puntaje, y las casillas exploradas en las últimas cuatro. Tiene que ser mayor que
# cualquier cantidad posible de casillas exploradas.
BASE_DEL_PUNTAJE = 10000


def puntaje(resultado):
    """Calcula el puntaje de un algoritmo en un mapa. Mientras más bajo, mejor.

        puntaje = costo * 10 000 + casillas exploradas

    Las últimas cuatro cifras son las casillas exploradas y las de adelante son
    el costo. Como una diferencia de 1 en el costo vale 10 000 y las casillas
    exploradas siempre son menos que eso, un costo menor da siempre un puntaje
    menor; las casillas exploradas solo deciden cuando el costo empata.

    Entrada: el resultado de un algoritmo, un diccionario con 'ruta', 'exploradas' y 'costo'.

    Salida: el puntaje, un número entero. None si el algoritmo no encontró ruta.
    """
    if resultado['ruta'] is None:
        return None                                  # sin ruta no hay puntaje: no participa
    exploradas = len(resultado['exploradas'])
    if exploradas >= BASE_DEL_PUNTAJE:
        # Con tantas casillas el número se desbordaría hacia las cifras del costo.
        raise ValueError(f'El puntaje solo sirve con menos de {BASE_DEL_PUNTAJE} casillas exploradas.')
    return resultado['costo'] * BASE_DEL_PUNTAJE + exploradas


def mejor_opcion(resultados):
    """Elige la mejor opción de un mapa: el algoritmo con el puntaje más bajo.

    Entrada: el diccionario de resultados que devuelve comparar.

    Salida: lista con los nombres de los ganadores.
            Normalmente trae uno solo. Trae varios si empatan en puntaje, y
            queda vacía si ningún algoritmo encontró ruta.
    """
    # El puntaje de cada algoritmo que sí encontró ruta.
    puntajes = {nombre: puntaje(r) for nombre, r in resultados.items() if r['ruta'] is not None}
    if not puntajes:
        return []                                    # no existe ruta: no hay ganador
    mas_bajo = min(puntajes.values())
    return [nombre for nombre, valor in puntajes.items() if valor == mas_bajo]


# ============================================================================
# 2. EDITAR EL MAPA
# ============================================================================

def pintar(mapa, casilla, pincel):
    """Aplica un pincel sobre una casilla del mapa.

    Entradas:
        mapa:    el mapa; se modifica directamente
        casilla: la posición (fila, columna)
        pincel:  '.', 'B', 'A' o '#' para un terreno; 'I' inicio, 'M' meta, 'O' objeto

    Salida: True si el mapa cambió y False si quedó igual. Sirve para saber
            si hay que volver a calcular la tabla.
    """
    if casilla not in mapa['terreno']:               # clic fuera de la cuadrícula
        return False
    es_especial = casilla in (mapa['inicio'], mapa['meta'])

    if pincel in ('I', 'M'):
        if es_especial:                              # el inicio y la meta no pueden compartir casilla
            return False
        if casilla in mapa['objetos']:
            mapa['objetos'].remove(casilla)
        mapa['terreno'][casilla] = '.'               # el inicio y la meta están sobre llano
        mapa['inicio' if pincel == 'I' else 'meta'] = casilla   # se mueve: solo hay uno de cada uno
        return True

    if pincel == 'O':
        if es_especial or casilla in mapa['objetos'] or len(mapa['objetos']) >= MAXIMO_DE_OBJETOS:
            return False
        mapa['terreno'][casilla] = '.'               # los objetos están sobre llano
        mapa['objetos'].append(casilla)
        return True

    # El pincel es un terreno.
    if es_especial:                                  # no se pinta sobre el inicio ni sobre la meta
        return False
    cambio = False
    if casilla in mapa['objetos']:                   # pintar terreno encima quita el objeto
        mapa['objetos'].remove(casilla)
        cambio = True
    if mapa['terreno'][casilla] != pincel:
        mapa['terreno'][casilla] = pincel
        cambio = True
    return cambio


def mapa_limpio(filas, columnas):
    """Crea un mapa de puro llano con el inicio a la izquierda y la meta a la derecha.

    Entradas: el número de filas y de columnas.
    Salida:   el diccionario del mapa.
    """
    renglones = ['.' * columnas for f in range(filas)]
    medio = filas // 2
    renglones[medio] = '.I' + '.' * (columnas - 4) + 'M.'
    return leer_mapa('\n'.join(renglones))


# ============================================================================
# 3. LA VENTANA
# Medidas en pixeles. La cuadrícula va a la izquierda y el panel a la derecha.
# ============================================================================

CELDA = 40                               # lado de cada casilla
FILAS, COLUMNAS = 16, 22                 # tamaño del mapa
ANCHO_MAPA = COLUMNAS * CELDA
ALTO = FILAS * CELDA
ANCHO_PANEL = 400
ANCHO = ANCHO_MAPA + ANCHO_PANEL
X_PANEL = ANCHO_MAPA + 16                # margen izquierdo del contenido del panel

# Colores (rojo, verde, azul).
COLORES = {'.': (239, 233, 200), 'B': (88, 165, 92), 'A': (109, 179, 242), '#': (59, 59, 59)}
COLOR_INICIO = (0, 200, 83)
COLOR_META = (255, 193, 7)
ROJO = (198, 40, 40)
NEGRO = (24, 24, 24)
BLANCO = (255, 255, 255)
GRIS = (150, 150, 150)
GRIS_OSCURO = (52, 52, 52)
VERDE_CLARO = (120, 220, 140)
COLOR_EXPLORADA = (126, 87, 194, 115)    # el cuarto número es la transparencia
COLOR_RUTA = (229, 57, 53)
FONDO_GRAFO = (246, 245, 240)            # fondo de la vista de grafo; ahí se ven los huecos de los muros
RADIO_VERTICE = 13                       # radio de cada vértice en la vista de grafo

# Los pinceles: carácter, nombre y tecla que lo elige.
PINCELES = [('.', 'Llano (1)', pygame.K_1), ('B', 'Bosque (3)', pygame.K_2), ('A', 'Agua (5)', pygame.K_3),
            ('#', 'Muro', pygame.K_4), ('I', 'Inicio', pygame.K_5), ('M', 'Meta', pygame.K_6),
            ('O', 'Objeto', pygame.K_7)]

# Velocidades de la animación: nombre y casillas exploradas por segundo.
VELOCIDADES = [('lenta', 8), ('normal', 30), ('rápida', 120)]

# Posición vertical de cada parte del panel.
Y_PINCELES = 70
Y_TABLA = 232
ALTO_RENGLON = 26
Y_FORMULA = 400                          # la fórmula del puntaje
Y_BOTONES = 528
Y_AVISOS = 598
ALTO_BOTON = 28

# La fórmula del puntaje y cómo leerlo, siempre visibles en el panel.
FORMULA = 'puntaje = costo × 10 000 + casillas exploradas'
EXPLICACION_DE_LA_FORMULA = ['Gana el puntaje más bajo, en verde. Se lee así: las últimas',
                             'cuatro cifras son las casillas exploradas y las de adelante,',
                             'el costo. Un algoritmo sin ruta no tiene puntaje.']


def casilla_en(posicion):
    """Convierte una posición del ratón en la casilla que hay debajo.

    Entrada: el par (x, y) en pixeles.
    Salida:  la casilla (fila, columna). Si el ratón está sobre el panel,
             la columna queda fuera del mapa y pintar la ignora.
    """
    x, y = posicion
    return (y // CELDA, x // CELDA)


def centro_de(casilla):
    """Da el pixel del centro de una casilla.

    Entrada: la casilla (fila, columna).
    Salida:  el par (x, y) en pixeles.
    """
    f, c = casilla
    return (c * CELDA + CELDA // 2, f * CELDA + CELDA // 2)


def puntos_de_estrella(centro, radio):
    """Calcula las 10 esquinas de una estrella de 5 puntas.

    Entradas: el centro (x, y) y el radio de las puntas, en pixeles.
    Salida:   lista de 10 puntos, alternando una punta y un hueco.
    """
    x, y = centro
    puntos = []
    for i in range(10):
        r = radio if i % 2 == 0 else radio * 0.42    # las posiciones pares son puntas; las impares, huecos
        angulo = -pi / 2 + i * pi / 5                # empieza arriba y avanza un décimo de vuelta
        puntos.append((x + r * cos(angulo), y + r * sin(angulo)))
    return puntos


def dibujar_inicio(pantalla, centro, radio):
    """Dibuja el inicio: un punto verde con borde negro."""
    pygame.draw.circle(pantalla, COLOR_INICIO, centro, radio)
    pygame.draw.circle(pantalla, NEGRO, centro, radio, 2)        # el último número es el grosor del borde


def dibujar_meta(pantalla, centro, radio):
    """Dibuja la meta: una estrella dorada con borde negro."""
    puntos = puntos_de_estrella(centro, radio)
    pygame.draw.polygon(pantalla, COLOR_META, puntos)
    pygame.draw.polygon(pantalla, NEGRO, puntos, 2)


def escribir(pantalla, fuente, texto, posicion, color=BLANCO, derecha=False):
    """Escribe un texto en la pantalla.

    Entradas:
        pantalla: donde se dibuja
        fuente:   el tipo de letra ya preparado
        texto:    lo que se escribe
        posicion: el par (x, y) de la esquina superior izquierda del texto
        color:    color de la letra
        derecha:  si es True, la x indica dónde termina el texto y no dónde empieza
    """
    imagen = fuente.render(str(texto), True, color)  # True suaviza las orillas de las letras
    x, y = posicion
    if derecha:
        x -= imagen.get_width()
    pantalla.blit(imagen, (x, y))                    # blit pega una imagen sobre otra


def casillas_visibles(estado):
    """Dice qué casillas exploradas hay que mostrar en este momento.

    Entrada: el diccionario de estado.

    Salida: el par (visibles, animando).
        visibles: las casillas exploradas por el algoritmo elegido. Durante la
                  animación, solo las exploradas hasta ese momento.
        animando: True si hay una animación en curso
    """
    exploradas = estado['resultados'][estado['elegido']]['exploradas']
    animando = estado['avance'] is not None
    visibles = exploradas[:int(estado['avance'])] if animando else exploradas
    return visibles, animando


def dibujar_objetos_y_simbolos(pantalla, estado, fuentes):
    """Dibuja lo que va encima del mapa en las dos vistas: objetos, inicio y meta.

    Entradas:
        pantalla: donde se dibuja
        estado:   el diccionario de estado
        fuentes:  los tipos de letra ya preparados
    """
    mapa = estado['mapa']
    # Los objetos: un círculo blanco con su número, según el orden en que se visitan.
    for casilla in mapa['objetos']:
        pygame.draw.circle(pantalla, BLANCO, centro_de(casilla), 14)
        pygame.draw.circle(pantalla, NEGRO, centro_de(casilla), 14, 2)
        numero = str(estado['orden'].index(casilla) + 1)
        imagen = fuentes['negrita'].render(numero, True, NEGRO)
        pantalla.blit(imagen, imagen.get_rect(center=centro_de(casilla)))   # centrado en la casilla
    # El punto verde del inicio y la estrella de la meta.
    dibujar_inicio(pantalla, centro_de(mapa['inicio']), 12)
    dibujar_meta(pantalla, centro_de(mapa['meta']), 17)


def dibujar_cuadricula(pantalla, estado, fuentes):
    """Dibuja el mapa como cuadrícula, con el resultado del algoritmo elegido.

    Entradas:
        pantalla: donde se dibuja
        estado:   el diccionario con todo lo que cambia mientras corre el programa
        fuentes:  los tipos de letra ya preparados

    Se dibuja por capas: terrenos, casillas exploradas, cuadrícula, ruta y símbolos.
    """
    mapa = estado['mapa']
    ruta = estado['resultados'][estado['elegido']]['ruta']
    visibles, animando = casillas_visibles(estado)

    # 1. El terreno de cada casilla.
    for (f, c), terreno in mapa['terreno'].items():
        pygame.draw.rect(pantalla, COLORES[terreno], (c * CELDA, f * CELDA, CELDA, CELDA))

    # 2. Un velo morado semitransparente sobre cada casilla explorada.
    #    set() quita las repetidas: con objetos, una casilla puede explorarse en varios tramos.
    for f, c in set(visibles):
        pantalla.blit(estado['velo'], (c * CELDA, f * CELDA))

    # 3. Las líneas de la cuadrícula.
    for c in range(COLUMNAS + 1):
        pygame.draw.line(pantalla, NEGRO, (c * CELDA, 0), (c * CELDA, ALTO))
    for f in range(FILAS + 1):
        pygame.draw.line(pantalla, NEGRO, (0, f * CELDA), (ANCHO_MAPA, f * CELDA))

    # 4. La ruta, cuando ya terminó la animación: una línea roja por los centros de sus casillas.
    if ruta and not animando:
        pygame.draw.lines(pantalla, COLOR_RUTA, False, [centro_de(casilla) for casilla in ruta], 5)

    # 5. Durante la animación, un marco rojo en la última casilla explorada.
    if animando and visibles:
        f, c = visibles[-1]
        pygame.draw.rect(pantalla, ROJO, (c * CELDA + 2, f * CELDA + 2, CELDA - 4, CELDA - 4), 4)

    # 6. Los objetos, el inicio y la meta.
    dibujar_objetos_y_simbolos(pantalla, estado, fuentes)


def dibujar_grafo(pantalla, estado, fuentes):
    """Dibuja el mismo mapa como grafo, con el resultado del algoritmo elegido.

    Entradas:
        pantalla: donde se dibuja
        estado:   el diccionario con todo lo que cambia mientras corre el programa
        fuentes:  los tipos de letra ya preparados

    Cada casilla que no es muro es un vértice, dibujado en el centro del lugar
    que ocupa en la cuadrícula. Cada par de casillas vecinas es una arista.
    Los muros no se dibujan: donde hay un muro queda un hueco.

    Se dibuja por capas: fondo, aristas, ruta, vértices y símbolos.
    """
    mapa = estado['mapa']
    ruta = estado['resultados'][estado['elegido']]['ruta']
    visibles, animando = casillas_visibles(estado)
    exploradas = set(visibles)                       # conjunto: preguntar si una casilla está es más rápido

    # 1. El fondo, que tapa lo que se dibujó en el cuadro anterior.
    pygame.draw.rect(pantalla, FONDO_GRAFO, (0, 0, ANCHO_MAPA, ALTO))

    # 2. Las aristas. Para no dibujar cada una dos veces, desde cada casilla solo se
    #    miran su vecina de la derecha y la de abajo.
    for (f, c), terreno in mapa['terreno'].items():
        if terreno == '#':
            continue                                 # un muro no es vértice: no tiene aristas
        for vecina in ((f, c + 1), (f + 1, c)):
            if mapa['terreno'].get(vecina, '#') != '#':
                pygame.draw.line(pantalla, GRIS, centro_de((f, c)), centro_de(vecina), 2)

    # 3. Las aristas de la ruta, en rojo y más gruesas, cuando ya terminó la animación.
    if ruta and not animando:
        pygame.draw.lines(pantalla, COLOR_RUTA, False, [centro_de(casilla) for casilla in ruta], 7)

    # 4. Los vértices: un círculo del color de su terreno con lo que cuesta entrar a él.
    for casilla, terreno in mapa['terreno'].items():
        if terreno == '#':
            continue
        centro = centro_de(casilla)
        if casilla in exploradas:
            # Un vértice explorado lleva alrededor un aro morado.
            pygame.draw.circle(pantalla, COLOR_EXPLORADA[:3], centro, RADIO_VERTICE + 5)
        pygame.draw.circle(pantalla, COLORES[terreno], centro, RADIO_VERTICE)
        pygame.draw.circle(pantalla, NEGRO, centro, RADIO_VERTICE, 1)
        imagen = fuentes['costos'][terreno]          # el número ya está preparado: 1, 3 o 5
        pantalla.blit(imagen, imagen.get_rect(center=centro))

    # 5. Durante la animación, un aro rojo en el último vértice explorado.
    if animando and visibles:
        pygame.draw.circle(pantalla, ROJO, centro_de(visibles[-1]), RADIO_VERTICE + 6, 4)

    # 6. Los objetos, el inicio y la meta, encima de sus vértices.
    dibujar_objetos_y_simbolos(pantalla, estado, fuentes)


def dibujar_mapa(pantalla, estado, fuentes):
    """Dibuja el mapa en la vista que esté elegida: cuadrícula o grafo.

    Entradas:
        pantalla: donde se dibuja
        estado:   el diccionario de estado; estado['vista'] dice cuál vista toca
        fuentes:  los tipos de letra ya preparados
    """
    if estado['vista'] == 'grafo':
        dibujar_grafo(pantalla, estado, fuentes)
    else:
        dibujar_cuadricula(pantalla, estado, fuentes)


def crear_botones():
    """Prepara los botones del panel: los pinceles, los renglones de la tabla y las acciones.

    Salida: lista de diccionarios {'zona', 'tipo', 'valor', 'texto'}.
        zona:  el rectángulo del botón en la pantalla
        tipo:  'pincel', 'algoritmo' o 'accion'
        valor: qué pincel, qué algoritmo o qué acción representa
        texto: lo que lleva escrito (los renglones de la tabla se escriben aparte)
    """
    botones = []
    ancho = (ANCHO_PANEL - 40) // 2                  # dos botones por renglón
    paso = ALTO_BOTON + 6                            # distancia entre un renglón de botones y el siguiente

    # El botón que cambia de vista, arriba, junto al título.
    botones.append({'zona': pygame.Rect(X_PANEL + 170, 11, ANCHO_PANEL - 206, 32), 'tipo': 'accion',
                    'valor': 'vista', 'texto': ''})

    # Los pinceles, en dos columnas.
    for i, (pincel, nombre, tecla) in enumerate(PINCELES):
        x = X_PANEL + (i % 2) * (ancho + 8)
        y = Y_PINCELES + (i // 2) * paso
        botones.append({'zona': pygame.Rect(x, y, ancho, ALTO_BOTON), 'tipo': 'pincel', 'valor': pincel,
                        'texto': f'{i + 1}  {nombre}'})

    # Un renglón de la tabla por algoritmo: hacer clic en él lo elige.
    for i, nombre in enumerate(ALGORITMOS):
        zona = pygame.Rect(X_PANEL - 6, Y_TABLA + 22 + i * ALTO_RENGLON, ANCHO_PANEL - 20, ALTO_RENGLON)
        botones.append({'zona': zona, 'tipo': 'algoritmo', 'valor': nombre, 'texto': ''})

    # Las acciones, en dos columnas.
    acciones = [('animar', 'Animar (Espacio)'), ('velocidad', ''), ('limpiar', 'Limpiar (L)'), ('ejemplo', 'Ejemplo (R)')]
    for i, (accion, texto) in enumerate(acciones):
        x = X_PANEL + (i % 2) * (ancho + 8)
        y = Y_BOTONES + (i // 2) * paso
        botones.append({'zona': pygame.Rect(x, y, ancho, ALTO_BOTON), 'tipo': 'accion', 'valor': accion, 'texto': texto})
    return botones


def dibujar_panel(pantalla, estado, fuentes):
    """Dibuja el panel de la derecha: pinceles, tabla con puntaje, fórmula, botones y avisos.

    Entradas:
        pantalla: donde se dibuja
        estado:   el diccionario con todo lo que cambia mientras corre el programa
        fuentes:  los tipos de letra ya preparados
    """
    mapa = estado['mapa']
    resultados = estado['resultados']
    ganadores = estado['ganadores']

    # Fondo del panel y una franja roja que lo separa del mapa.
    pygame.draw.rect(pantalla, NEGRO, (ANCHO_MAPA, 0, ANCHO_PANEL, ALTO))
    pygame.draw.rect(pantalla, ROJO, (ANCHO_MAPA, 0, 4, ALTO))

    escribir(pantalla, fuentes['titulo'], 'MazeRunner', (X_PANEL, 10))
    escribir(pantalla, fuentes['chica'], 'PINCEL', (X_PANEL, Y_PINCELES - 20), GRIS)
    escribir(pantalla, fuentes['chica'], 'COMPARACIÓN (clic en un algoritmo para verlo)', (X_PANEL, Y_TABLA - 22), GRIS)

    # Encabezado de la tabla. Las cuatro columnas de números van alineadas a la derecha.
    x_exploradas, x_pasos, x_costo, x_puntaje = X_PANEL + 164, X_PANEL + 218, X_PANEL + 272, X_PANEL + 364
    escribir(pantalla, fuentes['chica'], 'Algoritmo', (X_PANEL, Y_TABLA), GRIS)
    escribir(pantalla, fuentes['chica'], 'Exploradas', (x_exploradas, Y_TABLA), GRIS, derecha=True)
    escribir(pantalla, fuentes['chica'], 'Pasos', (x_pasos, Y_TABLA), GRIS, derecha=True)
    escribir(pantalla, fuentes['chica'], 'Costo', (x_costo, Y_TABLA), GRIS, derecha=True)
    escribir(pantalla, fuentes['chica'], 'Puntaje', (x_puntaje, Y_TABLA), GRIS, derecha=True)

    for boton in estado['botones']:
        zona = boton['zona']

        if boton['tipo'] == 'algoritmo':
            # Un renglón de la tabla. El algoritmo que se muestra en el mapa lleva fondo rojo.
            nombre = boton['valor']
            r = resultados[nombre]
            elegido = nombre == estado['elegido']
            if elegido:
                pygame.draw.rect(pantalla, ROJO, zona, border_radius=5)
            y = zona.y + 2
            escribir(pantalla, fuentes['negrita'], nombre, (X_PANEL, y))
            escribir(pantalla, fuentes['normal'], len(r['exploradas']), (x_exploradas, y), derecha=True)
            if r['ruta'] is None:
                # Sin ruta no hay pasos, ni costo, ni puntaje: no participa.
                escribir(pantalla, fuentes['normal'], 'sin ruta', (x_puntaje, y), BLANCO if elegido else GRIS, derecha=True)
            else:
                escribir(pantalla, fuentes['normal'], r['pasos'], (x_pasos, y), derecha=True)
                escribir(pantalla, fuentes['normal'], r['costo'], (x_costo, y), derecha=True)
                # El puntaje más bajo va en verde y en negrita. Si varios empatan, todos.
                if nombre in ganadores:
                    if elegido:
                        # Sobre el fondo rojo el verde no se lee: se pone detrás un fondo oscuro.
                        ancho = fuentes['negrita'].size(str(puntaje(r)))[0]
                        pygame.draw.rect(pantalla, NEGRO, (x_puntaje - ancho - 5, zona.y + 2, ancho + 10, zona.height - 4),
                                         border_radius=4)
                    escribir(pantalla, fuentes['negrita'], puntaje(r), (x_puntaje, y), VERDE_CLARO, derecha=True)
                else:
                    escribir(pantalla, fuentes['normal'], puntaje(r), (x_puntaje, y), derecha=True)
            continue

        # Un botón normal. El pincel elegido lleva fondo blanco; los demás, gris oscuro.
        activo = boton['tipo'] == 'pincel' and boton['valor'] == estado['pincel']
        pygame.draw.rect(pantalla, BLANCO if activo else GRIS_OSCURO, zona, border_radius=6)
        texto = boton['texto']
        if boton['valor'] == 'velocidad':
            texto = f"Velocidad: {VELOCIDADES[estado['velocidad']][0]} (V)"
        elif boton['valor'] == 'vista':
            # El botón dice a qué vista se pasa al oprimirlo.
            texto = 'Ver cuadrícula (G)' if estado['vista'] == 'grafo' else 'Ver grafo (G)'
        x_texto = zona.x + 10

        if boton['tipo'] == 'pincel':
            # Muestra de lo que pinta cada pincel: su color, el punto verde, la estrella o un objeto.
            muestra = (zona.x + 18, zona.centery)
            if boton['valor'] == 'I':
                dibujar_inicio(pantalla, muestra, 8)
            elif boton['valor'] == 'M':
                dibujar_meta(pantalla, muestra, 11)
            elif boton['valor'] == 'O':
                pygame.draw.circle(pantalla, BLANCO, muestra, 9)
                pygame.draw.circle(pantalla, NEGRO, muestra, 9, 2)
            else:
                pygame.draw.rect(pantalla, COLORES[boton['valor']], (zona.x + 9, zona.centery - 9, 18, 18))
                pygame.draw.rect(pantalla, GRIS, (zona.x + 9, zona.centery - 9, 18, 18), 1)
            x_texto = zona.x + 36

        # El texto se centra a lo alto del botón.
        alto_texto = fuentes['normal'].get_height()
        escribir(pantalla, fuentes['normal'], texto, (x_texto, zona.centery - alto_texto // 2), NEGRO if activo else BLANCO)

    # Debajo de la tabla: la fórmula del puntaje y cómo leerlo.
    escribir(pantalla, fuentes['formula'], FORMULA, (X_PANEL, Y_FORMULA), VERDE_CLARO)
    for i, linea in enumerate(EXPLICACION_DE_LA_FORMULA):
        escribir(pantalla, fuentes['chica'], linea, (X_PANEL, Y_FORMULA + 24 + i * 18), GRIS)

    # Avisos al pie: el estado del mapa y cómo se pinta.
    if not ganadores:
        aviso = 'Ningún algoritmo puede llegar: no hay mejor opción.'
    elif not mapa['objetos']:
        aviso = 'Sin objetos: se busca del inicio a la meta.'
    else:
        aviso = f"Objetos: {len(mapa['objetos'])} de {MAXIMO_DE_OBJETOS}. Su número es el orden de visita."
    escribir(pantalla, fuentes['chica'], aviso, (X_PANEL, Y_AVISOS), BLANCO)
    vista = 'grafo' if estado['vista'] == 'grafo' else 'cuadrícula'
    escribir(pantalla, fuentes['chica'], f'Vista de {vista}. Clic izquierdo pinta. Clic derecho borra.',
             (X_PANEL, Y_AVISOS + 19), GRIS)


def recalcular(estado):
    """Vuelve a correr los cinco algoritmos sobre el mapa actual y detiene la animación.

    Entrada: el diccionario de estado; se actualizan sus resultados, el orden de los
             objetos y la mejor opción.
    Se llama cada vez que el mapa cambia, y por eso la tabla y los puntajes
    siempre están al día, sin importar en qué vista se haya editado.
    """
    estado['resultados'], estado['orden'] = comparar(estado['mapa'])
    estado['ganadores'] = mejor_opcion(estado['resultados'])
    estado['avance'] = None


def hacer_accion(estado, accion):
    """Ejecuta una de las acciones del panel.

    Entradas:
        estado: el diccionario de estado
        accion: 'animar', 'velocidad', 'vista', 'limpiar' o 'ejemplo'
    """
    if accion == 'animar':
        estado['avance'] = 0.0                       # la animación empieza sin casillas exploradas
    elif accion == 'velocidad':
        estado['velocidad'] = (estado['velocidad'] + 1) % len(VELOCIDADES)   # pasa a la siguiente y da la vuelta
    elif accion == 'vista':
        # Solo cambia cómo se dibuja. El mapa y los resultados son los mismos en las dos vistas.
        estado['vista'] = 'cuadricula' if estado['vista'] == 'grafo' else 'grafo'
    elif accion == 'limpiar':
        estado['mapa'] = mapa_limpio(FILAS, COLUMNAS)
        recalcular(estado)
    elif accion == 'ejemplo':
        estado['mapa'] = leer_mapa(MAPA_DE_EJEMPLO)
        recalcular(estado)


def atender_clic(estado, posicion, boton_del_raton, arrastrando=False):
    """Decide qué hacer con un clic o un arrastre del ratón.

    Entradas:
        estado:           el diccionario de estado
        posicion:         el par (x, y) del ratón en pixeles
        boton_del_raton:  1 para el izquierdo y 3 para el derecho
        arrastrando:      True si el ratón se está moviendo con el botón oprimido

    En las dos vistas se edita igual, porque cada vértice del grafo está en el
    centro de su casilla: la posición del ratón se convierte en casilla de la
    misma forma.
    """
    if posicion[0] < ANCHO_MAPA:
        # Sobre el mapa: el botón izquierdo pinta con el pincel y el derecho borra dejando llano.
        casilla = casilla_en(posicion)
        pincel = estado['pincel'] if boton_del_raton == 1 else '.'
        # En el grafo los muros son huecos. Un clic con el pincel de muro sobre un hueco
        # quita ese muro. Solo con un clic, no al arrastrar, para poder trazar muros de corrido.
        if (estado['vista'] == 'grafo' and pincel == '#' and not arrastrando
                and estado['mapa']['terreno'].get(casilla) == '#'):
            pincel = '.'
        if pintar(estado['mapa'], casilla, pincel):
            recalcular(estado)                       # solo se recalcula si el mapa cambió de verdad
        return

    if boton_del_raton != 1:
        return
    # Sobre el panel: se busca el botón que está debajo del ratón.
    for boton in estado['botones']:
        if boton['zona'].collidepoint(posicion):
            if boton['tipo'] == 'pincel':
                estado['pincel'] = boton['valor']
            elif boton['tipo'] == 'algoritmo':
                estado['elegido'] = boton['valor']
                estado['avance'] = None              # al cambiar de algoritmo se muestra su resultado completo
            else:
                hacer_accion(estado, boton['valor'])


def crear_estado():
    """Prepara todo lo que cambia mientras corre el programa.

    Salida: un diccionario con
        'mapa':       el mapa que se está editando
        'vista':      'cuadricula' o 'grafo': cómo se dibuja el mapa
        'pincel':     el carácter del pincel elegido
        'elegido':    el nombre del algoritmo que se muestra sobre el mapa
        'resultados': lo que encontró cada algoritmo
        'ganadores':  los nombres de los algoritmos con el puntaje más bajo (lista)
        'orden':      los objetos en el orden en que se visitan
        'avance':     None si no hay animación; si la hay, cuántas casillas exploradas se muestran
        'velocidad':  la posición en la lista VELOCIDADES
        'botones':    los botones del panel
        'velo':       la imagen semitransparente que marca una casilla explorada
    """
    velo = pygame.Surface((CELDA, CELDA), pygame.SRCALPHA)       # SRCALPHA permite transparencia
    velo.fill(COLOR_EXPLORADA)
    estado = {'mapa': leer_mapa(MAPA_DE_EJEMPLO), 'vista': 'cuadricula', 'pincel': '#', 'elegido': 'A*',
              'resultados': None, 'ganadores': [], 'orden': [], 'avance': None, 'velocidad': 1,
              'botones': crear_botones(), 'velo': velo}
    recalcular(estado)
    return estado


def crear_fuentes():
    """Prepara los tipos de letra que usa el programa.

    Salida: diccionario {'titulo', 'normal', 'negrita', 'chica', 'formula', 'costos'}.
            'costos' no es un tipo de letra: guarda la imagen ya preparada del
            número que lleva cada vértice del grafo, según su terreno.
    """
    nombres = 'segoeui,arial,dejavusans'             # se usa el primero que exista en la computadora
    fuentes = {'titulo': pygame.font.SysFont(nombres, 26, bold=True),
               'normal': pygame.font.SysFont(nombres, 17),
               'negrita': pygame.font.SysFont(nombres, 17, bold=True),
               'chica': pygame.font.SysFont(nombres, 14),
               'formula': pygame.font.SysFont(nombres, 16, bold=True)}
    # Los números de los vértices se preparan una sola vez: escribir cientos de textos
    # nuevos en cada cuadro haría lenta la ventana.
    fuentes['costos'] = {terreno: fuentes['chica'].render(str(costo), True, NEGRO)
                         for terreno, costo in COSTOS.items()}
    return fuentes


def principal():
    """Abre la ventana y atiende al usuario hasta que la cierre.

    En cada vuelta del ciclo se hacen tres cosas: atender el ratón y el teclado,
    avanzar la animación y volver a dibujar todo.
    """
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption('MazeRunner, fase 2: mapa editable')
    fuentes = crear_fuentes()
    estado = crear_estado()
    reloj = pygame.time.Clock()
    teclas_de_pincel = {tecla: pincel for pincel, nombre, tecla in PINCELES}

    abierta = True
    while abierta:
        segundos = reloj.tick(60) / 1000             # espera para ir a 60 cuadros por segundo; da el tiempo que pasó

        # 1. Atender lo que hizo el usuario.
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                abierta = False
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button in (1, 3):
                atender_clic(estado, evento.pos, evento.button)
            elif evento.type == pygame.MOUSEMOTION and evento.pos[0] < ANCHO_MAPA:
                # Arrastrar con un botón oprimido sigue pintando o borrando.
                if evento.buttons[0]:
                    atender_clic(estado, evento.pos, 1, arrastrando=True)
                elif evento.buttons[2]:
                    atender_clic(estado, evento.pos, 3, arrastrando=True)
            elif evento.type == pygame.KEYDOWN:
                if evento.key in teclas_de_pincel:
                    estado['pincel'] = teclas_de_pincel[evento.key]
                elif evento.key == pygame.K_SPACE:
                    hacer_accion(estado, 'animar')
                elif evento.key == pygame.K_v:
                    hacer_accion(estado, 'velocidad')
                elif evento.key == pygame.K_g:
                    hacer_accion(estado, 'vista')
                elif evento.key == pygame.K_l:
                    hacer_accion(estado, 'limpiar')
                elif evento.key == pygame.K_r:
                    hacer_accion(estado, 'ejemplo')

        # 2. Avanzar la animación: se muestran más casillas según el tiempo que pasó.
        if estado['avance'] is not None:
            estado['avance'] += VELOCIDADES[estado['velocidad']][1] * segundos
            if estado['avance'] >= len(estado['resultados'][estado['elegido']]['exploradas']):
                estado['avance'] = None              # terminó: se muestra el resultado completo con su ruta

        # 3. Dibujar todo y mostrarlo.
        dibujar_mapa(pantalla, estado, fuentes)
        dibujar_panel(pantalla, estado, fuentes)
        pygame.display.flip()                        # pasa a la ventana lo que se acaba de dibujar

    pygame.quit()


if __name__ == '__main__':
    principal()
