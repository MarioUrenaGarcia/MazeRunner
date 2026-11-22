"""Maze Runner: juegos y modo de aprendizaje con algoritmos de búsqueda en grafos.

Proyecto de matemáticas discretas, fase 3. Un solo programa con portada, menú
y siete modos. En todos compiten los cinco algoritmos de la fase 1: BFS, DFS,
Dijkstra, la búsqueda voraz y A*. El tablero se ve desde arriba e inclinado.

    Atrapa gemas         Cada competidor corre en su propio tablero de 9 x 9,
                         todos idénticos, y recoge las mismas 8 gemas en el
                         mismo orden, una a la vez. Gana quien termine primero.
    Captura la bandera   En un tablero de 17 x 11, hay que robar la bandera del
                         rival y llevarla a donde está la propia. A tres puntos.
    Maze Runner          Un laberinto de 21 x 31 casillas, el mismo para todos,
                         que cambia cada 3 segundos. Gana quien llegue primero
                         a la salida.
    Mirar                Una versión de cada juego en la que compiten solo los
                         algoritmos y se puede acercar y mover la vista.
    Aprender             Un algoritmo paso a paso, con su código, su estructura
                         de datos dibujada y una tabla que compara a los cinco.

Reglas comunes:
    - Entrar a llano cuesta 1, a bosque 3 y a agua 5. En los juegos ese costo
      es tiempo: cruzar agua tarda cinco veces más que cruzar llano. Por eso
      la ruta más barata es también la más rápida.
    - El jugador avanza a 5.0 casillas por segundo y los rivales a 4.4
      (4.3 en captura la bandera).
    - Cada vez que un rival planea una ruta se queda quieto pensando 0.008
      segundos por cada casilla que exploró (la mitad en Maze Runner). El que
      explora de más pierde tiempo.
    - El terreno cambia durante la partida y nunca encierra a nadie.
    - Siempre se ve dibujada la ruta que planea cada rival.

Controles al jugar:
    Flechas o W A S D    mover al personaje, casilla por casilla
    C                    acercar la vista al personaje, o regresarla
    R                    reiniciar la partida
    Espacio o Enter      otra partida, cuando ya terminó
    Esc                  regresar al menú
    1 a 6                elegir rival en captura la bandera

Controles al solo mirar:
    Rueda del ratón      acercar y alejar
    Arrastrar, W A S D   mover la vista
    Tab                  pasar a seguir a otro personaje
    0                    volver a la vista general

Para ejecutarlo:  python fase3_juegos.py
"""

import heapq                              # cola de prioridad: siempre entrega el elemento más pequeño
import random                             # gemas, banderas, terrenos y laberintos distintos en cada partida
from collections import deque             # cola: se saca por un extremo y se mete por el otro
from math import ceil, cos, hypot, pi, radians, sin

import pygame                             # ventana, dibujo, teclado y ratón

# ============================================================================
# 1. EL MAPA Y LOS ALGORITMOS
# Es la misma lógica del notebook de la fase 1.
# ============================================================================

# Costo de entrar a cada tipo de terreno. Los muros no aparecen porque no se pueden pisar.
COSTOS = {'.': 1, 'B': 3, 'A': 5}

# Los 4 movimientos permitidos como (cambio de fila, cambio de columna).
MOVIMIENTOS = [(-1, 0), (0, 1), (1, 0), (0, -1)]   # arriba, derecha, abajo, izquierda


def vecinos(mapa, casilla):
    """Da las casillas a las que se puede pasar desde una casilla. Son las aristas del grafo.

    Entradas:
        mapa:    diccionario con 'terreno', 'filas' y 'columnas'
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
        casilla = padres[casilla]
    ruta.reverse()                    # se armó de la meta al inicio; se voltea
    return ruta


def estimacion(casilla, meta):
    """Estima cuánto falta para llegar a la meta: la distancia en casillas, sin diagonales.

    Entradas: dos casillas (fila, columna).
    Salida:   cuántas filas faltan más cuántas columnas faltan.
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
                cola.append(vecina)

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
    vistas = set()

    while pila:
        actual = pila.pop()              # sale la última que entró
        if actual in vistas:             # una casilla puede estar repetida en la pila: se ignora
            continue
        vistas.add(actual)
        exploradas.append(actual)
        if actual == meta:
            return reconstruir_ruta(padres, meta), exploradas
        # Se meten al revés para que la primera en salir sea la de arriba.
        for vecina, costo in reversed(vecinos(mapa, actual)):
            if vecina not in vistas:
                padres[vecina] = actual
                pila.append(vecina)

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
        if actual in vistas:
            continue
        vistas.add(actual)
        exploradas.append(actual)
        if actual == meta:
            return reconstruir_ruta(padres, meta), exploradas
        for vecina, paso in vecinos(mapa, actual):
            nuevo = costo + paso                 # costo de llegar a la vecina pasando por la actual
            if vecina not in costos or nuevo < costos[vecina]:
                costos[vecina] = nuevo
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
            nuevo = costos[actual] + paso        # lo gastado para llegar a la vecina
            if vecina not in costos or nuevo < costos[vecina]:
                costos[vecina] = nuevo
                padres[vecina] = actual
                distancia = estimacion(vecina, meta)
                heapq.heappush(cola, (nuevo + distancia, distancia, vecina))

    return None, exploradas


# Los cinco algoritmos con su nombre.
ALGORITMOS = {'BFS': bfs, 'DFS': dfs, 'Dijkstra': dijkstra, 'Voraz': voraz, 'A*': a_estrella}


def alcanzables(mapa, origen):
    """Da todas las casillas a las que se puede llegar desde una casilla.

    Entradas: el mapa y la casilla de origen.
    Salida:   un conjunto de casillas.

    Usa BFS con una meta que no existe: así explora todo lo alcanzable antes de rendirse.
    """
    ruta, exploradas = bfs(mapa, origen, None)
    return set(exploradas)


# ============================================================================
# 2. TERRENO SORTEADO
# Los tableros empiezan vacíos. El terreno se sortea en manchas de dos casillas
# contiguas: 5 de muro, 5 de árboles y 5 de agua.
# ============================================================================

# Una letra por mancha: 5 muros, 5 bosques y 5 charcos.
MANCHAS = '#' * 5 + 'B' * 5 + 'A' * 5
DURACION_DEL_CAMBIO = 0.6                # segundos que tarda en verse un cambio de terreno


def mapa_vacio(filas, columnas):
    """Crea un mapa de puro llano.

    Entradas: el número de filas y de columnas.
    Salida:   diccionario con 'terreno', 'filas' y 'columnas'.
    """
    return {'terreno': {(f, c): '.' for f in range(filas) for c in range(columnas)},
            'filas': filas, 'columnas': columnas}


def junto_a(casilla):
    """Da una casilla y sus cuatro vecinas, sin fijarse en muros ni en bordes.

    Entrada: la casilla (fila, columna).
    Salida:  lista de 5 casillas. Sirve para apartar el terreno de un personaje.
    """
    f, c = casilla
    return [(f, c)] + [(f + df, c + dc) for df, dc in MOVIMIENTOS]


def sortear_terreno(filas, columnas, prohibidas, conectadas, espejo=False):
    """Sortea el terreno de un tablero: 5 muros, 5 árboles y 5 charcos, en manchas de dos.

    Entradas:
        filas, columnas: el tamaño del tablero
        prohibidas:      casillas donde no puede caer terreno (gemas, banderas,
                         salidas y lo que está junto a los personajes)
        conectadas:      casillas que deben seguir comunicadas entre sí
        espejo:          si es True, las manchas se sortean en la mitad izquierda
                         y se copian reflejadas en la derecha; la columna del
                         centro queda libre. Son 5, 5 y 5 en cada mitad.

    Salida: el mapa. Se repite el sorteo hasta que todas las casillas de
            'conectadas' queden comunicadas. Si no se logra, devuelve el tablero vacío.
    """
    ultima = columnas // 2 - 1 if espejo else columnas - 1      # última columna donde se sortea

    def reflejo(casilla):
        """La casilla que queda del otro lado, a la misma distancia del centro."""
        return (casilla[0], columnas - 1 - casilla[1])

    vedadas = set(prohibidas)
    if espejo:
        # Una casilla prohibida en la derecha prohíbe también a su pareja de la izquierda.
        vedadas |= {reflejo(casilla) for casilla in prohibidas}

    for intento in range(400):
        mapa = mapa_vacio(filas, columnas)
        terreno = mapa['terreno']
        completo = True
        for tipo in MANCHAS:
            # Se busca dónde quepa una mancha: una casilla y una de sus vecinas, las dos libres.
            for prueba in range(80):
                f, c = random.randrange(filas), random.randrange(ultima + 1)
                df, dc = random.choice(MOVIMIENTOS)
                par = [(f, c), (f + df, c + dc)]
                if all(0 <= x < filas and 0 <= y <= ultima and (x, y) not in vedadas and terreno[(x, y)] == '.'
                       for x, y in par):
                    for casilla in par:
                        terreno[casilla] = tipo
                        if espejo:
                            terreno[reflejo(casilla)] = tipo
                    break
            else:
                completo = False                     # no cupo esta mancha: se descarta el intento
                break
        # Sirve si cupieron todas las manchas y nadie quedó encerrado.
        if completo and set(conectadas) <= alcanzables(mapa, conectadas[0]):
            return mapa

    return mapa_vacio(filas, columnas)


# ============================================================================
# 3. LOS CORREDORES
# Un corredor es cualquier personaje: el jugador o un rival.
# ============================================================================

VELOCIDAD_JUGADOR = 5.0                  # casillas de llano por segundo
VELOCIDAD_RIVAL = 4.4
VELOCIDAD_RIVAL_BANDERA = 4.3            # en captura la bandera el rival va un poco más lento
SEGUNDOS_DE_PENSAR = 0.008               # por cada casilla que el rival exploró al planear su ruta
CUENTA_REGRESIVA = 3.0                   # segundos antes de arrancar

ROJO = (198, 40, 40)
NEGRO = (20, 20, 20)
BLANCO = (250, 250, 250)
GRIS = (150, 150, 150)
GRIS_OSCURO = (48, 48, 48)
DORADO = (255, 193, 7)
VERDE_INICIO = (0, 200, 83)

# El color de cada competidor: el jugador rojo, BFS ámbar, DFS turquesa,
# Dijkstra azul, Voraz violeta y A* carbón.
COLOR_DE = {'Tú': ROJO, 'BFS': (255, 179, 0), 'DFS': (0, 191, 178), 'Dijkstra': (41, 121, 255),
            'Voraz': (156, 77, 204), 'A*': (58, 62, 70)}


def crear_corredor(nombre, casilla, algoritmo=None, velocidad=VELOCIDAD_RIVAL, color=None):
    """Crea un personaje.

    Entradas:
        nombre:    'Tú' para el jugador o el nombre de un algoritmo
        casilla:   la casilla donde empieza
        algoritmo: la función de búsqueda con la que se mueve; None para el jugador
        velocidad: casillas de llano que recorre por segundo
        color:     su color; si no se da, el que le toca por su nombre

    Salida: un diccionario con
        'nombre', 'color', 'algoritmo', 'velocidad'
        'casilla':   la casilla en la que está
        'destino':   la casilla vecina hacia la que camina, o None si está quieto
        'avance':    cuánto lleva del paso actual, de 0 a 1
        'duracion':  cuántos segundos dura el paso actual
        'sobra':     segundos que sobraron al llegar a una casilla; se usan en el paso siguiente
        'zancadas':  cuántos pasos ha dado; sirve para alternar las piernas al dibujarlo
        'mira':      hacia dónde ve: 1 a la derecha y -1 a la izquierda
        'brillo':    segundos que le quedan de brillar por haber recogido algo
        'final':     en qué momento terminó la carrera, o None
        Y, para los rivales:
        'ruta':      las casillas que le faltan por recorrer
        'objetivo':  la casilla hacia la que planeó su ruta
        'pensando':  segundos que le faltan de estar quieto pensando
        'replanear': True si el terreno cambió y tiene que planear de nuevo
        'pasos':     cuántos pasos ha dado desde que planeó
        'planes':    cuántas veces ha planeado en la partida
    """
    return {'nombre': nombre, 'color': color or COLOR_DE[nombre], 'algoritmo': algoritmo, 'velocidad': velocidad,
            'casilla': casilla, 'destino': None, 'avance': 0.0, 'duracion': 0.0, 'sobra': 0.0,
            'zancadas': 0, 'mira': 1, 'brillo': 0.0, 'final': None,
            'ruta': [], 'objetivo': None, 'pensando': 0.0, 'replanear': False, 'pasos': 0, 'planes': 0}


def empezar_paso(corredor, mapa, vecina):
    """Hace que un corredor empiece a caminar hacia una casilla vecina.

    Entradas: el corredor, el mapa y la casilla vecina.
    Salida:   True si empezó a caminar; False si la casilla es muro o está fuera del mapa.
    """
    terreno = mapa['terreno'].get(vecina, '#')
    if terreno == '#':
        return False
    if vecina[1] != corredor['casilla'][1]:          # si cambia de columna, voltea hacia ese lado
        corredor['mira'] = 1 if vecina[1] > corredor['casilla'][1] else -1
    corredor['destino'] = vecina
    corredor['zancadas'] += 1
    # El costo del terreno se vuelve tiempo: a 5 casillas por segundo, el llano tarda
    # 0.2 segundos, el bosque 3 veces más y el agua 5 veces más.
    corredor['duracion'] = COSTOS[terreno] / corredor['velocidad']
    # El tiempo que sobró al llegar a la casilla anterior cuenta para este paso.
    # Sin esto se perdería una fracción de cuadro en cada casilla y la velocidad real sería menor.
    corredor['avance'] = min(corredor['sobra'] / corredor['duracion'], 0.99)
    corredor['sobra'] = 0.0
    return True


def avanzar(corredor, segundos):
    """Hace avanzar el paso que un corredor tiene en curso.

    Entradas: el corredor y los segundos que pasaron desde el cuadro anterior.
    Salida:   True si en este cuadro terminó de llegar a una casilla nueva.
    """
    corredor['brillo'] = max(0.0, corredor['brillo'] - segundos)
    if corredor['destino'] is None:
        corredor['sobra'] = 0.0                      # lleva quieto un cuadro: ya no hay tiempo sobrante
        return False
    corredor['avance'] += segundos / corredor['duracion']
    if corredor['avance'] >= 1:
        corredor['sobra'] = (corredor['avance'] - 1) * corredor['duracion']   # el tiempo que se pasó de la llegada
        corredor['casilla'] = corredor['destino']    # llegó: ahora está en esa casilla
        corredor['destino'] = None
        return True
    return False


def posicion(corredor):
    """Da la posición exacta de un corredor, aunque esté a medio paso.

    Entrada: el corredor.
    Salida:  el par (fila, columna) con decimales. Sirve para dibujarlo
             deslizándose entre casillas y para medir distancias.
    """
    f, c = corredor['casilla']
    if corredor['destino'] is None:
        return (f, c)
    fd, cd = corredor['destino']
    a = corredor['avance']
    return (f + (fd - f) * a, c + (cd - c) * a)


def distancia(a, b):
    """Distancia en línea recta entre dos posiciones (fila, columna), en casillas."""
    return hypot(a[0] - b[0], a[1] - b[1])


def conducir_rival(rival, mapa, objetivo, segundos, factor_de_pensar=1.0):
    """Mueve a un rival durante un cuadro: piensa, planea o da su siguiente paso.

    Entradas:
        rival:            el corredor
        mapa:             el mapa en el que está
        objetivo:         la casilla a la que quiere llegar
        segundos:         el tiempo que pasó desde el cuadro anterior
        factor_de_pensar: por cuánto se multiplica su tiempo de pensar

    El rival solo vuelve a planear cuando cambia su objetivo o cuando cambió el
    terreno. Cada vez que planea se queda quieto 0.008 segundos por cada
    casilla que exploró: el que explora de más pierde tiempo.
    """
    if rival['pensando'] > 0:                        # sigue quieto, pensando
        rival['pensando'] -= segundos
        return
    if rival['destino'] is not None:                 # va a medio paso: lo termina antes de decidir
        return

    cambio_de_objetivo = rival['objetivo'] != objetivo
    # Cuando el objetivo se mueve (persigue a alguien), se le pide dar al menos un paso
    # con cada plan. Si no, se quedaría pensando para siempre sin avanzar.
    puede = rival['pasos'] >= 1 or not rival['ruta']
    if rival['replanear'] or (cambio_de_objetivo and puede):
        ruta, exploradas = rival['algoritmo'](mapa, rival['casilla'], objetivo)
        rival['ruta'] = ruta[1:] if ruta else []     # sin la primera casilla, que es donde ya está
        rival['objetivo'] = objetivo
        rival['replanear'] = False
        rival['pasos'] = 0
        rival['planes'] += 1
        rival['pensando'] = SEGUNDOS_DE_PENSAR * len(exploradas) * factor_de_pensar
        return

    if rival['ruta']:
        if empezar_paso(rival, mapa, rival['ruta'][0]):
            rival['ruta'].pop(0)
            rival['pasos'] += 1
        else:
            rival['replanear'] = True                # la ruta ya no sirve: planea otra


def mover_jugador(jugador, mapa, direcciones):
    """Empieza un paso del jugador si está quieto y tiene una dirección oprimida.

    Entradas:
        jugador:     el corredor del jugador
        mapa:        el mapa
        direcciones: lista de movimientos (df, dc) oprimidos, del más viejo al más reciente

    Mientras se mantiene una dirección, el jugador avanza casilla por casilla.
    """
    if jugador['destino'] is not None:
        return
    # Se prueba primero la tecla más reciente. Si esa choca con un muro, se prueban las demás.
    for df, dc in reversed(direcciones):
        f, c = jugador['casilla']
        if empezar_paso(jugador, mapa, (f + df, c + dc)):
            return


def crear_camara():
    """Crea la cámara de una partida: qué tanto se acerca la vista y a quién sigue.

    Salida: diccionario con
        'zoom':    1.0 es el tablero completo; más grande es más cerca
        'centro':  la posición (fila, columna) que queda al centro, o None para centrar el tablero
        'seguir':  el número del corredor al que sigue la vista, o None
        'libre':   True si la vista se movió a mano y ya no sigue al corredor
        'casilla_px': ancho y alto de una casilla en pantalla; sirve para arrastrar la vista
    """
    return {'zoom': 1.0, 'centro': None, 'seguir': None, 'libre': False, 'casilla_px': (40, 30)}


def anotar_evento(juego, tipo, quien, tablero=0):
    """Deja anotado algo que pasó en la partida, para que el dibujo le ponga un efecto.

    Entradas:
        juego:   la partida
        tipo:    'recoger' (tomó una gema o una bandera), 'punto' (anotó) o 'victoria' (terminó o ganó)
        quien:   el corredor al que le pasó
        tablero: en qué tablero ocurrió (en atrapa gemas hay uno por competidor)

    La lógica del juego solo anota; las partículas y los fuegos artificiales los hace el dibujo.
    """
    juego['eventos'].append({'tipo': tipo, 'quien': quien, 'tablero': tablero})
    del juego['eventos'][:-40]                       # si nadie los dibuja, no se acumulan sin fin
    if tipo == 'recoger':
        quien['brillo'] = 0.9                        # quien recoge algo brilla un momento


# ============================================================================
# 4. ATRAPA GEMAS
# ============================================================================

LADO_GEMAS = 9                           # cada tablero mide 9 x 9
CANTIDAD_DE_GEMAS = 8
SALIDA_GEMAS = (0, 0)                    # la esquina superior izquierda
DISTANCIA_ENTRE_GEMAS = 5                # cada gema aparece al menos a 5 casillas de la anterior
RADIO_DE_RECOGER = 0.5                   # la gema se recoge al estar a menos de media casilla


def crear_gemas(con_jugador=True):
    """Prepara una partida de atrapa gemas.

    Entrada: con_jugador es True para jugar y False para solo mirar a los cinco algoritmos.

    Salida: un diccionario con
        'tipo':       'gemas'
        'gemas':      la secuencia de 8 casillas, sorteada una vez e igual para todos
        'mapas':      8 terrenos, uno por gema, sorteados una vez e iguales para todos
        'corredores': los competidores. Cada uno lleva además 'siguiente' (cuántas
                      gemas ha recogido) y 'cambio' (segundos desde que cambió su terreno)
        'jugador':    el corredor del jugador, o None al solo mirar
        'reloj':      segundos de carrera
        'cuenta':     segundos que faltan de la cuenta regresiva
        'fase':       'cuenta' o 'carrera'
        'anuncio':    True cuando ya se anunció el resultado
        'camara':     la cámara de la partida
        'eventos':    lo que acaba de pasar, para los efectos
        'adornos':    los adornos de cada tablero, distintos en cada uno
    """
    gemas = []
    mapas = []
    previa = SALIDA_GEMAS
    for numero in range(CANTIDAD_DE_GEMAS):
        # La gema se sortea entre las casillas que están lejos de la anterior, sin diagonales.
        lejanas = [(f, c) for f in range(LADO_GEMAS) for c in range(LADO_GEMAS)
                   if estimacion((f, c), previa) >= DISTANCIA_ENTRE_GEMAS]
        gema = random.choice(lejanas)
        # El terreno de esta gema. Cuando aparece, cada competidor está parado en la gema
        # anterior (o en la salida): ahí y alrededor no cae nada, ni tampoco sobre la gema.
        mapas.append(sortear_terreno(LADO_GEMAS, LADO_GEMAS, [gema] + junto_a(previa), [previa, gema]))
        gemas.append(gema)
        previa = gema

    nombres = (['Tú'] if con_jugador else []) + list(ALGORITMOS)
    corredores = []
    for nombre in nombres:
        if nombre == 'Tú':
            corredor = crear_corredor('Tú', SALIDA_GEMAS, velocidad=VELOCIDAD_JUGADOR)
        else:
            corredor = crear_corredor(nombre, SALIDA_GEMAS, ALGORITMOS[nombre], VELOCIDAD_RIVAL)
        corredor.update({'siguiente': 0, 'cambio': 0.0})
        corredores.append(corredor)

    return {'tipo': 'gemas', 'gemas': gemas, 'mapas': mapas, 'corredores': corredores,
            'jugador': corredores[0] if con_jugador else None,
            'reloj': 0.0, 'cuenta': CUENTA_REGRESIVA, 'fase': 'cuenta', 'anuncio': False,
            'camara': crear_camara(), 'eventos': [],
            'adornos': [crear_adornos(LADO_GEMAS, LADO_GEMAS) for corredor in corredores]}


def mapa_de(juego, corredor):
    """Da el terreno que le toca ver a un competidor de atrapa gemas.

    Entradas: la partida y el corredor.
    Salida:   el mapa de la gema que ese corredor está buscando. Por eso el
              terreno de su tablero cambia cada vez que toma una gema.
    """
    return juego['mapas'][min(corredor['siguiente'], CANTIDAD_DE_GEMAS - 1)]


def actualizar_gemas(juego, segundos, direcciones):
    """Avanza un cuadro de atrapa gemas.

    Entradas:
        juego:       el diccionario de la partida
        segundos:    el tiempo que pasó desde el cuadro anterior
        direcciones: las direcciones que el jugador tiene oprimidas
    """
    for corredor in juego['corredores']:
        corredor['cambio'] += segundos               # el terreno se ve crecer también durante la cuenta regresiva
    if juego['fase'] == 'cuenta':
        juego['cuenta'] -= segundos
        if juego['cuenta'] <= 0:
            juego['fase'] = 'carrera'
        return

    juego['reloj'] += segundos
    for numero, corredor in enumerate(juego['corredores']):
        if corredor['final'] is not None:
            continue                                 # ya terminó: se queda en su tablero
        avanzar(corredor, segundos)

        # La gema se recoge al estar a menos de media casilla de ella.
        if distancia(posicion(corredor), juego['gemas'][corredor['siguiente']]) < RADIO_DE_RECOGER:
            corredor['siguiente'] += 1               # con esto su tablero pasa al terreno de la gema que sigue
            corredor['cambio'] = 0.0                 # empieza a verse el cambio de terreno
            corredor['objetivo'] = None              # el rival tendrá que planear hacia la gema nueva
            corredor['ruta'] = []
            anotar_evento(juego, 'recoger', corredor, numero)
            if corredor['siguiente'] == CANTIDAD_DE_GEMAS:
                corredor['final'] = juego['reloj']
                anotar_evento(juego, 'victoria', corredor, numero)
                continue

        mapa = mapa_de(juego, corredor)
        if corredor['algoritmo'] is None:
            mover_jugador(corredor, mapa, direcciones)
        else:
            conducir_rival(corredor, mapa, juego['gemas'][corredor['siguiente']], segundos)

    # El resultado se anuncia cuando termina el jugador. Al solo mirar, cuando llega el primero.
    # Los demás siguen corriendo.
    if juego['jugador'] is not None:
        juego['anuncio'] = juego['jugador']['final'] is not None
    else:
        juego['anuncio'] = any(c['final'] is not None for c in juego['corredores'])


def clasificacion(juego):
    """Ordena a los competidores de una carrera del primero al último.

    Entrada: la partida de atrapa gemas o de Maze Runner.
    Salida:  la lista de corredores ordenada.
        En atrapa gemas: primero quien ya terminó (por su tiempo), luego quien
        lleva más gemas y luego quien está más cerca de su siguiente gema.
        En Maze Runner: primero quien ya salió y luego quien está más cerca de la salida.
    """
    def orden(corredor):
        """La clave para ordenar: mientras más chica, mejor lugar."""
        if corredor['final'] is not None:
            return (0, corredor['final'], 0)
        if juego['tipo'] == 'laberinto':
            return (1, 0, juego['distancias'].get(corredor['destino'] or corredor['casilla'], 9999))
        falta = distancia(posicion(corredor), juego['gemas'][corredor['siguiente']])
        return (1, -corredor['siguiente'], falta)

    return sorted(juego['corredores'], key=orden)


# ============================================================================
# 5. CAPTURA LA BANDERA
# ============================================================================

FILAS_BANDERA, COLUMNAS_BANDERA = 11, 17
SALIDA_IZQUIERDA = (FILAS_BANDERA // 2, 0)                       # centro del borde izquierdo
SALIDA_DERECHA = (FILAS_BANDERA // 2, COLUMNAS_BANDERA - 1)      # centro del borde derecho
PUNTOS_PARA_GANAR = 3
POSICIONES_DE_BANDERA = 16               # largo de la secuencia de posiciones de la bandera
DISTANCIA_A_LA_SALIDA = 3                # la bandera aparece al menos a 3 casillas de la salida
DISTANCIA_DE_CHOQUE = 0.6                # en casillas: más cerca que esto, chocan
OPCIONES_DE_RIVAL = list(ALGORITMOS) + ['Azar']                  # se eligen con las teclas 1 a 6


def reflejo_bandera(casilla):
    """Da la casilla espejo en el tablero de captura la bandera: la misma fila, del otro lado."""
    return (casilla[0], COLUMNAS_BANDERA - 1 - casilla[1])


def crear_bandera(eleccion='A*', izquierda=None):
    """Prepara una partida de captura la bandera.

    Entradas:
        eleccion:  el rival del lado derecho: el nombre de un algoritmo o 'Azar'
        izquierda: None para jugar. Para solo mirar, el nombre del algoritmo que
                   juega del lado izquierdo; conserva el color rojo.

    Salida: un diccionario con
        'tipo':      'bandera'
        'eleccion':  lo que se eligió como rival; con 'Azar', el rival cambia tras cada punto
        'humano':    True si el lado izquierdo lo maneja una persona
        'mapa':      el terreno actual, siempre en espejo
        'mapa_viejo' y 'cambio': el terreno anterior y los segundos desde que cambió
        'secuencia': 16 posiciones para la bandera del lado izquierdo, sorteadas al
                     empezar. La del lado derecho está siempre en la casilla espejo.
        'turno':     qué posición de la secuencia toca; avanza con cada punto y cada choque
        'jugador':   el corredor del lado izquierdo
        'rival':     el corredor del lado derecho
                     Los dos llevan además 'salida', 'lleva' (True si carga la
                     bandera del otro) y 'puntos'.
        'corredores': los dos, en una lista
        'reloj', 'cuenta', 'fase' ('cuenta', 'carrera' o 'final')
        'pausa':     segundos de pausa tras un choque
        'aviso':     texto que se muestra un momento, y 'aviso_resta' los segundos que le quedan
        'camara', 'eventos', 'adornos'
    """
    # La bandera de la izquierda va en su mitad: lejos de su salida y fuera de las tres columnas centrales.
    centro = COLUMNAS_BANDERA // 2
    posibles = [(f, c) for f in range(FILAS_BANDERA) for c in range(centro - 1)
                if estimacion((f, c), SALIDA_IZQUIERDA) >= DISTANCIA_A_LA_SALIDA]
    secuencia = [random.choice(posibles) for numero in range(POSICIONES_DE_BANDERA)]

    nombre = random.choice(list(ALGORITMOS)) if eleccion == 'Azar' else eleccion
    if izquierda is None:
        jugador = crear_corredor('Tú', SALIDA_IZQUIERDA, velocidad=VELOCIDAD_JUGADOR)
    else:
        jugador = crear_corredor(izquierda, SALIDA_IZQUIERDA, ALGORITMOS[izquierda], VELOCIDAD_RIVAL_BANDERA, color=ROJO)
    rival = crear_corredor(nombre, SALIDA_DERECHA, ALGORITMOS[nombre], VELOCIDAD_RIVAL_BANDERA)
    jugador.update({'salida': SALIDA_IZQUIERDA, 'lleva': False, 'puntos': 0, 'mira': 1})
    rival.update({'salida': SALIDA_DERECHA, 'lleva': False, 'puntos': 0, 'mira': -1})

    juego = {'tipo': 'bandera', 'eleccion': eleccion, 'humano': izquierda is None,
             'mapa': mapa_vacio(FILAS_BANDERA, COLUMNAS_BANDERA), 'mapa_viejo': None, 'cambio': 0.0,
             'secuencia': secuencia, 'turno': 0, 'jugador': jugador, 'rival': rival, 'corredores': [jugador, rival],
             'reloj': 0.0, 'cuenta': CUENTA_REGRESIVA, 'fase': 'cuenta',
             'pausa': 0.0, 'aviso': '', 'aviso_resta': 0.0, 'camara': crear_camara(), 'eventos': [],
             'adornos': crear_adornos(FILAS_BANDERA, COLUMNAS_BANDERA)}
    cambiar_terreno(juego)                           # el terreno cambia al empezar
    return juego


def bandera_de(juego, corredor):
    """Da la casilla donde está la bandera de un personaje cuando nadie la carga.

    Entradas: la partida y el corredor dueño de la bandera.
    Salida:   la casilla. La del lado izquierdo sale de la secuencia; la del derecho es su espejo.
    """
    mia = juego['secuencia'][juego['turno'] % POSICIONES_DE_BANDERA]     # al acabarse la secuencia, vuelve a empezar
    return mia if corredor is juego['jugador'] else reflejo_bandera(mia)


def cambiar_terreno(juego):
    """Sortea un terreno nuevo para captura la bandera.

    Entrada: la partida; se reemplaza su mapa.

    El terreno nunca cae sobre una salida ni una bandera, ni encima o junto a un
    personaje, y siempre deja comunicadas las salidas, las banderas y los personajes.
    """
    jugador, rival = juego['jugador'], juego['rival']
    fijas = [SALIDA_IZQUIERDA, SALIDA_DERECHA, bandera_de(juego, jugador), bandera_de(juego, rival)]
    # Donde está cada personaje: su casilla y, si va a medio paso, la casilla a la que entra.
    personajes = [casilla for corredor in (jugador, rival)
                  for casilla in (corredor['casilla'], corredor['destino']) if casilla is not None]
    prohibidas = fijas + [cerca for casilla in personajes for cerca in junto_a(casilla)]
    juego['mapa_viejo'] = juego['mapa']              # se guarda el anterior para dibujar la transformación
    juego['cambio'] = 0.0
    juego['mapa'] = sortear_terreno(FILAS_BANDERA, COLUMNAS_BANDERA, prohibidas, fijas + personajes, espejo=True)
    jugador['replanear'] = True                      # con terreno nuevo, los que se mueven solos vuelven a planear
    rival['replanear'] = True


def avisar(juego, texto, segundos=1.6):
    """Muestra un aviso en pantalla durante un momento.

    Entradas: la partida, el texto y cuántos segundos se muestra.
    """
    juego['aviso'] = texto
    juego['aviso_resta'] = segundos


def objetivo_de(juego, quien, otro):
    """Decide a dónde quiere ir un personaje automático de captura la bandera.

    Entradas: la partida, el corredor que decide y su contrincante.
    Salida:   una casilla.
        Si lleva la bandera del otro, va a donde está la suya para anotar.
        Si el otro lleva la suya, lo persigue: su objetivo es la casilla del otro.
        Si nadie lleva nada, va a robar la bandera del otro.
    """
    if quien['lleva']:
        return bandera_de(juego, quien)
    if otro['lleva']:
        return otro['destino'] or otro['casilla']
    return bandera_de(juego, otro)


def objetivo_del_rival(juego):
    """Da el objetivo del lado derecho. Es objetivo_de visto desde el rival."""
    return objetivo_de(juego, juego['rival'], juego['jugador'])


def nombre_para_aviso(juego, corredor):
    """Da el nombre con el que se menciona a un personaje en los avisos."""
    if corredor is juego['jugador'] and not juego['humano']:
        return corredor['nombre'] + ' (rojo)'
    return corredor['nombre']


def revisar_banderas(juego, quien, otro):
    """Revisa si un personaje roba una bandera o anota, según la casilla que pisa.

    Entradas:
        juego: la partida
        quien: el corredor que se revisa
        otro:  su contrincante
    """
    if quien['destino'] is not None:
        return                                       # va a medio paso: todavía no pisa la casilla
    es_humano = quien is juego['jugador'] and juego['humano']
    if not quien['lleva'] and quien['casilla'] == bandera_de(juego, otro):
        quien['lleva'] = True                        # pisó la bandera del otro: se la roba
        cambiar_terreno(juego)                       # el terreno cambia cuando alguien roba
        anotar_evento(juego, 'recoger', quien)
        if not es_humano:
            dueño = 'tu bandera' if juego['humano'] else 'la bandera de ' + nombre_para_aviso(juego, otro)
            avisar(juego, f'{nombre_para_aviso(juego, quien)} robó {dueño}')
    elif quien['lleva'] and quien['casilla'] == bandera_de(juego, quien):
        quien['puntos'] += 1                         # pisó su propia bandera cargando la del otro: punto
        quien['lleva'] = False
        otro['lleva'] = False                        # quien cargaba una bandera la pierde
        if quien['puntos'] >= PUNTOS_PARA_GANAR:
            quien['final'] = juego['reloj']          # con esto se queda bailando
            juego['fase'] = 'final'
            anotar_evento(juego, 'victoria', quien)
            return
        anotar_evento(juego, 'punto', quien)
        juego['turno'] += 1                          # las dos banderas saltan a la siguiente posición
        rival = juego['rival']
        if juego['eleccion'] == 'Azar':
            # En Azar, el rival cambia de algoritmo después de cada punto.
            nombre = random.choice([n for n in ALGORITMOS if n != rival['nombre']])
            rival.update({'nombre': nombre, 'algoritmo': ALGORITMOS[nombre], 'color': COLOR_DE[nombre]})
        cambiar_terreno(juego)                       # el terreno cambia cuando alguien anota
        avisar(juego, 'Punto para ti' if es_humano else f'Punto para {nombre_para_aviso(juego, quien)}')


def actualizar_bandera(juego, segundos, direcciones):
    """Avanza un cuadro de captura la bandera.

    Entradas:
        juego:       el diccionario de la partida
        segundos:    el tiempo que pasó desde el cuadro anterior
        direcciones: las direcciones que el jugador tiene oprimidas
    """
    juego['aviso_resta'] = max(0.0, juego['aviso_resta'] - segundos)
    juego['cambio'] += segundos
    if juego['fase'] == 'cuenta':
        juego['cuenta'] -= segundos
        if juego['cuenta'] <= 0:
            juego['fase'] = 'carrera'
        return
    if juego['fase'] == 'final':
        return
    if juego['pausa'] > 0:                           # tras un choque, un momento de espera
        juego['pausa'] -= segundos
        return

    juego['reloj'] += segundos
    jugador, rival = juego['jugador'], juego['rival']

    avanzar(jugador, segundos)
    avanzar(rival, segundos)
    revisar_banderas(juego, jugador, rival)
    if juego['fase'] == 'carrera':
        revisar_banderas(juego, rival, jugador)
    if juego['fase'] == 'final':
        return

    # Choque: solo cuenta si alguno lleva una bandera. Los dos regresan a su salida, sueltan
    # lo que llevaban, y las banderas y el terreno cambian de lugar.
    if (jugador['lleva'] or rival['lleva']) and distancia(posicion(jugador), posicion(rival)) < DISTANCIA_DE_CHOQUE:
        for corredor in (jugador, rival):
            corredor.update({'casilla': corredor['salida'], 'destino': None, 'lleva': False,
                             'ruta': [], 'objetivo': None, 'pensando': 0.0})
        juego['turno'] += 1
        cambiar_terreno(juego)
        juego['pausa'] = 0.8
        avisar(juego, 'Choque: los dos regresan a su salida')
        return

    if juego['humano']:
        mover_jugador(jugador, juego['mapa'], direcciones)
    else:
        conducir_rival(jugador, juego['mapa'], objetivo_de(juego, jugador, rival), segundos)
    conducir_rival(rival, juego['mapa'], objetivo_de(juego, rival, jugador), segundos)


# ============================================================================
# 6. MAZE RUNNER
# Un laberinto de 10 x 15 celdas. Entre celda y celda hay una casilla que es
# pasillo (abierta) o muro (cerrada), así que el tablero mide 21 x 31 casillas.
# ============================================================================

CELDAS_ALTO, CELDAS_ANCHO = 10, 15
FILAS_LABERINTO, COLUMNAS_LABERINTO = 2 * CELDAS_ALTO + 1, 2 * CELDAS_ANCHO + 1     # 21 x 31
PARTIDA_LABERINTO = (1, 1)                                       # la celda de la esquina superior izquierda
META_LABERINTO = (FILAS_LABERINTO - 2, COLUMNAS_LABERINTO - 2)   # la celda de la esquina inferior derecha
PASILLOS_EXTRA = 22                      # pasillos que se abren de más, para que haya rutas alternativas
CELDAS_LENTAS = 15                       # 15 celdas con agua y 15 con bosque
SEGUNDOS_ENTRE_CAMBIOS = 3.0
PASILLOS_POR_CAMBIO = 8                  # en cada cambio se cierran hasta 8 y se abren tantos como se cerraron
FACTOR_DE_PENSAR_LABERINTO = 0.5         # en Maze Runner el tiempo de pensar es la mitad


def celdas_del_laberinto():
    """Da las casillas que son celdas del laberinto: las de fila y columna impares."""
    return [(2 * i + 1, 2 * j + 1) for i in range(CELDAS_ALTO) for j in range(CELDAS_ANCHO)]


def todo_conectado(terreno):
    """Dice si desde la partida se puede llegar a todas las celdas del laberinto.

    Entrada: el diccionario de terreno del laberinto.
    Salida:  True si el laberinto está completamente conectado.

    Recorre el laberinto de celda en celda: de una celda se pasa a la de al
    lado solo si la casilla que hay entre las dos está abierta.
    """
    vistas = {PARTIDA_LABERINTO}
    pendientes = [PARTIDA_LABERINTO]
    while pendientes:
        f, c = pendientes.pop()
        for df, dc in MOVIMIENTOS:
            entre = (f + df, c + dc)                 # la casilla que separa a las dos celdas
            vecina = (f + 2 * df, c + 2 * dc)
            if vecina not in vistas and terreno.get(entre, '#') != '#' and vecina in terreno:
                vistas.add(vecina)
                pendientes.append(vecina)
    return len(vistas) == CELDAS_ALTO * CELDAS_ANCHO


def costo_hasta(mapa, meta):
    """Calcula cuánto cuesta llegar a una casilla desde cada una de las demás.

    Entradas: el mapa y la casilla meta.
    Salida:   diccionario {casilla: costo de la ruta más barata hasta la meta}.

    Es Dijkstra corrido al revés, saliendo de la meta. Sirve para saber, en
    Maze Runner, quién está más cerca de la salida.
    """
    costos = {meta: 0}
    cola = [(0, meta)]
    while cola:
        costo, actual = heapq.heappop(cola)
        if costo > costos[actual]:
            continue
        # Para ir de una vecina a la actual hay que pagar lo que cuesta entrar a la actual.
        paso = COSTOS[mapa['terreno'][actual]]
        for vecina, costo_de_la_vecina in vecinos(mapa, actual):
            nuevo = costo + paso
            if vecina not in costos or nuevo < costos[vecina]:
                costos[vecina] = nuevo
                heapq.heappush(cola, (nuevo, vecina))
    return costos


def crear_laberinto(con_jugador=True):
    """Prepara una partida de Maze Runner.

    Entrada: con_jugador es True para jugar y False para solo mirar.

    Salida: un diccionario con
        'tipo':       'laberinto'
        'mapa':       el laberinto, el mismo para todos
        'pasillos':   todas las casillas que pueden ser pasillo o muro
        'corredores': los competidores, y 'jugador' el de la persona, o None
        'distancias': cuánto cuesta llegar a la salida desde cada casilla
        'proximo':    segundos que faltan para el siguiente cambio del laberinto
        'recientes':  los pasillos que cambiaron en el último cambio, y 'cambio' los segundos desde entonces
        'reloj', 'cuenta', 'fase', 'anuncio', 'camara', 'eventos', 'adornos'
    """
    terreno = {(f, c): '#' for f in range(FILAS_LABERINTO) for c in range(COLUMNAS_LABERINTO)}
    celdas = celdas_del_laberinto()
    for celda in celdas:
        terreno[celda] = '.'

    # 1. Un laberinto con un solo camino entre cada par de celdas. Se camina al azar
    #    abriendo paso hacia celdas no visitadas; al quedar sin salida, se regresa.
    visitadas = {PARTIDA_LABERINTO}
    camino = [PARTIDA_LABERINTO]
    while camino:
        f, c = camino[-1]
        opciones = [(df, dc) for df, dc in MOVIMIENTOS
                    if (f + 2 * df, c + 2 * dc) in terreno and (f + 2 * df, c + 2 * dc) not in visitadas]
        if not opciones:
            camino.pop()                             # callejón: se regresa una celda
            continue
        df, dc = random.choice(opciones)
        terreno[(f + df, c + dc)] = '.'              # se abre el pasillo entre las dos celdas
        visitadas.add((f + 2 * df, c + 2 * dc))
        camino.append((f + 2 * df, c + 2 * dc))

    # 2. Las casillas que separan dos celdas vecinas: las que pueden ser pasillo o muro.
    pasillos = [(f, c) for f in range(1, FILAS_LABERINTO - 1) for c in range(1, COLUMNAS_LABERINTO - 1)
                if (f + c) % 2 == 1]

    # 3. Se abren 22 pasillos de más, para que haya rutas alternativas.
    cerrados = [p for p in pasillos if terreno[p] == '#']
    for pasillo in random.sample(cerrados, PASILLOS_EXTRA):
        terreno[pasillo] = '.'

    # 4. 30 celdas lentas: 15 con agua y 15 con bosque, nunca pegadas a la partida ni a la salida.
    apartadas = set()
    for extremo in (PARTIDA_LABERINTO, META_LABERINTO):
        f, c = extremo
        apartadas |= {extremo} | {(f + 2 * df, c + 2 * dc) for df, dc in MOVIMIENTOS}
    elegidas = random.sample([celda for celda in celdas if celda not in apartadas], 2 * CELDAS_LENTAS)
    for numero, celda in enumerate(elegidas):
        terreno[celda] = 'A' if numero < CELDAS_LENTAS else 'B'

    mapa = {'terreno': terreno, 'filas': FILAS_LABERINTO, 'columnas': COLUMNAS_LABERINTO}
    nombres = (['Tú'] if con_jugador else []) + list(ALGORITMOS)
    corredores = []
    for nombre in nombres:
        if nombre == 'Tú':
            corredores.append(crear_corredor('Tú', PARTIDA_LABERINTO, velocidad=VELOCIDAD_JUGADOR))
        else:
            corredores.append(crear_corredor(nombre, PARTIDA_LABERINTO, ALGORITMOS[nombre], VELOCIDAD_RIVAL))

    return {'tipo': 'laberinto', 'mapa': mapa, 'pasillos': pasillos, 'corredores': corredores,
            'jugador': corredores[0] if con_jugador else None, 'distancias': costo_hasta(mapa, META_LABERINTO),
            'proximo': SEGUNDOS_ENTRE_CAMBIOS, 'recientes': {}, 'cambio': 9.0,
            'reloj': 0.0, 'cuenta': CUENTA_REGRESIVA, 'fase': 'cuenta', 'anuncio': False,
            'camara': crear_camara(), 'eventos': [],
            'adornos': crear_adornos(FILAS_LABERINTO, COLUMNAS_LABERINTO)}


def cambiar_laberinto(juego):
    """Cambia el laberinto: cierra hasta 8 pasillos y abre tantos como cerró.

    Entrada: la partida; su mapa se modifica directamente.
    Salida:  el par (cerrados, abiertos) con las casillas que cambiaron.

    Un pasillo solo se cierra si el laberinto sigue completamente conectado y
    si nadie está en él ni va entrando. Así nadie queda encerrado.
    """
    terreno = juego['mapa']['terreno']
    ocupadas = set()
    for corredor in juego['corredores']:
        ocupadas |= {corredor['casilla'], corredor['destino']}

    estaban_cerrados = [p for p in juego['pasillos'] if terreno[p] == '#']
    candidatos = [p for p in juego['pasillos'] if terreno[p] != '#' and p not in ocupadas]
    random.shuffle(candidatos)
    cerrados = []
    for pasillo in candidatos:
        if len(cerrados) == PASILLOS_POR_CAMBIO:
            break
        terreno[pasillo] = '#'                       # se prueba a cerrarlo
        if todo_conectado(terreno):
            cerrados.append(pasillo)
        else:
            terreno[pasillo] = '.'                   # dejaba celdas aisladas: se vuelve a abrir

    # Se abren tantos como se cerraron, entre los que ya estaban cerrados antes.
    abiertos = random.sample(estaban_cerrados, min(len(cerrados), len(estaban_cerrados)))
    for pasillo in abiertos:
        terreno[pasillo] = '.'

    # Un rival solo vuelve a planear si el cambio le cerró el camino que llevaba.
    for corredor in juego['corredores']:
        if corredor['algoritmo'] is not None and any(terreno[casilla] == '#' for casilla in corredor['ruta']):
            corredor['replanear'] = True
    juego['distancias'] = costo_hasta(juego['mapa'], META_LABERINTO)
    # Se anota qué casillas cambiaron, para dibujar los muros subiendo y bajando.
    juego['recientes'] = {**{p: 'cerrado' for p in cerrados}, **{p: 'abierto' for p in abiertos}}
    juego['cambio'] = 0.0
    return cerrados, abiertos


def actualizar_laberinto(juego, segundos, direcciones):
    """Avanza un cuadro de Maze Runner.

    Entradas:
        juego:       el diccionario de la partida
        segundos:    el tiempo que pasó desde el cuadro anterior
        direcciones: las direcciones que el jugador tiene oprimidas
    """
    if juego['fase'] == 'cuenta':
        juego['cuenta'] -= segundos
        if juego['cuenta'] <= 0:
            juego['fase'] = 'carrera'
        return

    juego['reloj'] += segundos
    juego['cambio'] += segundos
    # Cada 3 segundos el laberinto cambia.
    juego['proximo'] -= segundos
    if juego['proximo'] <= 0:
        juego['proximo'] += SEGUNDOS_ENTRE_CAMBIOS
        cambiar_laberinto(juego)

    for corredor in juego['corredores']:
        if corredor['final'] is not None:
            continue
        if avanzar(corredor, segundos) and corredor['casilla'] == META_LABERINTO:
            corredor['final'] = juego['reloj']       # llegó a la salida
            anotar_evento(juego, 'victoria', corredor)
            continue
        if corredor['algoritmo'] is None:
            mover_jugador(corredor, juego['mapa'], direcciones)
        else:
            conducir_rival(corredor, juego['mapa'], META_LABERINTO, segundos, FACTOR_DE_PENSAR_LABERINTO)

    # El resultado se anuncia igual que en atrapa gemas.
    if juego['jugador'] is not None:
        juego['anuncio'] = juego['jugador']['final'] is not None
    else:
        juego['anuncio'] = any(c['final'] is not None for c in juego['corredores'])

# ============================================================================
# 7. DIBUJO DEL TABLERO
# El tablero se ve desde arriba e inclinado: las casillas son más anchas que
# altas, y los muros, los árboles y los personajes tienen altura. Se dibuja de
# la fila del fondo a la de enfrente, para que lo de adelante tape lo de atrás.
# ============================================================================

ANCHO, ALTO = 1280, 720
ACERCAMIENTO = 1.9                       # cuánto se agranda el tablero con la tecla C

PASTO = [(126, 188, 98), (114, 176, 88)]             # el llano es pasto en dos tonos, como tablero de ajedrez
PISO = {'B': (86, 148, 78), 'A': (96, 168, 232), '#': (122, 112, 98)}
PIEDRA, PIEDRA_OSCURA = (170, 170, 178), (112, 112, 124)


def mezclar(a, b, cuanto):
    """Mezcla dos colores.

    Entradas: los colores a y b, y cuánto del segundo se usa (0 es todo a, 1 es todo b).
    Salida:   el color intermedio.
    """
    return tuple(int(x + (y - x) * cuanto) for x, y in zip(a, b))


def color_de_piso(terreno, fila, columna):
    """Da el color del piso de una casilla según su terreno."""
    return PASTO[(fila + columna) % 2] if terreno == '.' else PISO[terreno]


def crear_vista(zona, mapa, zoom=1.0, centro=None):
    """Define dónde y de qué tamaño se dibuja un tablero dentro de una zona de la pantalla.

    Entradas:
        zona:   el rectángulo de la pantalla reservado para el tablero
        mapa:   el mapa que se va a dibujar
        zoom:   1.0 muestra el tablero completo; más grande lo acerca
        centro: la posición (fila, columna) que queda al centro cuando está acercado.
                Si no se da, el centro del tablero.

    Salida: diccionario con
        'x', 'y':  esquina superior izquierda del piso del tablero, en pixeles
        'ancho':   ancho de una casilla
        'alto':    alto de una casilla en pantalla. Es 3/4 del ancho: esa es la inclinación.
        'altura':  cuántos pixeles se levantan los muros
        'escala':  tamaño relativo; sirve para dibujar personajes, gemas y banderas
        'zona':    la misma zona, para recortar lo que se salga de ella
    """
    # El tamaño de casilla más grande con el que el tablero completo cabe en la zona.
    ancho = int(min(zona.width / mapa['columnas'], zona.height / (mapa['filas'] * 0.75)) * zoom)
    alto = ancho * 3 // 4
    total_x, total_y = mapa['columnas'] * ancho, mapa['filas'] * alto
    if centro is None:
        centro = ((mapa['filas'] - 1) / 2, (mapa['columnas'] - 1) / 2)
    # El centro pedido queda a media zona, sin dejar que se vea más allá del borde del tablero.
    x = zona.centerx - (centro[1] + 0.5) * ancho
    y = zona.centery - (centro[0] + 0.5) * alto
    x = zona.centerx - total_x / 2 if total_x <= zona.width else min(zona.x, max(zona.right - total_x, x))
    y = zona.centery - total_y / 2 if total_y <= zona.height else min(zona.y, max(zona.bottom - total_y, y))
    return {'x': x, 'y': y, 'ancho': ancho, 'alto': alto, 'altura': ancho * 2 // 5, 'escala': ancho / 48, 'zona': zona}


def vista_de_camara(zona, mapa, camara, corredores):
    """Crea la vista de un tablero según la cámara de la partida.

    Entradas: la zona, el mapa, la cámara y la lista de corredores.
    Salida:   la vista. Si la cámara sigue a un corredor, queda centrada en él.
    """
    centro = camara['centro']
    if camara['seguir'] is not None and not camara['libre']:
        centro = posicion(corredores[camara['seguir']])
    return crear_vista(zona, mapa, camara['zoom'], centro)


def en_pantalla(vista, fila, columna):
    """Convierte una posición del tablero en un punto de la pantalla.

    Entradas: la vista y la posición (fila, columna), que puede tener decimales.
    Salida:   el pixel (x, y) del centro del piso de esa posición.
    """
    return (vista['x'] + (columna + 0.5) * vista['ancho'], vista['y'] + (fila + 0.5) * vista['alto'])


def casilla_en(vista, punto):
    """Convierte un punto de la pantalla en la posición del tablero que hay debajo.

    Entradas: la vista y el pixel (x, y).
    Salida:   la posición (fila, columna), con decimales.
    """
    return ((punto[1] - vista['y']) / vista['alto'] - 0.5, (punto[0] - vista['x']) / vista['ancho'] - 0.5)


def crear_adornos(filas, columnas):
    """Sortea los adornos de un tablero: flores, rocas y lámparas.

    Entradas: el tamaño del tablero.
    Salida:   diccionario {casilla: adorno}. Cada adorno es un diccionario con
              'tipo' ('flor', 'roca' o 'lampara'), su lugar dentro de la casilla
              ('dx', 'dy', de 0 a 1), un 'color' y una 'altura'.
              También trae, en la llave 'luciernagas', una lista de puntos de
              partida para las luciérnagas.

    Los adornos no estorban el paso: solo se dibujan, y solo donde hay pasto.
    """
    adornos = {}
    colores = [(250, 250, 250), (255, 214, 64), (244, 143, 177), (179, 157, 219), (255, 138, 101)]
    for f in range(filas):
        for c in range(columnas):
            suerte = random.random()
            if suerte < 0.17:
                tipo = 'flor'
            elif suerte < 0.23:
                tipo = 'roca'
            elif suerte < 0.26:
                tipo = 'lampara'
            else:
                continue
            adornos[(f, c)] = {'tipo': tipo, 'dx': random.uniform(0.18, 0.82), 'dy': random.uniform(0.25, 0.85),
                               'color': random.choice(colores), 'altura': random.uniform(0.5, 1.3)}
    adornos['luciernagas'] = [(random.uniform(0, filas - 1), random.uniform(0, columnas - 1), random.uniform(0, 6.28))
                              for numero in range(max(3, filas * columnas // 24))]
    return adornos


def dibujar_bloque(pantalla, vista, fila, columna, terreno, tamaño=1.0):
    """Dibuja lo que tiene altura en una casilla: el bloque de un muro o los árboles de un bosque.

    Entradas: la pantalla, la vista, la casilla, su terreno y el tamaño (de 0 a 1).
    El tamaño sirve para los cambios de terreno: los muros suben o bajan y los
    árboles crecen o se los traga la tierra.
    """
    w, h = vista['ancho'], vista['alto']
    alto = vista['altura'] * tamaño
    x, y = vista['x'] + columna * w, vista['y'] + fila * h
    if terreno == '#':
        # Un bloque de piedra: la cara de arriba, levantada, y la cara de enfrente, más oscura.
        pygame.draw.rect(pantalla, PIEDRA_OSCURA, (x, y - alto + h, w, alto + 1))    # cara de enfrente
        pygame.draw.rect(pantalla, PIEDRA, (x, y - alto, w, h))                      # cara de arriba
        pygame.draw.rect(pantalla, NEGRO, (x, y - alto, w, h + alto), 1)
    elif terreno == 'B':
        # Dos arbolitos: un tronco y una copa triangular.
        for dx, dy in ((0.3, 0.45), (0.7, 0.8)):
            bx, by = x + w * dx, y + h * dy
            pygame.draw.rect(pantalla, (110, 78, 48), (bx - w * 0.03, by - alto * 0.3, w * 0.06, alto * 0.3 + 1))
            copa = [(bx - w * 0.17 * tamaño, by - alto * 0.25), (bx + w * 0.17 * tamaño, by - alto * 0.25),
                    (bx, by - alto * 1.25)]
            pygame.draw.polygon(pantalla, (40, 112, 56), copa)
            pygame.draw.polygon(pantalla, (24, 72, 36), copa, 1)


def dibujar_adorno(pantalla, vista, casilla, adorno, entorno):
    """Dibuja un adorno: una flor, una roca o una lámpara.

    Entradas: la pantalla, la vista, la casilla, el adorno y el entorno
              (para saber si es de noche y encender la lámpara).
    """
    s = vista['escala']
    x = vista['x'] + (casilla[1] + adorno['dx']) * vista['ancho']
    y = vista['y'] + (casilla[0] + adorno['dy']) * vista['alto']
    if adorno['tipo'] == 'flor':
        # Cuatro pétalos alrededor de un centro amarillo.
        for dx, dy in ((-2.6, 0), (2.6, 0), (0, -2.6), (0, 2.6)):
            pygame.draw.circle(pantalla, adorno['color'], (x + dx * s, y + dy * s), max(1, 2.2 * s))
        pygame.draw.circle(pantalla, (255, 196, 0), (x, y), max(1, 1.6 * s))
    elif adorno['tipo'] == 'roca':
        # Una piedra gris; cada una tiene su propia altura.
        alto = 9 * s * adorno['altura']
        zona = (x - 7 * s, y - alto, 14 * s, alto)
        pygame.draw.ellipse(pantalla, (138, 140, 146), zona)
        pygame.draw.ellipse(pantalla, (70, 72, 78), zona, 1)
    else:
        # Una lámpara: un poste con un farol. De noche se enciende y alumbra.
        encendida = entorno['oscuridad'] > 0.25
        pygame.draw.line(pantalla, (60, 50, 44), (x, y), (x, y - 30 * s), max(2, int(3 * s)))
        farol = pygame.Rect(0, 0, 9 * s, 10 * s)
        farol.midbottom = (x, y - 28 * s)
        pygame.draw.rect(pantalla, (255, 236, 130) if encendida else (190, 190, 170), farol, border_radius=2)
        pygame.draw.rect(pantalla, (60, 50, 44), farol, 1, border_radius=2)
        if encendida:
            entorno['luces'].append((x, y - 30 * s, 95 * s))


def dibujar_ruta(pantalla, vista, corredor, color=None, casillas=None):
    """Dibuja sobre el piso la ruta que tiene planeada un personaje.

    Entradas:
        pantalla, vista
        corredor: el personaje; la línea sale de donde está
        color:    el color de la línea; si no se da, el del personaje
        casillas: las casillas de la ruta; si no se dan, las que le faltan al personaje
    """
    if casillas is None:
        casillas = ([corredor['destino']] if corredor['destino'] else []) + corredor['ruta']
    puntos = [en_pantalla(vista, *posicion(corredor))] + [en_pantalla(vista, *casilla) for casilla in casillas]
    if len(puntos) >= 2:
        grosor = max(2, int(5 * vista['escala']))
        pygame.draw.lines(pantalla, NEGRO, False, puntos, grosor + 2)            # borde oscuro, para que se vea sobre cualquier terreno
        pygame.draw.lines(pantalla, color or corredor['color'], False, puntos, grosor)
        pygame.draw.circle(pantalla, color or corredor['color'], puntos[-1], grosor * 1.4)   # un punto donde termina


def dibujar_bandera(pantalla, vista, pie, color, tamaño=1.0):
    """Dibuja una bandera: un asta y un triángulo de tela.

    Entradas: la pantalla, la vista, el pixel donde se apoya el asta, el color y el tamaño relativo.
    """
    s = vista['escala'] * tamaño
    x, y = pie
    pygame.draw.line(pantalla, NEGRO, (x, y), (x, y - 44 * s), max(2, int(3 * s)))
    tela = [(x, y - 44 * s), (x + 24 * s, y - 36 * s), (x, y - 28 * s)]
    pygame.draw.polygon(pantalla, color, tela)
    pygame.draw.polygon(pantalla, NEGRO, tela, max(1, int(2 * s)))


def dibujar_gema(pantalla, vista, casilla, t):
    """Dibuja la gema que toca recoger: un rombo dorado que flota.

    Entradas: la pantalla, la vista, la casilla donde está y el tiempo en segundos.
    """
    s = vista['escala']
    x, y = en_pantalla(vista, *casilla)
    y = y - 16 * s + sin(t * 4) * 3 * s              # sube y baja despacio
    radio = 14 * s
    rombo = [(x, y - radio * 1.3), (x + radio, y), (x, y + radio * 1.1), (x - radio, y)]
    pygame.draw.polygon(pantalla, DORADO, rombo)
    pygame.draw.polygon(pantalla, NEGRO, rombo, max(1, int(2 * s)))
    pygame.draw.line(pantalla, BLANCO, (x - radio * 0.4, y - radio * 0.3), (x, y - radio * 0.9), max(1, int(2 * s)))   # un brillo


def dibujar_tablero(pantalla, vista, mapa, planos, altos, t, entorno, adornos=None, anterior=None, progreso=1.0):
    """Dibuja un tablero completo, respetando qué tapa a qué.

    Entradas:
        pantalla, vista, mapa
        planos:   lista de funciones que dibujan cosas pegadas al piso (salidas, rutas, marcas)
        altos:    lista de pares (fila, funcion) con las cosas que tienen altura
                  (personajes, gemas, banderas). La fila dice en qué momento se dibuja cada una.
        t:        tiempo en segundos
        entorno:  el estado del ambiente (día o noche, luces)
        adornos:  los adornos del tablero, o None
        anterior: diccionario {casilla: terreno que tenía antes} con las casillas que
                  están cambiando, o None si el terreno no está cambiando
        progreso: de 0 a 1, cuánto va del cambio de terreno

    Orden: primero todo el piso, luego lo pegado al piso y al final, fila por
    fila desde el fondo, los bloques de esa fila y las cosas paradas en ella.
    Así un muro de enfrente tapa a un personaje que está detrás. Lo que se sale
    de la zona del tablero se recorta: hace falta cuando la vista está acercada.

    Cambio de terreno: en la primera mitad, lo viejo se hunde (los muros bajan
    y a los árboles se los traga la tierra); en la segunda, lo nuevo crece. El
    color del piso pasa poco a poco del anterior al nuevo, y así el agua
    aparece y desaparece.
    """
    zona = vista['zona']
    w, h = vista['ancho'], vista['alto']
    anterior = anterior or {}
    # El recorte se extiende un poco hacia arriba: es lo que sobresalen los muros y los
    # personajes de la primera fila. Tiene tope, para que al acercar la vista el tablero
    # no invada los letreros que van encima.
    sobra = min(w, 40)
    pantalla.set_clip(zona.x, zona.y - sobra, zona.width, zona.height + sobra)

    # 1. El piso: una losa por casilla.
    for (f, c), terreno in mapa['terreno'].items():
        x, y = vista['x'] + c * w, vista['y'] + f * h
        if x + w < zona.x or x > zona.right or y + h < zona.y - sobra or y > zona.bottom:
            continue                                 # queda fuera de la vista: no se dibuja
        color = color_de_piso(terreno, f, c)
        if (f, c) in anterior:
            color = mezclar(color_de_piso(anterior[(f, c)], f, c), color, progreso)
        pygame.draw.rect(pantalla, color, (x, y, w + 1, h + 1))
        if terreno == 'A' and ((f, c) not in anterior or progreso > 0.5):
            # Dos ondas claras que se mueven de lado a lado.
            corrimiento = sin(t * 2 + f + c) * w * 0.08
            for k in (0.35, 0.68):
                pygame.draw.line(pantalla, (190, 222, 250), (x + w * 0.2 + corrimiento, y + h * k),
                                 (x + w * 0.8 + corrimiento, y + h * k), max(1, int(2 * vista['escala'])))

    # 2. Lo que va pegado al piso: flores, y luego salidas, rutas y marcas.
    if adornos:
        for casilla, adorno in adornos.items():
            if casilla != 'luciernagas' and adorno['tipo'] == 'flor' and mapa['terreno'].get(casilla) == '.':
                dibujar_adorno(pantalla, vista, casilla, adorno, entorno)
    for dibujar in planos:
        dibujar()

    # 3. Fila por fila: bloques, adornos con altura y cosas paradas en la fila.
    for fila in range(mapa['filas']):
        for columna in range(mapa['columnas']):
            casilla = (fila, columna)
            terreno = mapa['terreno'][casilla]
            if casilla in anterior:
                # Está cambiando: primero se encoge lo viejo y después crece lo nuevo.
                if progreso < 0.5 and anterior[casilla] in '#B':
                    dibujar_bloque(pantalla, vista, fila, columna, anterior[casilla], 1 - progreso * 2)
                elif progreso >= 0.5 and terreno in '#B':
                    dibujar_bloque(pantalla, vista, fila, columna, terreno, progreso * 2 - 1)
            elif terreno in '#B':
                dibujar_bloque(pantalla, vista, fila, columna, terreno)
            elif adornos and casilla in adornos and adornos[casilla]['tipo'] != 'flor' and terreno == '.':
                dibujar_adorno(pantalla, vista, casilla, adornos[casilla], entorno)
        for fila_de_la_cosa, dibujar in altos:
            # Una cosa a medio paso entre dos filas se dibuja con la fila a la que está más cerca.
            if round(fila_de_la_cosa) == fila:
                dibujar()

    # 4. De noche, las luciérnagas: puntos que dan vueltas despacio. Se dibujan después, sobre la oscuridad.
    if adornos and entorno['oscuridad'] > 0.3:
        for f0, c0, fase in adornos['luciernagas']:
            punto = en_pantalla(vista, f0 + sin(t * 0.7 + fase) * 1.3, c0 + cos(t * 0.5 + fase * 2) * 1.6)
            if zona.collidepoint(punto):
                entorno['chispas'].append((punto[0], punto[1] - 18 * vista['escala'], 0.6 + 0.4 * sin(t * 3 + fase)))
    pantalla.set_clip(None)                          # se quita el recorte


def casillas_que_cambian(viejo, nuevo):
    """Da las casillas cuyo terreno es distinto entre dos mapas.

    Entradas: el mapa anterior y el nuevo.
    Salida:   diccionario {casilla: terreno que tenía antes}, solo con las que cambiaron.
    """
    if viejo is None:
        return {}
    return {casilla: terreno for casilla, terreno in viejo['terreno'].items() if nuevo['terreno'][casilla] != terreno}


# ============================================================================
# 8. LOS PERSONAJES
# Cada personaje es un muñequito con cabeza, cuerpo, brazos y piernas. Su
# postura se calcula en cada cuadro: cada algoritmo camina y festeja a su modo.
# ============================================================================

def pose_de(corredor, t):
    """Calcula la postura de un personaje en este momento.

    Entradas: el corredor y el tiempo en segundos.

    Salida: un diccionario con
        'salto':       cuántos pixeles está levantado del piso (antes de escalar)
        'inclinacion': grados que se inclina el cuerpo; positivo, hacia la derecha de la pantalla
        'pierna_izq', 'pierna_der': ángulo de cada pierna, en grados desde "hacia abajo";
                       positivo es hacia la derecha de la pantalla
        'brazo_izq', 'brazo_der':   lo mismo para los brazos; 180 es hacia arriba
        'codo_izq', 'codo_der':     cuánto se dobla el antebrazo respecto al brazo
        'ancho':       1 es de frente; al acercarse a 0 se ve de canto (para girar como trompo)
        'cabeza':      grados que se ladea la cabeza

    Personalidades:
        BFS        marcha como soldado y festeja con saltos de tijera
        DFS        corre inclinado con los brazos hacia atrás y festeja girando como trompo
        Dijkstra   camina de puntillas equilibrándose y festeja con una reverencia
        Voraz      da zancadas enormes con los brazos al frente y festeja a grandes brincos
        A*         corre a saltos largos, uno por casilla, y festeja con el baile del robot
    """
    pose = {'salto': 0.0, 'inclinacion': 0.0, 'pierna_izq': 0.0, 'pierna_der': 0.0, 'brazo_izq': -8.0, 'brazo_der': 8.0,
            'codo_izq': 0.0, 'codo_der': 0.0, 'ancho': 1.0, 'cabeza': 0.0}
    nombre = corredor['nombre'] if corredor['algoritmo'] is not None else 'Tú'
    m = corredor['mira']                             # 1 si ve a la derecha, -1 si ve a la izquierda

    # ---- Festejo: quien ya terminó o ganó se queda bailando.
    if corredor['final'] is not None:
        if nombre == 'BFS':
            # Saltos de tijera: brazos y piernas se abren y se cierran al mismo tiempo.
            k = (sin(t * 7) + 1) / 2
            pose.update(brazo_izq=-(20 + 140 * k), brazo_der=20 + 140 * k, pierna_izq=-30 * k, pierna_der=30 * k, salto=8 * k)
        elif nombre == 'DFS':
            # Gira como trompo: el cuerpo se ve de frente, de canto, de espaldas...
            pose.update(ancho=cos(t * 9), brazo_izq=-90, brazo_der=90, salto=2)
        elif nombre == 'Dijkstra':
            # Una reverencia lenta, una y otra vez.
            k = (sin(t * 3) + 1) / 2
            pose.update(inclinacion=70 * k * m, brazo_izq=-12, brazo_der=12)
        elif nombre == 'Voraz':
            # Grandes brincos con los brazos arriba.
            k = abs(sin(t * 5))
            pose.update(salto=30 * k, brazo_izq=-160, brazo_der=160, pierna_izq=-25 * k, pierna_der=25 * k)
        elif nombre == 'A*':
            # El baile del robot: posturas rígidas, en ángulo recto, que cambian de golpe.
            paso = int(t * 3) % 4
            codos = [(90, -90), (-90, -90), (-90, 90), (90, 90)][paso]
            pose.update(brazo_izq=-90, brazo_der=90, codo_izq=codos[0], codo_der=codos[1],
                        cabeza=[-14, 0, 14, 0][paso], inclinacion=[-6, 0, 6, 0][paso])
        else:
            # El jugador: brazos arriba, saludando, y brinquitos.
            pose.update(brazo_izq=-(150 + 15 * sin(t * 8)), brazo_der=150 + 15 * sin(t * 8 + 1), salto=6 * abs(sin(t * 6)))
        return pose

    # ---- Pensando: quieto, con una mano en la cabeza.
    if corredor['pensando'] > 0:
        pose.update(brazo_der=140, codo_der=75, cabeza=8)
        return pose

    # ---- Quieto: respira un poco.
    if corredor['destino'] is None:
        pose['salto'] = 0.6 * sin(t * 3)
        return pose

    # ---- Caminando. El vaivén va de 0 a 1 y de regreso a 0 dentro de cada paso,
    #      y cambia de signo en cada paso para alternar la pierna que va adelante.
    avance = corredor['avance']
    lado = 1 if corredor['zancadas'] % 2 == 0 else -1
    vaiven = sin(pi * avance) * lado
    if nombre == 'BFS':
        # Marcha: piernas y brazos tiesos, parejos, sin brincar.
        pose.update(pierna_izq=42 * vaiven * m, pierna_der=-42 * vaiven * m, brazo_izq=-48 * vaiven * m, brazo_der=48 * vaiven * m)
    elif nombre == 'DFS':
        # Corre lanzado: cuerpo inclinado, brazos hacia atrás, pasos rápidos.
        rapido = sin(4 * pi * avance)
        pose.update(inclinacion=24 * m, brazo_izq=-70 * m, brazo_der=-70 * m, pierna_izq=52 * rapido * m, pierna_der=-52 * rapido * m,
                    salto=2 * abs(rapido))
    elif nombre == 'Dijkstra':
        # De puntillas: pasos cortos, brazos abiertos que se balancean.
        balance = sin(t * 9)
        pose.update(salto=4, pierna_izq=14 * vaiven * m, pierna_der=-14 * vaiven * m, brazo_izq=-(88 + 12 * balance),
                    brazo_der=88 - 12 * balance, inclinacion=4 * balance)
    elif nombre == 'Voraz':
        # Zancadas enormes con los brazos al frente.
        pose.update(pierna_izq=62 * vaiven * m, pierna_der=-62 * vaiven * m, brazo_izq=85 * m, brazo_der=(85 + 8 * sin(t * 14)) * m,
                    inclinacion=10 * m, salto=7 * abs(vaiven))
    elif nombre == 'A*':
        # Un salto largo por casilla, como correr y saltar a la vez: sale parado, en el aire abre
        # las piernas una adelante y otra atrás, y cae con las dos juntas. En cada salto cambia
        # cuál pierna va adelante. Los brazos van al contrario de las piernas, como al correr.
        # Los pies no atraviesan el piso: el salto sube más de lo que las piernas bajan al abrirse.
        aire = sin(pi * avance)
        pose.update(salto=22 * aire, inclinacion=10 * aire * m, pierna_izq=68 * aire * lado * m, pierna_der=-68 * aire * lado * m,
                    brazo_izq=-78 * aire * lado * m, brazo_der=78 * aire * lado * m)
    else:
        # El jugador camina normal.
        pose.update(pierna_izq=32 * vaiven * m, pierna_der=-32 * vaiven * m, brazo_izq=-28 * vaiven * m, brazo_der=28 * vaiven * m,
                    salto=3 * abs(vaiven))
    return pose


def dibujar_personaje(pantalla, vista, corredor, t, entorno, bandera=None):
    """Dibuja un personaje con la postura que le toca.

    Entradas:
        pantalla, vista
        corredor: el personaje
        t:        tiempo en segundos
        entorno:  el estado del ambiente; de noche el personaje lleva una linterna
        bandera:  el color de la bandera que carga, o None
    """
    s = vista['escala']
    pose = pose_de(corredor, t)
    x, y = en_pantalla(vista, *posicion(corredor))
    ancho = pose['ancho']
    oscuro = mezclar(corredor['color'], NEGRO, 0.35)
    grosor = max(2, int(4.5 * s))

    def extremo(origen, largo, grados):
        """El punto donde termina un brazo o una pierna: sale del origen y baja girado tantos grados."""
        angulo = radians(grados)
        return (origen[0] + largo * sin(angulo) * (ancho if abs(ancho) > 0.25 else 0.25), origen[1] + largo * cos(angulo))

    # La sombra, en el piso. Se achica cuando el personaje salta.
    chica = max(0.5, 1 - pose['salto'] / 40)
    pygame.draw.ellipse(pantalla, (52, 84, 46), (x - 13 * s * chica, y - 4 * s, 26 * s * chica, 9 * s))

    # El brillo de quien acaba de recoger algo: un halo blanco que late. Se dibuja antes que el
    # personaje, así que queda detrás de él y solo se ve alrededor de su silueta.
    if corredor['brillo'] > 0:
        radio = int((26 + 6 * sin(t * 20)) * s)
        halo = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 255, 255, int(170 * min(1, corredor['brillo'] * 2))), (radio, radio), radio)
        pantalla.blit(halo, (x - radio, y - 22 * s - radio))

    # Las articulaciones: cadera, hombros y cabeza. La inclinación gira el cuerpo sobre la cadera.
    piso = y - pose['salto'] * s
    cadera = (x, piso - 13 * s)
    inclinacion = radians(pose['inclinacion'])
    hombros = (cadera[0] + 15 * s * sin(inclinacion), cadera[1] - 15 * s * cos(inclinacion))
    cabeza = (hombros[0] + 9 * s * sin(inclinacion + radians(pose['cabeza'])), hombros[1] - 9 * s * cos(inclinacion))

    # Las piernas, de la cadera hacia abajo.
    for lado, clave in ((-1, 'pierna_izq'), (1, 'pierna_der')):
        origen = (cadera[0] + lado * 3.5 * s * ancho, cadera[1])
        pygame.draw.line(pantalla, NEGRO, origen, extremo(origen, 13 * s, pose[clave]), grosor + 2)
        pygame.draw.line(pantalla, oscuro, origen, extremo(origen, 13 * s, pose[clave]), grosor)

    # El cuerpo: un rectángulo girado, de la cadera a los hombros.
    medio = 7 * s * max(abs(ancho), 0.3)
    dx, dy = cos(inclinacion) * medio, sin(inclinacion) * medio
    cuerpo = [(cadera[0] - dx, cadera[1] - dy), (cadera[0] + dx, cadera[1] + dy),
              (hombros[0] + dx, hombros[1] + dy), (hombros[0] - dx, hombros[1] - dy)]
    pygame.draw.polygon(pantalla, corredor['color'], cuerpo)
    pygame.draw.polygon(pantalla, NEGRO, cuerpo, max(1, int(2 * s)))

    # Los brazos: brazo y antebrazo, que se dobla en el codo.
    mano = None
    for lado, clave, codo in ((-1, 'brazo_izq', 'codo_izq'), (1, 'brazo_der', 'codo_der')):
        hombro = (hombros[0] + lado * 6.5 * s * ancho, hombros[1] + 2 * s)
        punto_del_codo = extremo(hombro, 7 * s, pose[clave])
        mano = extremo(punto_del_codo, 7 * s, pose[clave] + pose[codo])
        for a, b in ((hombro, punto_del_codo), (punto_del_codo, mano)):
            pygame.draw.line(pantalla, NEGRO, a, b, grosor + 2)
            pygame.draw.line(pantalla, oscuro, a, b, grosor)

    # La cabeza: un círculo liso, sin cara.
    pygame.draw.circle(pantalla, (255, 224, 189), cabeza, 8.5 * s)
    pygame.draw.circle(pantalla, NEGRO, cabeza, 8.5 * s, max(1, int(2 * s)))

    if bandera:
        dibujar_bandera(pantalla, vista, (hombros[0] - 8 * s * corredor['mira'], hombros[1] + 6 * s), bandera, 0.7)

    # De noche, una linterna en la mano que alumbra alrededor.
    if entorno['oscuridad'] > 0.25:
        pygame.draw.circle(pantalla, (255, 236, 130), mano, max(2, 3.5 * s))
        pygame.draw.circle(pantalla, NEGRO, mano, max(2, 3.5 * s), 1)
        entorno['luces'].append((x, piso - 16 * s, 80 * s))

    # Mientras piensa su ruta, un globito con puntos suspensivos.
    if corredor['pensando'] > 0 and corredor['final'] is None:
        globo = pygame.Rect(0, 0, 30 * s, 18 * s)
        globo.center = (x + 18 * s, piso - 52 * s)
        pygame.draw.ellipse(pantalla, BLANCO, globo)
        pygame.draw.ellipse(pantalla, NEGRO, globo, max(1, int(2 * s)))
        for dx in (-7, 0, 7):
            pygame.draw.circle(pantalla, NEGRO, (globo.centerx + dx * s, globo.centery), max(1, 2 * s))


# ============================================================================
# 9. EFECTOS Y AMBIENTE
# Partículas al recoger algo, fuegos artificiales al anotar o ganar, nubes y
# pájaros que pasan, y el ciclo de día y noche.
# ============================================================================

DURACION_DEL_DIA = 90.0                  # segundos que dura un día completo, con su noche
OSCURIDAD_MAXIMA = 0.66                  # qué tan oscura llega a ser la noche (1 sería negro total)
COLORES_DE_FIESTA = [(255, 82, 82), (255, 214, 64), (105, 240, 174), (64, 196, 255), (224, 130, 255), BLANCO]


def crear_efectos():
    """Crea el estado de los efectos.

    Salida: diccionario con
        'particulas': lista de chispas en vuelo. Cada una tiene posición, velocidad,
                      color, tamaño y los segundos de vida que le quedan.
        'cohetes':    fuegos artificiales programados: (segundos que faltan, x, y, color)
    """
    return {'particulas': [], 'cohetes': []}


def estallar(efectos, x, y, color, cantidad=16, fuerza=150.0):
    """Suelta un montón de partículas desde un punto, en todas direcciones.

    Entradas: los efectos, el punto (x, y) de la pantalla, el color, cuántas y con qué fuerza salen.
    """
    for numero in range(cantidad):
        angulo = random.uniform(0, 2 * pi)
        rapidez = random.uniform(0.35, 1.0) * fuerza
        vida = random.uniform(0.45, 0.95)
        efectos['particulas'].append({'x': x, 'y': y, 'vx': cos(angulo) * rapidez, 'vy': sin(angulo) * rapidez - fuerza * 0.4,
                                      'color': color, 'radio': random.uniform(2.0, 4.5), 'vida': vida, 'total': vida})
    del efectos['particulas'][:-900]                 # nunca más de 900 a la vez, para no alentar el juego


def fuegos_artificiales(efectos, zona, cantidad):
    """Programa varios fuegos artificiales sobre una zona de la pantalla.

    Entradas: los efectos, el rectángulo donde estallan y cuántos son.
    Estallan uno tras otro, con una pausa corta entre ellos.
    """
    for numero in range(cantidad):
        x = random.uniform(zona.x + zona.width * 0.15, zona.right - zona.width * 0.15)
        y = random.uniform(zona.y + zona.height * 0.1, zona.y + zona.height * 0.55)
        efectos['cohetes'].append([numero * 0.22, x, y, random.choice(COLORES_DE_FIESTA)])


def lanzar_eventos(efectos, juego, vistas):
    """Convierte en efectos lo que acaba de pasar en la partida.

    Entradas:
        efectos: el estado de los efectos
        juego:   la partida; se vacía su lista de eventos
        vistas:  diccionario {número de tablero: vista} con las vistas de este cuadro

    Recoger algo suelta partículas doradas donde está el personaje. Anotar o
    ganar lanza fuegos artificiales sobre su tablero.
    """
    for evento in juego['eventos']:
        vista = vistas.get(evento['tablero'])
        if vista is None:
            continue                                 # ese tablero no se está viendo ahora
        x, y = en_pantalla(vista, *posicion(evento['quien']))
        if evento['tipo'] == 'recoger':
            estallar(efectos, x, y - 20 * vista['escala'], DORADO)
        elif evento['tipo'] == 'punto':
            fuegos_artificiales(efectos, vista['zona'], 4)
        else:
            fuegos_artificiales(efectos, vista['zona'], 9)
    juego['eventos'].clear()


def actualizar_efectos(efectos, segundos):
    """Mueve las partículas y hace estallar los fuegos artificiales a su tiempo.

    Entradas: los efectos y los segundos que pasaron desde el cuadro anterior.
    """
    for cohete in efectos['cohetes']:
        cohete[0] -= segundos
        if cohete[0] <= 0:
            estallar(efectos, cohete[1], cohete[2], cohete[3], 34, 230.0)
    efectos['cohetes'] = [cohete for cohete in efectos['cohetes'] if cohete[0] > 0]
    for p in efectos['particulas']:
        p['x'] += p['vx'] * segundos
        p['y'] += p['vy'] * segundos
        p['vy'] += 260 * segundos                    # la gravedad las hace caer
        p['vida'] -= segundos
    efectos['particulas'] = [p for p in efectos['particulas'] if p['vida'] > 0]


def dibujar_efectos(pantalla, efectos):
    """Dibuja las partículas. Se achican conforme se les acaba la vida."""
    for p in efectos['particulas']:
        pygame.draw.circle(pantalla, p['color'], (p['x'], p['y']), max(1, p['radio'] * p['vida'] / p['total']))


def crear_entorno():
    """Crea el estado del ambiente: la hora del día, las nubes y los pájaros.

    Salida: diccionario con
        't':         segundos desde que abrió el programa
        'oscuridad': de 0 (día) a OSCURIDAD_MAXIMA (noche cerrada)
        'luces':     las luces de este cuadro: (x, y, radio). Las ponen las lámparas y las linternas.
        'chispas':   las luciérnagas de este cuadro: (x, y, brillo)
        'nubes':     lista de nubes: posición, tamaño, velocidad y su imagen ya preparada
        'pajaros':   lista de bandadas: posición, velocidad y cuántos pájaros lleva
        'capa':      la imagen con la que se oscurece la pantalla de noche
        'focos':     imágenes de luz ya preparadas, por tamaño
    """
    nubes = []
    for numero in range(5):
        ancho = random.randint(170, 300)
        imagen = pygame.Surface((ancho, ancho // 2), pygame.SRCALPHA)
        # Cada nube es de una sola pieza: varios óvalos blancos y translúcidos encimados.
        for parte in range(5):
            w = random.randint(ancho // 3, ancho // 2)
            pygame.draw.ellipse(imagen, (255, 255, 255, 46), (random.randint(0, ancho - w), random.randint(0, ancho // 5), w, ancho // 3))
        nubes.append({'x': random.uniform(0, ANCHO), 'y': random.uniform(70, ALTO - 220), 'vel': random.uniform(6, 16), 'imagen': imagen})
    return {'t': 0.0, 'oscuridad': 0.0, 'luces': [], 'chispas': [], 'nubes': nubes, 'pajaros': [],
            'capa': pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA), 'focos': {}}


def actualizar_entorno(entorno, segundos):
    """Avanza el ambiente un cuadro: la hora, las nubes y los pájaros.

    Entradas: el entorno y los segundos que pasaron desde el cuadro anterior.
    """
    entorno['t'] += segundos
    # La hora va de 0 a 1 a lo largo del día. La primera mitad es de día; luego
    # atardece, es de noche y amanece.
    hora = (entorno['t'] % DURACION_DEL_DIA) / DURACION_DEL_DIA
    if hora < 0.5:
        nivel = 0.0
    elif hora < 0.6:
        nivel = (hora - 0.5) / 0.1                   # atardecer
    elif hora < 0.9:
        nivel = 1.0                                  # noche
    else:
        nivel = (1.0 - hora) / 0.1                   # amanecer
    entorno['oscuridad'] = nivel * OSCURIDAD_MAXIMA

    for nube in entorno['nubes']:
        nube['x'] += nube['vel'] * segundos
        if nube['x'] > ANCHO + 20:                   # salió por la derecha: vuelve a entrar por la izquierda
            nube['x'] = -nube['imagen'].get_width()
            nube['y'] = random.uniform(70, ALTO - 220)
    # De vez en cuando cruza una bandada de pájaros.
    if random.random() < segundos / 9:
        direccion = random.choice([-1, 1])
        entorno['pajaros'].append({'x': -40 if direccion == 1 else ANCHO + 40, 'y': random.uniform(90, ALTO - 200),
                                   'vel': direccion * random.uniform(70, 120), 'cuantos': random.randint(3, 6)})
    for bandada in entorno['pajaros']:
        bandada['x'] += bandada['vel'] * segundos
    entorno['pajaros'] = [b for b in entorno['pajaros'] if -80 < b['x'] < ANCHO + 80]


def color_del_cielo(entorno):
    """Da el color del fondo según la hora: azul verdoso de día y azul muy oscuro de noche."""
    return mezclar((52, 92, 112), (10, 14, 30), entorno['oscuridad'] / OSCURIDAD_MAXIMA)


def empezar_cuadro(entorno):
    """Vacía las luces y las luciérnagas del cuadro anterior. Se llama antes de dibujar los tableros."""
    entorno['luces'].clear()
    entorno['chispas'].clear()


def dibujar_cielo(pantalla, entorno, t):
    """Dibuja lo que pasa por encima de los tableros: nubes, pájaros y, de noche, la oscuridad.

    Entradas: la pantalla, el entorno y el tiempo en segundos.

    La noche es una capa azul oscura semitransparente sobre toda la pantalla.
    Donde hay una luz (una lámpara encendida o la linterna de un personaje) se
    le resta transparencia a la capa, y por eso ahí se ve claro.
    """
    for nube in entorno['nubes']:
        pantalla.blit(nube['imagen'], (nube['x'], nube['y']))
    for bandada in entorno['pajaros']:
        for numero in range(bandada['cuantos']):
            # Cada pájaro es una "v" que aletea; van en fila escalonada.
            x = bandada['x'] - numero * 22 * (1 if bandada['vel'] > 0 else -1)
            y = bandada['y'] + numero * 9 * (1 if numero % 2 else -1)
            ala = 5 + 3 * sin(t * 10 + numero)
            pygame.draw.lines(pantalla, (30, 30, 36), False, [(x - 7, y - ala), (x, y), (x + 7, y - ala)], 2)

    if entorno['oscuridad'] > 0.02:
        capa = entorno['capa']
        capa.fill((8, 12, 44, int(255 * entorno['oscuridad'])))
        for x, y, radio in entorno['luces']:
            radio = max(20, int(radio / 10) * 10)    # se redondea para reutilizar las imágenes ya hechas
            if radio not in entorno['focos']:
                # Un foco: círculos cada vez más chicos y más fuertes. Al restarlo de la capa abre un hueco de luz.
                foco = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
                for paso in range(12):
                    pygame.draw.circle(foco, (0, 0, 0, 22), (radio, radio), int(radio * (1 - paso / 12)))
                entorno['focos'][radio] = foco
            capa.blit(entorno['focos'][radio], (x - radio, y - radio), special_flags=pygame.BLEND_RGBA_SUB)
        pantalla.blit(capa, (0, 0))
        # Las luciérnagas, encima de la oscuridad.
        for x, y, brillo in entorno['chispas']:
            pygame.draw.circle(pantalla, (255, 244, 150), (x, y), 2 + 1.5 * brillo)

# ============================================================================
# 10. LA INTERFAZ, AL ESTILO DE UN JUEGO DE CARRERAS
# ============================================================================

GRIS_CLARO = (205, 208, 212)


def crear_fuentes():
    """Prepara los tipos de letra.

    Salida: diccionario {'enorme', 'titulo', 'grande', 'normal', 'chica', 'codigo'}.
    """
    nombres = 'segoeui,arial,dejavusans'             # se usa el primero que exista en la computadora
    return {'enorme': pygame.font.SysFont(nombres, 150, bold=True),
            'titulo': pygame.font.SysFont(nombres, 60, bold=True),
            'grande': pygame.font.SysFont(nombres, 34, bold=True),
            'normal': pygame.font.SysFont(nombres, 22, bold=True),
            'chica': pygame.font.SysFont(nombres, 17),
            'codigo': pygame.font.SysFont('consolas,couriernew,dejavusansmono', 15)}


def escribir(pantalla, fuente, texto, posicion_del_texto, color=BLANCO, ancla='izquierda'):
    """Escribe un texto.

    Entradas:
        pantalla, fuente, texto
        posicion_del_texto: el punto (x, y) de referencia
        color:              color de la letra
        ancla:              'izquierda' (el punto es la esquina superior izquierda),
                            'derecha' (esquina superior derecha) o 'centro' (el centro del texto)

    Salida: el rectángulo que ocupó el texto.
    """
    imagen = fuente.render(str(texto), True, color)
    zona = imagen.get_rect()
    if ancla == 'centro':
        zona.center = posicion_del_texto
    elif ancla == 'derecha':
        zona.topright = posicion_del_texto
    else:
        zona.topleft = posicion_del_texto
    pantalla.blit(imagen, zona)
    return zona


def dibujar_ficha(pantalla, color, zona):
    """Dibuja un cuadrito del color de un competidor, con borde blanco.

    Entradas: la pantalla, el color y el rectángulo.
    El borde hace falta porque el carbón de A* casi no se ve sobre un fondo oscuro.
    """
    pygame.draw.rect(pantalla, color, zona, border_radius=4)
    pygame.draw.rect(pantalla, BLANCO, zona, 2, border_radius=4)


def dibujar_boton(pantalla, fuentes, zona, texto, activo=False, color=None):
    """Dibuja un botón: un rectángulo redondeado con su texto al centro.

    Entradas: la pantalla, las fuentes, el rectángulo, el texto, si está activo
              (se pinta de rojo) y, si se quiere, el color de un competidor para ponerle su ficha.
    """
    pygame.draw.rect(pantalla, ROJO if activo else GRIS_OSCURO, zona, border_radius=8)
    pygame.draw.rect(pantalla, (90, 90, 94), zona, 1, border_radius=8)
    if color:
        dibujar_ficha(pantalla, color, pygame.Rect(zona.x + 7, zona.y + 8, 12, zona.height - 16))
    escribir(pantalla, fuentes['chica'], texto, (zona.centerx + (7 if color else 0), zona.centery), BLANCO, 'centro')


def texto_de_tiempo(segundos):
    """Escribe un tiempo como en un cronómetro: minutos, segundos y décimas (0:07.3)."""
    return f'{int(segundos // 60)}:{segundos % 60:04.1f}'


def dibujar_barra(pantalla, fuentes, titulo, reloj):
    """Dibuja la barra superior: el nombre del juego y el cronómetro.

    Entradas: la pantalla, las fuentes, el nombre del juego y los segundos de carrera.
    """
    pygame.draw.rect(pantalla, NEGRO, (0, 0, ANCHO, 72))
    pygame.draw.rect(pantalla, ROJO, (0, 72, ANCHO, 5))
    escribir(pantalla, fuentes['grande'], titulo, (24, 14))
    escribir(pantalla, fuentes['chica'], 'TIEMPO', (ANCHO - 24, 8), GRIS, 'derecha')
    escribir(pantalla, fuentes['grande'], texto_de_tiempo(reloj), (ANCHO - 24, 26), BLANCO, 'derecha')


def dibujar_cuenta(pantalla, fuentes, juego):
    """Dibuja la cuenta regresiva de salida: 3, 2, 1 y la palabra de arranque.

    Entradas: la pantalla, las fuentes y la partida.
    """
    if juego['fase'] == 'cuenta':
        texto = str(ceil(juego['cuenta']))           # 2.4 segundos se muestra como 3
    elif juego['fase'] == 'carrera' and juego['reloj'] < 0.8:
        texto = '¡Ya!'
    else:
        return
    # El número con un borde negro: se escribe 4 veces corrido en negro y una vez en dorado encima.
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4)):
        escribir(pantalla, fuentes['enorme'], texto, (ANCHO // 2 + dx, ALTO // 2 + dy), NEGRO, 'centro')
    escribir(pantalla, fuentes['enorme'], texto, (ANCHO // 2, ALTO // 2), DORADO, 'centro')


def dibujar_cartel(pantalla, fuentes, titulo, renglones, pie):
    """Dibuja un cartel centrado, para anunciar el resultado.

    Entradas:
        pantalla, fuentes
        titulo:    texto grande de arriba
        renglones: lista de tuplas (texto izquierdo, texto derecho, color)
        pie:       texto chico de abajo
    """
    alto = 170 + len(renglones) * 38
    zona = pygame.Rect(0, 0, 620, alto)
    zona.center = (ANCHO // 2, ALTO // 2)
    velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)        # oscurece un poco el juego que queda detrás
    velo.fill((0, 0, 0, 110))
    pantalla.blit(velo, (0, 0))
    pygame.draw.rect(pantalla, NEGRO, zona, border_radius=12)
    pygame.draw.rect(pantalla, ROJO, zona, 5, border_radius=12)
    escribir(pantalla, fuentes['titulo'], titulo, (zona.centerx, zona.y + 56), BLANCO, 'centro')
    for i, (izquierda, derecha, color) in enumerate(renglones):
        y = zona.y + 112 + i * 38
        escribir(pantalla, fuentes['normal'], izquierda, (zona.x + 60, y), color)
        escribir(pantalla, fuentes['normal'], derecha, (zona.right - 60, y), color, 'derecha')
    escribir(pantalla, fuentes['chica'], pie, (zona.centerx, zona.bottom - 28), GRIS, 'centro')


def cartel_de_carrera(pantalla, fuentes, juego, orden):
    """Anuncia el resultado de una carrera (atrapa gemas o Maze Runner).

    Entradas: la pantalla, las fuentes, la partida y los corredores ya ordenados.
    El cartel dice el lugar del jugador y los tiempos de quienes ya llegaron.
    Los demás siguen corriendo detrás del cartel.
    """
    jugador = juego['jugador']
    renglones = []
    for lugar, corredor in enumerate(orden):
        tiempo = texto_de_tiempo(corredor['final']) if corredor['final'] is not None else 'sigue corriendo'
        renglones.append((f"{lugar + 1}.  {corredor['nombre']}", tiempo, DORADO if corredor is jugador else BLANCO))
    if jugador is None:
        titulo = f"Ganó {orden[0]['nombre']}"
    elif orden[0] is jugador:
        titulo = '¡Ganaste!'
    else:
        titulo = f'Quedaste en el lugar {orden.index(jugador) + 1}'
    dibujar_cartel(pantalla, fuentes, titulo, renglones, 'Espacio o Enter: otra carrera.   R: reiniciar.   Esc: menú.')


AYUDA_DE_MIRAR = 'Rueda: acercar.   Arrastrar o W A S D: mover.   Tab: seguir a otro.   0: vista general.   R: reiniciar.   Esc: menú.'
AYUDA_DE_JUGAR = 'Flechas o W A S D: moverte.   C: acercar.   R: reiniciar.   Esc: menú.'


# ---------------------------------------------------------------- atrapa gemas

ZONA_GRANDE_GEMAS = pygame.Rect(290, 132, 700, 560)


def zona_de_tablero_de_gemas(numero):
    """Da el rectángulo de la pantalla donde va el tablero de un competidor.

    Entrada: el número del competidor, contando desde 0.
    Salida:  el rectángulo. Los tableros se acomodan en filas de tres.
    """
    return pygame.Rect(46 + (numero % 3) * 406, 122 + (numero // 3) * 310, 376, 256)


def dibujar_tablero_de_gemas(pantalla, juego, numero, zona, t, entorno):
    """Dibuja el tablero de un competidor de atrapa gemas.

    Entradas: la pantalla, la partida, el número del competidor, su zona, el tiempo y el entorno.
    Salida:   la vista con la que se dibujó.
    Cada competidor tiene su propio tablero y ve el terreno de la gema que busca.
    """
    corredor = juego['corredores'][numero]
    camara = juego['camara']
    mapa = mapa_de(juego, corredor)
    # La cámara solo acerca el tablero del corredor al que sigue.
    if camara['seguir'] == numero:
        vista = vista_de_camara(zona, mapa, camara, juego['corredores'])
    else:
        vista = crear_vista(zona, mapa)
    camara['casilla_px'] = (vista['ancho'], vista['alto'])
    radio = 9 * vista['escala']

    def salida():
        """Marca la casilla de salida con un punto verde."""
        centro = en_pantalla(vista, *SALIDA_GEMAS)
        pygame.draw.circle(pantalla, VERDE_INICIO, centro, radio)
        pygame.draw.circle(pantalla, NEGRO, centro, radio, max(1, int(2 * vista['escala'])))

    planos = [salida]
    if corredor['algoritmo'] is not None:
        planos.append(lambda: dibujar_ruta(pantalla, vista, corredor))       # la ruta que planeó el rival
    altos = [(posicion(corredor)[0], lambda: dibujar_personaje(pantalla, vista, corredor, t, entorno))]
    # Solo hay una gema a la vista: la que le toca a este competidor.
    if corredor['final'] is None:
        gema = juego['gemas'][corredor['siguiente']]
        altos.append((gema[0] - 0.1, lambda: dibujar_gema(pantalla, vista, gema, t)))

    # Si el terreno acaba de cambiar, se dibuja la transformación desde el anterior.
    anterior, progreso = None, 1.0
    if corredor['cambio'] < DURACION_DEL_CAMBIO and corredor['final'] is None:
        if corredor['siguiente'] == 0:
            previo = mapa_vacio(LADO_GEMAS, LADO_GEMAS)          # al empezar, el tablero estaba vacío
        else:
            previo = juego['mapas'][corredor['siguiente'] - 1]
        anterior, progreso = casillas_que_cambian(previo, mapa), corredor['cambio'] / DURACION_DEL_CAMBIO
    dibujar_tablero(pantalla, vista, mapa, planos, altos, t, entorno, juego['adornos'][numero], anterior, progreso)
    return vista


def dibujar_gemas(pantalla, fuentes, juego, t, entorno, efectos, con_interfaz=True):
    """Dibuja toda la pantalla de atrapa gemas.

    Entradas: la pantalla, las fuentes, la partida, el tiempo, el entorno y los efectos.
              con_interfaz es False para la partida que se juega sola detrás de
              la portada: se dibujan los tableros, pero no la barra ni los letreros.
    Los tableros van en filas de tres, cada uno con el lugar que lleva su
    competidor. Al solo mirar, se puede ver en grande el tablero de uno.
    """
    pantalla.fill(color_del_cielo(entorno))
    empezar_cuadro(entorno)
    orden = clasificacion(juego)
    jugador = juego['jugador']
    # Al solo mirar, si la cámara sigue a alguien, se ve solo su tablero y en grande.
    solo = juego['camara']['seguir'] if jugador is None else None

    vistas = {}
    for numero, corredor in enumerate(juego['corredores']):
        if solo is None or numero == solo:
            zona = zona_de_tablero_de_gemas(numero) if solo is None else ZONA_GRANDE_GEMAS
            vistas[numero] = dibujar_tablero_de_gemas(pantalla, juego, numero, zona, t, entorno)
    dibujar_cielo(pantalla, entorno, t)
    lanzar_eventos(efectos, juego, vistas)
    dibujar_efectos(pantalla, efectos)

    if not con_interfaz:
        return
    # La interfaz se dibuja al final, para que la noche no la oscurezca.
    dibujar_barra(pantalla, fuentes, 'Atrapa gemas' if jugador is not None else 'Mirar: atrapa gemas', juego['reloj'])
    if jugador is not None:
        escribir(pantalla, fuentes['normal'], f'Vas en el lugar {orden.index(jugador) + 1} de {len(orden)}',
                 (ANCHO // 2, 24), DORADO, 'centro')
        escribir(pantalla, fuentes['chica'], AYUDA_DE_JUGAR, (ANCHO // 2, 54), GRIS, 'centro')
    else:
        escribir(pantalla, fuentes['normal'], f"Va ganando {orden[0]['nombre']}", (ANCHO // 2, 24), DORADO, 'centro')
        # La ayuda de mirar es más ancha que el hueco entre el título y el reloj,
        # así que va al pie de la pantalla, en la franja libre debajo de los tableros.
        escribir(pantalla, fuentes['chica'], AYUDA_DE_MIRAR, (ANCHO // 2, 706), GRIS_CLARO, 'centro')

    for numero, vista in vistas.items():
        # Encabezado del tablero: el lugar que lleva, su color, su nombre y su avance.
        corredor = juego['corredores'][numero]
        zona = vista['zona']
        lugar = orden.index(corredor) + 1
        y = zona.y - 40
        escribir(pantalla, fuentes['grande'], lugar, (zona.x, y - 8), DORADO if lugar == 1 else BLANCO)
        dibujar_ficha(pantalla, corredor['color'], pygame.Rect(zona.x + 34, y, 16, 22))
        escribir(pantalla, fuentes['normal'], corredor['nombre'], (zona.x + 58, y - 4))
        if corredor['final'] is not None:
            avance = 'terminó en ' + texto_de_tiempo(corredor['final'])
        elif corredor['pensando'] > 0:
            avance = f"pensando...  gema {corredor['siguiente'] + 1} de {CANTIDAD_DE_GEMAS}"
        else:
            avance = f"gema {corredor['siguiente'] + 1} de {CANTIDAD_DE_GEMAS}"
        escribir(pantalla, fuentes['chica'], avance, (zona.right, y), GRIS_CLARO, 'derecha')

    dibujar_cuenta(pantalla, fuentes, juego)
    if juego['anuncio'] and solo is None:
        cartel_de_carrera(pantalla, fuentes, juego, orden)


# ---------------------------------------------------------------- captura la bandera

ZONA_BANDERA = pygame.Rect(120, 190, 1040, 470)


def zonas_de_rival(mirando=False):
    """Da los rectángulos de los botones para elegir al rival del lado derecho.

    Entrada: mirando es True en el modo de solo mirar, donde los botones van a la
             derecha para dejar lugar a los del lado izquierdo.
    Salida:  lista de 6 rectángulos, en el mismo orden que OPCIONES_DE_RIVAL.
    """
    ancho = 92 if mirando else 150
    total = len(OPCIONES_DE_RIVAL) * (ancho + 6)
    izquierda = ANCHO - 30 - total if mirando else (ANCHO - total) // 2
    return [pygame.Rect(izquierda + i * (ancho + 6), 674, ancho, 34) for i in range(len(OPCIONES_DE_RIVAL))]


def zonas_de_izquierda():
    """Da los rectángulos de los botones para elegir el algoritmo del lado izquierdo, al solo mirar.

    Salida: lista de 5 rectángulos, uno por algoritmo.
    """
    return [pygame.Rect(30 + i * 98, 674, 92, 34) for i in range(len(ALGORITMOS))]


def ruta_dorada(juego):
    """Calcula la ruta más corta desde el jugador hasta su propia bandera.

    Entrada: la partida.
    Salida:  lista de casillas. Se dibuja en dorado mientras el jugador lleva
             la bandera rival, para mostrarle a dónde llevarla.
    """
    jugador = juego['jugador']
    desde = jugador['destino'] or jugador['casilla']
    ruta, exploradas = dijkstra(juego['mapa'], desde, bandera_de(juego, jugador))
    return ruta or []


def dibujar_bandera_juego(pantalla, fuentes, juego, t, entorno, efectos):
    """Dibuja toda la pantalla de captura la bandera.

    Entradas: la pantalla, las fuentes, la partida, el tiempo, el entorno y los efectos.
    """
    pantalla.fill(color_del_cielo(entorno))
    empezar_cuadro(entorno)
    jugador, rival = juego['jugador'], juego['rival']
    mapa = juego['mapa']
    humano = juego['humano']
    en_juego = juego['fase'] == 'carrera'
    vista = vista_de_camara(ZONA_BANDERA, mapa, juego['camara'], juego['corredores'])
    juego['camara']['casilla_px'] = (vista['ancho'], vista['alto'])

    def salidas():
        """Dibuja las dos salidas: un óvalo del color de su dueño, pegado al piso."""
        for corredor in (jugador, rival):
            x, y = en_pantalla(vista, *corredor['salida'])
            w, h = vista['ancho'] * 0.8, vista['alto'] * 0.8
            pygame.draw.ellipse(pantalla, corredor['color'], (x - w / 2, y - h / 2, w, h))
            pygame.draw.ellipse(pantalla, BLANCO, (x - w / 2, y - h / 2, w, h), 3)

    def rutas():
        """Dibuja la ruta planeada de cada rival y, si el jugador lleva la bandera, su ruta dorada."""
        dibujar_ruta(pantalla, vista, rival)
        if not humano:
            dibujar_ruta(pantalla, vista, jugador)
        elif jugador['lleva'] and en_juego:
            dibujar_ruta(pantalla, vista, jugador, DORADO, ruta_dorada(juego))

    def destino_del_jugador():
        """Mientras el jugador lleva la bandera, hace latir con aros dorados el lugar a donde va."""
        if humano and jugador['lleva'] and en_juego:
            x, y = en_pantalla(vista, *bandera_de(juego, jugador))
            for k in range(3):
                radio = (20 + ((t * 40 + k * 22) % 60)) * vista['escala']     # tres aros que crecen uno tras otro
                pygame.draw.ellipse(pantalla, DORADO, (x - radio, y - radio * 0.7, radio * 2, radio * 1.4), 4)

    altos = [(posicion(jugador)[0], lambda: dibujar_personaje(pantalla, vista, jugador, t, entorno, rival['color'] if jugador['lleva'] else None)),
             (posicion(rival)[0], lambda: dibujar_personaje(pantalla, vista, rival, t, entorno, jugador['color'] if rival['lleva'] else None))]
    # Cada bandera está clavada en su casilla mientras el otro no se la lleve.
    for dueño, otro in ((jugador, rival), (rival, jugador)):
        if not otro['lleva']:
            casilla = bandera_de(juego, dueño)
            pie = en_pantalla(vista, *casilla)
            altos.append((casilla[0] - 0.2, lambda pie=pie, dueño=dueño:
                          dibujar_bandera(pantalla, vista, pie, dueño['color'])))
    anterior, progreso = None, 1.0
    if juego['cambio'] < DURACION_DEL_CAMBIO:
        anterior, progreso = casillas_que_cambian(juego['mapa_viejo'], mapa), juego['cambio'] / DURACION_DEL_CAMBIO
    dibujar_tablero(pantalla, vista, mapa, [salidas, rutas, destino_del_jugador], altos, t, entorno,
                    juego['adornos'], anterior, progreso)

    if humano and jugador['lleva'] and en_juego:
        # Una flecha que sube y baja sobre el lugar a donde hay que llevar la bandera.
        x, y = en_pantalla(vista, *bandera_de(juego, jugador))
        s = vista['escala']
        y = y - 96 * s + sin(t * 6) * 8
        flecha = [(x - 15 * s, y), (x + 15 * s, y), (x + 15 * s, y + 20 * s), (x + 30 * s, y + 20 * s),
                  (x, y + 48 * s), (x - 30 * s, y + 20 * s), (x - 15 * s, y + 20 * s)]
        pantalla.set_clip(ZONA_BANDERA.inflate(0, 60))
        pygame.draw.polygon(pantalla, DORADO, flecha)
        pygame.draw.polygon(pantalla, NEGRO, flecha, 3)
        pantalla.set_clip(None)

    dibujar_cielo(pantalla, entorno, t)
    lanzar_eventos(efectos, juego, {0: vista})
    dibujar_efectos(pantalla, efectos)

    # ---- La interfaz, encima de todo.
    dibujar_barra(pantalla, fuentes, 'Captura la bandera' if humano else 'Mirar: captura la bandera', juego['reloj'])
    # El marcador, al centro de la barra.
    izquierdo = 'Tú' if humano else jugador['nombre']
    escribir(pantalla, fuentes['grande'], f"{izquierdo}  {jugador['puntos']}", (ANCHO // 2 - 24, 14), (255, 110, 110), 'derecha')
    escribir(pantalla, fuentes['grande'], ':', (ANCHO // 2, 34), BLANCO, 'centro')
    nombre = escribir(pantalla, fuentes['grande'], f"{rival['puntos']}  {rival['nombre']}", (ANCHO // 2 + 24, 14))
    dibujar_ficha(pantalla, rival['color'], pygame.Rect(nombre.right + 10, 24, 18, 26))

    # Una franja oscura al pie, detrás de los botones, para que se lean aunque la vista esté acercada.
    franja = pygame.Surface((ANCHO, ALTO - 664), pygame.SRCALPHA)
    franja.fill((0, 0, 0, 150))
    pantalla.blit(franja, (0, 664))

    # El aviso fijo: qué hacer o qué está pasando.
    if not humano:
        mensaje, color = f"{jugador['nombre']} (rojo) contra {rival['nombre']}. Gana quien llegue a {PUNTOS_PARA_GANAR}.", BLANCO
    elif jugador['lleva'] and en_juego:
        mensaje, color = '¡Llevas la bandera! Llévala a donde está la tuya: sigue la ruta dorada.', DORADO
    elif rival['lleva'] and en_juego:
        mensaje, color = f"{rival['nombre']} te robó la bandera. Chócalo para recuperarla.", (255, 170, 170)
    else:
        mensaje, color = f"Roba la bandera de {rival['nombre']} y llévala a donde está la tuya.", BLANCO
    escribir(pantalla, fuentes['normal'], mensaje, (ANCHO // 2, 104), color, 'centro')
    ayuda = f'A {PUNTOS_PARA_GANAR} puntos.   ' + AYUDA_DE_JUGAR if humano else AYUDA_DE_MIRAR
    escribir(pantalla, fuentes['chica'], ayuda, (ANCHO // 2, 136), GRIS_CLARO, 'centro')

    # Los botones para elegir rival. El elegido va en rojo.
    for numero, (opcion, zona) in enumerate(zip(OPCIONES_DE_RIVAL, zonas_de_rival(not humano))):
        dibujar_boton(pantalla, fuentes, zona, f'{numero + 1} {opcion}', opcion == juego['eleccion'], COLOR_DE.get(opcion))
    if humano:
        escribir(pantalla, fuentes['chica'], 'Rival:', (zonas_de_rival()[0].x - 12, 682), GRIS_CLARO, 'derecha')
    else:
        # Al solo mirar, también se elige el algoritmo del lado izquierdo, que conserva el rojo.
        for nombre_de_algoritmo, zona in zip(ALGORITMOS, zonas_de_izquierda()):
            dibujar_boton(pantalla, fuentes, zona, nombre_de_algoritmo, nombre_de_algoritmo == jugador['nombre'], ROJO)
        # El letrero va corto para caber en el hueco entre los dos grupos de botones.
        escribir(pantalla, fuentes['chica'], 'Mayús + 1 a 5', (zonas_de_izquierda()[-1].right + 10, 682), GRIS_CLARO)

    if juego['aviso_resta'] > 0 and juego['fase'] != 'final':
        # El aviso de choque, de robo o de punto, sobre una franja oscura.
        franja = pygame.Surface((ANCHO, 76), pygame.SRCALPHA)
        franja.fill((0, 0, 0, 190))
        pantalla.blit(franja, (0, ALTO // 2 - 38))
        escribir(pantalla, fuentes['grande'], juego['aviso'], (ANCHO // 2, ALTO // 2), DORADO, 'centro')
    dibujar_cuenta(pantalla, fuentes, juego)

    if juego['fase'] == 'final':
        gano_izquierda = jugador['puntos'] > rival['puntos']
        ganador = jugador if gano_izquierda else rival
        titulo = '¡Ganaste!' if humano and gano_izquierda else f"Ganó {nombre_para_aviso(juego, ganador)}"
        renglones = [(izquierdo, jugador['puntos'], DORADO), (rival['nombre'], rival['puntos'], BLANCO),
                     ('Tiempo', texto_de_tiempo(juego['reloj']), GRIS)]
        dibujar_cartel(pantalla, fuentes, titulo, renglones, 'Espacio o Enter: otra partida.   R: reiniciar.   Esc: menú.')


# ---------------------------------------------------------------- Maze Runner

ZONA_LABERINTO = pygame.Rect(24, 104, 1232, 600)
BOTON_ACERCAR = pygame.Rect(24, 80, 150, 30)
BOTON_ANTERIOR = pygame.Rect(184, 80, 44, 30)
BOTON_SIGUIENTE = pygame.Rect(234, 80, 44, 30)


def dibujar_laberinto(pantalla, fuentes, juego, t, entorno, efectos):
    """Dibuja toda la pantalla de Maze Runner.

    Entradas: la pantalla, las fuentes, la partida, el tiempo, el entorno y los efectos.
    Todos corren en el mismo laberinto. Arriba van las posiciones y el contador
    de cuánto falta para el siguiente cambio.
    """
    pantalla.fill(color_del_cielo(entorno))
    empezar_cuadro(entorno)
    mapa = juego['mapa']
    jugador = juego['jugador']
    camara = juego['camara']
    orden = clasificacion(juego)
    vista = vista_de_camara(ZONA_LABERINTO, mapa, camara, juego['corredores'])
    camara['casilla_px'] = (vista['ancho'], vista['alto'])

    def marcas():
        """Marca la partida con un punto verde y dibuja la ruta planeada de cada rival."""
        centro = en_pantalla(vista, *PARTIDA_LABERINTO)
        pygame.draw.circle(pantalla, VERDE_INICIO, centro, 9 * vista['escala'])
        pygame.draw.circle(pantalla, NEGRO, centro, 9 * vista['escala'], 2)
        for corredor in juego['corredores']:
            if corredor['algoritmo'] is not None and corredor['final'] is None:
                dibujar_ruta(pantalla, vista, corredor)

    # La salida es una bandera dorada. Los personajes se dibujan del último al primero,
    # para que el que va ganando quede encima.
    pie = en_pantalla(vista, *META_LABERINTO)
    altos = [(META_LABERINTO[0] - 0.2, lambda: dibujar_bandera(pantalla, vista, pie, DORADO, 1.2))]
    for corredor in reversed(orden):
        altos.append((posicion(corredor)[0], lambda corredor=corredor: dibujar_personaje(pantalla, vista, corredor, t, entorno)))

    # Los pasillos que acaban de cambiar se ven subir o bajar.
    anterior, progreso = None, 1.0
    if juego['cambio'] < DURACION_DEL_CAMBIO:
        anterior = {casilla: '.' if que == 'cerrado' else '#' for casilla, que in juego['recientes'].items()}
        progreso = juego['cambio'] / DURACION_DEL_CAMBIO
    dibujar_tablero(pantalla, vista, mapa, [marcas], altos, t, entorno, juego['adornos'], anterior, progreso)
    dibujar_cielo(pantalla, entorno, t)
    lanzar_eventos(efectos, juego, {0: vista})
    dibujar_efectos(pantalla, efectos)

    # ---- La interfaz.
    dibujar_barra(pantalla, fuentes, 'Maze Runner', juego['reloj'])
    # Las posiciones en vivo, en una fila de fichas.
    x = 306
    for lugar, corredor in enumerate(orden):
        zona = pygame.Rect(x + lugar * 122, 8, 116, 30)
        pygame.draw.rect(pantalla, GRIS_OSCURO, zona, border_radius=6)
        if camara['seguir'] is not None and juego['corredores'][camara['seguir']] is corredor:
            pygame.draw.rect(pantalla, DORADO, zona, 2, border_radius=6)     # a quién sigue la vista
        dibujar_ficha(pantalla, corredor['color'], pygame.Rect(zona.x + 30, zona.y + 6, 12, 18))
        escribir(pantalla, fuentes['normal'], lugar + 1, (zona.x + 8, zona.y), DORADO if lugar == 0 else BLANCO)
        escribir(pantalla, fuentes['chica'], corredor['nombre'], (zona.x + 48, zona.y + 4))
    # El contador: los segundos enteros que faltan para el siguiente cambio.
    faltan = ceil(juego['proximo']) if juego['fase'] == 'carrera' else ceil(SEGUNDOS_ENTRE_CAMBIOS)
    escribir(pantalla, fuentes['normal'], f'El laberinto cambia en {faltan}', (ANCHO // 2, 54), DORADO, 'centro')

    franja = pygame.Surface((ANCHO, 38), pygame.SRCALPHA)
    franja.fill((0, 0, 0, 150))
    pantalla.blit(franja, (0, 77))
    if jugador is not None:
        dibujar_boton(pantalla, fuentes, BOTON_ACERCAR, 'Acercar (C)', camara['seguir'] is not None and jugador['final'] is None)
        if jugador['final'] is not None:
            # Cuando el jugador ya terminó, dos flechas para pasar la vista de un competidor a otro.
            dibujar_boton(pantalla, fuentes, BOTON_ANTERIOR, '<')
            dibujar_boton(pantalla, fuentes, BOTON_SIGUIENTE, '>')
            escribir(pantalla, fuentes['chica'], 'Ver a otro competidor (flechas)', (BOTON_SIGUIENTE.right + 10, 86), BLANCO)
        else:
            escribir(pantalla, fuentes['chica'], 'Flechas o W A S D: moverte.   R: reiniciar.   Esc: menú.', (BOTON_ACERCAR.right + 12, 86), BLANCO)
    else:
        escribir(pantalla, fuentes['chica'], AYUDA_DE_MIRAR, (24, 86), BLANCO)

    dibujar_cuenta(pantalla, fuentes, juego)
    # El cartel se quita al empezar a ver a otro competidor, para no tapar el laberinto.
    if juego['anuncio'] and not juego.get('cartel_cerrado'):
        cartel_de_carrera(pantalla, fuentes, juego, orden)

# ============================================================================
# 11. MODO APRENDER
# Muestra un algoritmo paso a paso: qué casilla sale de la estructura, cuáles
# entran, el renglón de código que se ejecuta y cómo va la estructura de datos.
# ============================================================================

# Cinco mapas, cada uno pensado para que se note una diferencia entre los algoritmos.
MAPAS_DE_APRENDER = [
    ('Campo abierto', """
............
.I..........
............
............
............
..........M.
............
............
"""),
    ('Pantano', """
............
....AAAA....
.I..AAAA..M.
....AAAA....
....AAAA....
............
............
............
"""),
    ('Pared', """
.....AAA....
....#####...
........#...
.I......#.M.
........#...
....#####...
............
............
"""),
    ('Laberinto', """
############
#I...#.....#
#.##.#.###.#
#.#....#...#
#.#.####.#.#
#...#....#M#
#.#...##...#
############
"""),
    ('Sin salida', """
............
.I......###.
........#M#.
........###.
............
............
............
............
"""),
]
QUE_ENSEÑA = {'Campo abierto': 'Todo cuesta 1: se ve quién explora de más para llegar a la misma ruta.',
              'Pantano': 'Cruzar el agua es corto pero caro: conviene rodear. Menos pasos no es menos costo.',
              'Pared': 'Una pared en U engaña al voraz: se mete en ella y sale por el lado del agua. A* rodea por el lado barato.',
              'Laberinto': 'Los muros obligan a alejarse de la meta: la estimación ayuda menos.',
              'Sin salida': 'La meta está encerrada: para saberlo hay que revisar todo lo alcanzable.'}

# El código que se muestra de cada algoritmo, renglón por renglón.
CODIGO = {
    'BFS': ['cola = deque([inicio])',
            'padres = {inicio: None}',
            'while cola:',
            '    actual = cola.popleft()',
            '    if actual == meta:',
            '        return reconstruir_ruta(padres, meta)',
            '    for vecina, costo in vecinos(mapa, actual):',
            '        if vecina not in padres:',
            '            padres[vecina] = actual',
            '            cola.append(vecina)',
            'return None'],
    'DFS': ['pila = [inicio]',
            'padres = {inicio: None};  vistas = set()',
            'while pila:',
            '    actual = pila.pop()',
            '    if actual in vistas: continue',
            '    vistas.add(actual)',
            '    if actual == meta:',
            '        return reconstruir_ruta(padres, meta)',
            '    for vecina, costo in reversed(vecinos(mapa, actual)):',
            '        if vecina not in vistas:',
            '            padres[vecina] = actual',
            '            pila.append(vecina)',
            'return None'],
    'Dijkstra': ['cola = [(0, inicio)]',
                 'costos = {inicio: 0};  padres = {inicio: None}',
                 'while cola:',
                 '    costo, actual = heapq.heappop(cola)',
                 '    if actual in vistas: continue',
                 '    vistas.add(actual)',
                 '    if actual == meta:',
                 '        return reconstruir_ruta(padres, meta)',
                 '    for vecina, paso in vecinos(mapa, actual):',
                 '        nuevo = costo + paso',
                 '        if vecina not in costos or nuevo < costos[vecina]:',
                 '            costos[vecina] = nuevo;  padres[vecina] = actual',
                 '            heapq.heappush(cola, (nuevo, vecina))',
                 'return None'],
    'Voraz': ['cola = [(estimacion(inicio, meta), inicio)]',
              'padres = {inicio: None}',
              'while cola:',
              '    distancia, actual = heapq.heappop(cola)',
              '    if actual == meta:',
              '        return reconstruir_ruta(padres, meta)',
              '    for vecina, costo in vecinos(mapa, actual):',
              '        if vecina not in padres:',
              '            padres[vecina] = actual',
              '            heapq.heappush(cola, (estimacion(vecina, meta), vecina))',
              'return None'],
    'A*': ['cola = [(estimacion(inicio, meta), inicio)]',
           'costos = {inicio: 0};  padres = {inicio: None}',
           'while cola:',
           '    prioridad, actual = heapq.heappop(cola)',
           '    if actual in vistas: continue',
           '    vistas.add(actual)',
           '    if actual == meta:',
           '        return reconstruir_ruta(padres, meta)',
           '    for vecina, paso in vecinos(mapa, actual):',
           '        nuevo = costos[actual] + paso',
           '        if vecina not in costos or nuevo < costos[vecina]:',
           '            costos[vecina] = nuevo;  padres[vecina] = actual',
           '            heapq.heappush(cola, (nuevo + estimacion(vecina, meta), vecina))',
           'return None'],
}
# En qué renglón del código cae cada momento del recorrido, para resaltarlo.
RENGLONES = {'BFS': {'inicio': 0, 'sale': 3, 'meta': 5, 'entran': 9, 'fin': 10},
             'DFS': {'inicio': 0, 'sale': 3, 'repetida': 4, 'meta': 7, 'entran': 11, 'fin': 12},
             'Dijkstra': {'inicio': 0, 'sale': 3, 'repetida': 4, 'meta': 7, 'entran': 12, 'fin': 13},
             'Voraz': {'inicio': 0, 'sale': 3, 'meta': 5, 'entran': 9, 'fin': 10},
             'A*': {'inicio': 0, 'sale': 3, 'repetida': 4, 'meta': 7, 'entran': 12, 'fin': 13}}
ESTRUCTURA_DE = {'BFS': 'cola', 'DFS': 'pila', 'Dijkstra': 'prioridad', 'Voraz': 'prioridad', 'A*': 'prioridad'}
VELOCIDADES_DE_APRENDER = [('lenta', 1.5), ('media', 5.0), ('rápida', 16.0)]      # nombre y pasos por segundo


def mapa_de_texto(texto):
    """Convierte el texto de un mapa en un mapa. Es la misma idea que leer_mapa del notebook.

    Entrada: el mapa escrito con un carácter por casilla: '.' llano, 'B' bosque,
             'A' agua, '#' muro, 'I' inicio y 'M' meta.
    Salida:  la terna (mapa, inicio, meta).
    """
    lineas = texto.strip('\n').split('\n')
    columnas = max(len(linea) for linea in lineas)
    terreno = {}
    inicio = meta = None
    for f, linea in enumerate(lineas):
        for c, caracter in enumerate(linea.ljust(columnas, '#')):     # lo que le falta a una fila corta es muro
            if caracter == 'I':
                inicio, caracter = (f, c), '.'
            elif caracter == 'M':
                meta, caracter = (f, c), '.'
            terreno[(f, c)] = caracter
    return {'terreno': terreno, 'filas': len(lineas), 'columnas': columnas}, inicio, meta


def pasos_de_aprender(nombre, mapa, inicio, meta):
    """Recorre un algoritmo y guarda una foto de cada momento, para mostrarlo paso a paso.

    Entradas: el nombre del algoritmo, el mapa, el inicio y la meta.

    Salida: lista de pasos. Cada paso es un diccionario con
        'renglon':    qué renglón del código se está ejecutando
        'texto':      la explicación en palabras
        'actual':     la casilla que se está explorando, o None
        'exploradas': las casillas ya exploradas
        'estructura': lo que hay en la pila o en la cola: lista de (valor, casilla),
                      acomodada con la próxima en salir al principio. En la pila
                      y en la cola simple el valor es None.
        'nuevas':     las casillas que acaban de entrar
        'ruta':       la ruta final, cuando ya se encontró

    Hace lo mismo que las funciones de la sección 1, pero deteniéndose a anotar.
    """
    tipo = ESTRUCTURA_DE[nombre]
    renglon = RENGLONES[nombre]
    pasos = []
    exploradas = []
    estructura = []                                  # la pila, la cola o la cola de prioridad
    padres = {inicio: None}
    costos = {inicio: 0}
    vistas = set()

    def prioridad_de(casilla):
        """El valor con el que una casilla entra a la cola de prioridad, según el algoritmo."""
        if nombre == 'Dijkstra':
            return costos[casilla]
        if nombre == 'Voraz':
            return estimacion(casilla, meta)
        return costos[casilla] + estimacion(casilla, meta)

    def desempate_de(casilla):
        """El segundo dato de cada elemento de la cola, que decide los empates.

        En A* es la estimación: entre dos casillas con el mismo valor sale la más
        cercana a la meta. En Dijkstra y en el voraz no hay segundo dato, así que
        los empates los decide la posición de la casilla, igual que en la sección 1.
        """
        return estimacion(casilla, meta) if nombre == 'A*' else 0

    def anotar(momento, texto, actual=None, nuevas=(), ruta=None):
        """Guarda la foto de este momento."""
        if tipo == 'cola':
            contenido = [(None, casilla) for casilla in estructura]              # sale la primera
        elif tipo == 'pila':
            contenido = [(None, casilla) for casilla in reversed(estructura)]    # sale la última que entró
        else:
            contenido = [(elemento[0], elemento[-1]) for elemento in sorted(estructura)]   # sale la de menor valor
        pasos.append({'renglon': renglon[momento], 'texto': texto, 'actual': actual, 'exploradas': list(exploradas),
                      'estructura': contenido, 'nuevas': set(nuevas), 'ruta': ruta})

    # ---- Al empezar, la estructura solo tiene el inicio.
    if tipo == 'prioridad':
        heapq.heappush(estructura, (prioridad_de(inicio), desempate_de(inicio), inicio))
    else:
        estructura.append(inicio)
    nombre_de = {'cola': 'La cola', 'pila': 'La pila', 'prioridad': 'La cola de prioridad'}[tipo]
    anotar('inicio', f'{nombre_de} empieza solo con la casilla de inicio, {inicio}.', nuevas=[inicio])

    while estructura:
        # ---- Sale una casilla. Cuál sale es lo que distingue a cada algoritmo.
        if tipo == 'cola':
            actual = estructura.pop(0)
            porque = 'es la que lleva más tiempo esperando: la primera que entró es la primera que sale.'
        elif tipo == 'pila':
            actual = estructura.pop()
            porque = 'es la última que entró: la pila entrega primero lo más reciente.'
        else:
            valor, desempate, actual = heapq.heappop(estructura)
            if nombre == 'Dijkstra':
                porque = f'es la de menor costo acumulado desde el inicio: {valor}.'
            elif nombre == 'Voraz':
                porque = f'es la que parece más cerca de la meta: le faltan {valor} casillas en línea recta, sin diagonales.'
            else:
                porque = (f'es la de menor suma: {costos[actual]} ya gastado más {estimacion(actual, meta)} que se estima '
                          f'que falta, {valor} en total. En empates gana la más cercana a la meta.')

        if nombre in ('DFS', 'Dijkstra', 'A*') and actual in vistas:
            anotar('repetida', f'Sale {actual}, pero ya se había explorado antes: estaba repetida. Se ignora.', actual)
            continue
        vistas.add(actual)
        exploradas.append(actual)
        anotar('sale', f'Sale {actual} porque {porque} Queda explorada: van {len(exploradas)}.', actual)

        if actual == meta:
            ruta = reconstruir_ruta(padres, meta)
            costo = sum(COSTOS[mapa['terreno'][casilla]] for casilla in ruta[1:])
            anotar('meta', f'Es la meta. La ruta se arma caminando hacia atrás por los padres: {len(ruta) - 1} pasos, '
                           f'costo {costo}. Se exploraron {len(exploradas)} casillas.', actual, ruta=ruta)
            return pasos

        # ---- Entran sus vecinas, según la regla de cada algoritmo.
        entran, ignoradas = [], []
        lista = vecinos(mapa, actual)
        if tipo == 'pila':
            lista = list(reversed(lista))            # al revés, para que la de arriba salga primero
        for vecina, paso in lista:
            if nombre in ('BFS', 'Voraz'):
                sirve = vecina not in padres         # solo las que nunca se habían descubierto
            elif nombre == 'DFS':
                sirve = vecina not in vistas
            else:
                nuevo = costos[actual] + paso
                sirve = vecina not in costos or nuevo < costos[vecina]   # primera vez, o un camino más barato
                if sirve:
                    costos[vecina] = nuevo
            if not sirve:
                ignoradas.append(vecina)
                continue
            padres[vecina] = actual
            entran.append(vecina)
            if tipo == 'prioridad':
                heapq.heappush(estructura, (prioridad_de(vecina), desempate_de(vecina), vecina))
            else:
                estructura.append(vecina)
        texto = f'No es la meta. Se revisan sus vecinas. Entran {len(entran)}: {entran}.' if entran else 'No es la meta, y ninguna de sus vecinas entra.'
        if ignoradas:
            texto += f' Se ignoran {len(ignoradas)}, que ya se conocían.'
        anotar('entran', texto, actual, entran)

    anotar('fin', f'{nombre_de} se quedó vacía sin llegar a la meta: no hay camino. Se exploraron {len(exploradas)} casillas.')
    return pasos


def crear_aprender(algoritmo='BFS', numero_de_mapa=0):
    """Prepara el modo Aprender para un algoritmo y un mapa.

    Entradas: el nombre del algoritmo y el número del mapa.

    Salida: un diccionario con
        'algoritmo', 'numero_de_mapa'
        'mapa', 'inicio', 'meta'
        'pasos':     todas las fotos del recorrido
        'paso':      en cuál se está
        'auto':      True si avanza solo
        'velocidad': la posición en VELOCIDADES_DE_APRENDER
        'cuenta':    fracción de paso acumulada mientras avanza solo
        'tabla':     por cada algoritmo, (exploradas, pasos, costo, puntaje); sin ruta, los tres últimos son None
    """
    nombre_del_mapa, texto = MAPAS_DE_APRENDER[numero_de_mapa]
    mapa, inicio, meta = mapa_de_texto(texto)
    tabla = {}
    for nombre, funcion in ALGORITMOS.items():
        ruta, exploradas = funcion(mapa, inicio, meta)
        if ruta is None:
            tabla[nombre] = (len(exploradas), None, None, None)
        else:
            costo = sum(COSTOS[mapa['terreno'][casilla]] for casilla in ruta[1:])
            # El mismo puntaje del notebook y del editor: costo * 10 000 + casillas exploradas.
            tabla[nombre] = (len(exploradas), len(ruta) - 1, costo, costo * 10000 + len(exploradas))
    return {'algoritmo': algoritmo, 'numero_de_mapa': numero_de_mapa, 'mapa': mapa, 'inicio': inicio, 'meta': meta,
            'pasos': pasos_de_aprender(algoritmo, mapa, inicio, meta), 'paso': 0, 'auto': False, 'velocidad': 1,
            'cuenta': 0.0, 'tabla': tabla}


def actualizar_aprender(aprender, segundos):
    """Avanza el modo Aprender cuando está en automático.

    Entradas: el estado del modo y los segundos que pasaron desde el cuadro anterior.
    """
    if not aprender['auto']:
        return
    aprender['cuenta'] += segundos * VELOCIDADES_DE_APRENDER[aprender['velocidad']][1]
    while aprender['cuenta'] >= 1:                   # con la velocidad rápida pueden tocar varios pasos por cuadro
        aprender['cuenta'] -= 1
        if aprender['paso'] < len(aprender['pasos']) - 1:
            aprender['paso'] += 1
        else:
            aprender['auto'] = False                 # llegó al final: se detiene solo


# ---------------------------------------------------------------- dibujo del modo Aprender

LADO_APRENDER = 44                                   # lado de cada casilla; aquí el mapa se ve de frente, sin inclinar
ORIGEN_APRENDER = (24, 92)
ZONA_CODIGO = pygame.Rect(572, 92, 684, 250)
ZONA_ESTRUCTURA = pygame.Rect(572, 350, 684, 170)
ZONA_TABLA = pygame.Rect(572, 528, 684, 180)
ZONA_EXPLICACION = pygame.Rect(24, 482, 528, 128)
COLOR_DE_PAPEL = {'explorada': (126, 87, 194), 'espera': (255, 179, 0), 'nueva': (255, 87, 34), 'actual': (213, 0, 0), 'ruta': (229, 57, 53)}
TEXTO_DE_PAPEL = [('actual', 'Explorando'), ('nueva', 'Acaba de entrar'), ('espera', 'Espera'), ('explorada', 'Explorada'), ('ruta', 'Ruta')]
BOTONES_DE_APRENDER = [('reiniciar', 'Reiniciar (R)'), ('anterior', 'Anterior'), ('siguiente', 'Siguiente'), ('auto', 'Automático'), ('velocidad', '')]


def zonas_de_aprender():
    """Da los rectángulos de todo lo que se puede oprimir en el modo Aprender.

    Salida: diccionario {(tipo, valor): rectángulo}. El tipo es 'algoritmo',
            'mapa' o 'boton'; el valor dice cuál.
    """
    zonas = {}
    for i, nombre in enumerate(ALGORITMOS):
        zonas[('algoritmo', nombre)] = pygame.Rect(250 + i * 122, 6, 116, 30)
    for i, (nombre, texto) in enumerate(MAPAS_DE_APRENDER):
        zonas[('mapa', i)] = pygame.Rect(250 + i * 136, 40, 130, 28)
    for i, (accion, texto) in enumerate(BOTONES_DE_APRENDER):
        zonas[('boton', accion)] = pygame.Rect(24 + i * 106, 664, 100 if i < 4 else 104, 34)
    return zonas


def puntos_de_estrella(centro, radio):
    """Calcula las 10 esquinas de una estrella de 5 puntas.

    Entradas: el centro (x, y) y el radio de las puntas.
    Salida:   lista de 10 puntos, alternando una punta y un hueco.
    """
    x, y = centro
    puntos = []
    for i in range(10):
        r = radio if i % 2 == 0 else radio * 0.42
        angulo = -pi / 2 + i * pi / 5
        puntos.append((x + r * cos(angulo), y + r * sin(angulo)))
    return puntos


def partir_texto(fuente, texto, ancho):
    """Parte un texto en renglones que quepan en un ancho.

    Entradas: el tipo de letra, el texto y el ancho disponible en pixeles.
    Salida:   lista de renglones.
    """
    renglones, actual = [], ''
    for palabra in texto.split(' '):
        prueba = (actual + ' ' + palabra).strip()
        if fuente.size(prueba)[0] <= ancho:
            actual = prueba
        else:
            renglones.append(actual)
            actual = palabra
    return renglones + [actual]


def dibujar_estructura(pantalla, fuentes, aprender, paso):
    """Dibuja la estructura de datos del algoritmo con lo que tiene en este paso.

    Entradas: la pantalla, las fuentes, el estado del modo y el paso actual.

    La pila es un vaso abierto solo por arriba: lo que entra queda encima y es
    lo primero que sale. La cola es un tubo abierto por los dos lados: se entra
    por un extremo y se sale por el otro. En la cola de prioridad cada caja
    lleva su valor y sale siempre la de menor valor.
    """
    zona = ZONA_ESTRUCTURA
    tipo = ESTRUCTURA_DE[aprender['algoritmo']]
    contenido = paso['estructura']
    pygame.draw.rect(pantalla, (30, 32, 38), zona, border_radius=8)
    titulo = {'pila': 'PILA: entra y sale por arriba', 'cola': 'COLA: entra por el fin y sale por el inicio',
              'prioridad': 'COLA DE PRIORIDAD: sale siempre la de menor valor'}[tipo]
    escribir(pantalla, fuentes['chica'], f'{titulo}.  Tiene {len(contenido)} casillas.', (zona.x + 12, zona.y + 8), GRIS_CLARO)

    def caja(x, y, ancho, alto, valor, casilla, sale):
        """Dibuja una caja con una casilla; la próxima en salir va resaltada en rojo."""
        pygame.draw.rect(pantalla, ROJO if sale else (255, 224, 130), (x, y, ancho, alto), border_radius=4)
        pygame.draw.rect(pantalla, NEGRO, (x, y, ancho, alto), 2, border_radius=4)
        color = BLANCO if sale else NEGRO
        if valor is None:
            escribir(pantalla, fuentes['codigo'], f'{casilla[0]},{casilla[1]}', (x + ancho / 2, y + alto / 2), color, 'centro')
        else:
            escribir(pantalla, fuentes['normal'], valor, (x + ancho / 2, y + alto * 0.34), color, 'centro')
            escribir(pantalla, fuentes['codigo'], f'{casilla[0]},{casilla[1]}', (x + ancho / 2, y + alto * 0.76), color, 'centro')

    if tipo == 'pila':
        # El vaso: dos paredes y un fondo. Las cajas se apilan desde el fondo; la de arriba es la que sale.
        x0, fondo, ancho, alto = zona.x + 250, zona.bottom - 14, 64, 20
        visibles = contenido[:5]
        pygame.draw.lines(pantalla, BLANCO, False, [(x0 - 6, fondo - 118), (x0 - 6, fondo), (x0 + ancho + 6, fondo), (x0 + ancho + 6, fondo - 118)], 3)
        for i, (valor, casilla) in enumerate(reversed(visibles)):                # de abajo hacia arriba
            caja(x0, fondo - 4 - (i + 1) * (alto + 2), ancho, alto, valor, casilla, i == len(visibles) - 1)
        arriba = fondo - 4 - len(visibles) * (alto + 2)
        escribir(pantalla, fuentes['chica'], 'TOPE (inicio): por aquí entra y por aquí sale', (x0 + ancho + 22, max(zona.y + 34, arriba - 2)), DORADO)
        escribir(pantalla, fuentes['chica'], 'FONDO (fin): lo más viejo', (x0 + ancho + 22, fondo - 22), GRIS_CLARO)
        if len(contenido) > 5:
            escribir(pantalla, fuentes['chica'], f'y {len(contenido) - 5} más abajo', (x0 - 20, fondo - 22), GRIS_CLARO, 'derecha')
        escribir(pantalla, fuentes['chica'], 'En rojo: la próxima en salir', (zona.x + 12, zona.y + 34), (255, 150, 150))
    else:
        # El tubo: dos líneas, abierto por los dos lados. La primera caja de la izquierda es la que sale.
        ancho, alto = (58, 46) if tipo == 'prioridad' else (58, 30)
        x0, y0 = zona.x + 96, zona.y + 50
        caben = 8
        pygame.draw.line(pantalla, BLANCO, (x0 - 10, y0 - 6), (x0 + caben * (ancho + 4) + 6, y0 - 6), 3)
        pygame.draw.line(pantalla, BLANCO, (x0 - 10, y0 + alto + 6), (x0 + caben * (ancho + 4) + 6, y0 + alto + 6), 3)
        for i, (valor, casilla) in enumerate(contenido[:caben]):
            caja(x0 + i * (ancho + 4), y0, ancho, alto, valor, casilla, i == 0)
        escribir(pantalla, fuentes['chica'], 'INICIO', (x0 - 18, y0 + alto / 2 - 20), DORADO, 'derecha')
        escribir(pantalla, fuentes['chica'], 'sale', (x0 - 18, y0 + alto / 2), DORADO, 'derecha')
        derecha = x0 + caben * (ancho + 4) + 14
        escribir(pantalla, fuentes['chica'], 'FIN', (derecha, y0 + alto / 2 - 20), GRIS_CLARO)
        escribir(pantalla, fuentes['chica'], 'entra', (derecha, y0 + alto / 2), GRIS_CLARO)
        pie = 'En rojo: la próxima en salir.'
        if len(contenido) > caben:
            pie += f'  Hay {len(contenido) - caben} más que no caben en el dibujo.'
        escribir(pantalla, fuentes['chica'], pie, (zona.x + 12, zona.bottom - 48), (255, 170, 170))
        if tipo == 'prioridad':
            que = {'Dijkstra': 'el costo acumulado', 'Voraz': 'la estimación hasta la meta', 'A*': 'el costo acumulado más la estimación'}[aprender['algoritmo']]
            escribir(pantalla, fuentes['chica'], f'El número de cada caja es {que}. Al entrar, se acomoda según ese valor.',
                     (zona.x + 12, zona.bottom - 26), GRIS_CLARO)


def dibujar_aprender(pantalla, fuentes, aprender, t):
    """Dibuja toda la pantalla del modo Aprender.

    Entradas: la pantalla, las fuentes, el estado del modo y el tiempo en segundos.
    A la izquierda van el mapa, la leyenda, la explicación y los controles; a la
    derecha, el código, la estructura de datos y la tabla comparativa.
    """
    pantalla.fill((22, 24, 30))
    paso = aprender['pasos'][aprender['paso']]
    mapa = aprender['mapa']
    zonas = zonas_de_aprender()
    nombre_del_mapa = MAPAS_DE_APRENDER[aprender['numero_de_mapa']][0]

    # ---- Barra superior: el título y los botones para elegir algoritmo y mapa.
    pygame.draw.rect(pantalla, NEGRO, (0, 0, ANCHO, 72))
    pygame.draw.rect(pantalla, ROJO, (0, 72, ANCHO, 5))
    escribir(pantalla, fuentes['grande'], 'Aprender', (24, 14))
    for i, nombre in enumerate(ALGORITMOS):
        dibujar_boton(pantalla, fuentes, zonas[('algoritmo', nombre)], f'{i + 1} {nombre}', nombre == aprender['algoritmo'], COLOR_DE[nombre])
    for i, (nombre, texto) in enumerate(MAPAS_DE_APRENDER):
        dibujar_boton(pantalla, fuentes, zonas[('mapa', i)], nombre, i == aprender['numero_de_mapa'])
    escribir(pantalla, fuentes['chica'], 'Algoritmo: 1 a 5.   Mapa: M.   Esc: menú.', (ANCHO - 24, 12), GRIS, 'derecha')
    escribir(pantalla, fuentes['chica'], 'Flechas: pasos.   Espacio: automático.', (ANCHO - 24, 44), GRIS, 'derecha')

    # ---- El mapa, visto de frente. Cada casilla se pinta según su papel en este paso.
    x0, y0 = ORIGEN_APRENDER
    lado = LADO_APRENDER
    exploradas = set(paso['exploradas'])
    esperan = {casilla for valor, casilla in paso['estructura']}
    velo = pygame.Surface((lado, lado), pygame.SRCALPHA)
    for (f, c), terreno in mapa['terreno'].items():
        zona = pygame.Rect(x0 + c * lado, y0 + f * lado, lado, lado)
        pygame.draw.rect(pantalla, PIEDRA_OSCURA if terreno == '#' else color_de_piso(terreno, f, c), zona)
        papel = None
        if (f, c) in paso['nuevas']:
            papel = 'nueva'
        elif (f, c) in esperan and (f, c) not in exploradas:
            papel = 'espera'
        elif (f, c) in exploradas:
            papel = 'explorada'
        if papel:
            velo.fill(COLOR_DE_PAPEL[papel] + (170,))            # el color del papel, semitransparente
            pantalla.blit(velo, zona)
        pygame.draw.rect(pantalla, NEGRO, zona, 1)
    if paso['ruta']:
        puntos = [(x0 + c * lado + lado / 2, y0 + f * lado + lado / 2) for f, c in paso['ruta']]
        pygame.draw.lines(pantalla, BLANCO, False, puntos, 9)
        pygame.draw.lines(pantalla, COLOR_DE_PAPEL['ruta'], False, puntos, 5)
    if paso['actual']:
        f, c = paso['actual']
        pygame.draw.rect(pantalla, COLOR_DE_PAPEL['actual'], (x0 + c * lado + 2, y0 + f * lado + 2, lado - 4, lado - 4), 5)
    # El inicio es un punto verde y la meta una estrella, cada uno con su letrero.
    for casilla, letrero in ((aprender['inicio'], 'Inicio'), (aprender['meta'], 'Meta')):
        centro = (x0 + casilla[1] * lado + lado / 2, y0 + casilla[0] * lado + lado / 2)
        if letrero == 'Inicio':
            pygame.draw.circle(pantalla, VERDE_INICIO, centro, 12)
            pygame.draw.circle(pantalla, NEGRO, centro, 12, 2)
        else:
            pygame.draw.polygon(pantalla, DORADO, puntos_de_estrella(centro, 17))
            pygame.draw.polygon(pantalla, NEGRO, puntos_de_estrella(centro, 17), 2)
        etiqueta = fuentes['chica'].render(letrero, True, BLANCO)
        fondo = etiqueta.get_rect(midbottom=(centro[0], centro[1] - 16)).inflate(8, 2)
        pygame.draw.rect(pantalla, NEGRO, fondo, border_radius=4)
        pantalla.blit(etiqueta, etiqueta.get_rect(center=fondo.center))

    # ---- La leyenda de colores.
    x = x0
    for papel, texto in TEXTO_DE_PAPEL:
        if papel == 'actual':
            pygame.draw.rect(pantalla, COLOR_DE_PAPEL[papel], (x, 452, 16, 16), 4)
        else:
            pygame.draw.rect(pantalla, COLOR_DE_PAPEL[papel], (x, 452, 16, 16))
        ancho = escribir(pantalla, fuentes['chica'], texto, (x + 22, 448), GRIS_CLARO).width
        x += ancho + 40

    # ---- La explicación en palabras de este paso.
    pygame.draw.rect(pantalla, (30, 32, 38), ZONA_EXPLICACION, border_radius=8)
    escribir(pantalla, fuentes['normal'], f"Paso {aprender['paso'] + 1} de {len(aprender['pasos'])}", (ZONA_EXPLICACION.x + 12, ZONA_EXPLICACION.y + 8), DORADO)
    for i, renglon in enumerate(partir_texto(fuentes['chica'], paso['texto'], ZONA_EXPLICACION.width - 24)[:4]):
        escribir(pantalla, fuentes['chica'], renglon, (ZONA_EXPLICACION.x + 12, ZONA_EXPLICACION.y + 38 + i * 21))
    # Debajo, qué enseña este mapa.
    for i, renglon in enumerate(partir_texto(fuentes['chica'], QUE_ENSEÑA[nombre_del_mapa], 528)[:2]):
        escribir(pantalla, fuentes['chica'], renglon, (24, 616 + i * 20), GRIS_CLARO)

    # ---- Los controles: avanzar, regresar, automático y velocidad.
    for accion, texto in BOTONES_DE_APRENDER:
        if accion == 'velocidad':
            texto = f"{VELOCIDADES_DE_APRENDER[aprender['velocidad']][0].capitalize()} (V)"
        elif accion == 'auto' and aprender['auto']:
            texto = 'Pausa'
        dibujar_boton(pantalla, fuentes, zonas[('boton', accion)], texto, accion == 'auto' and aprender['auto'])

    # ---- El código, con el renglón que se está ejecutando resaltado.
    pygame.draw.rect(pantalla, (30, 32, 38), ZONA_CODIGO, border_radius=8)
    for i, renglon in enumerate(CODIGO[aprender['algoritmo']]):
        y = ZONA_CODIGO.y + 8 + i * 17
        if i == paso['renglon']:
            pygame.draw.rect(pantalla, (255, 235, 59), (ZONA_CODIGO.x + 6, y - 1, ZONA_CODIGO.width - 12, 17), border_radius=3)
        escribir(pantalla, fuentes['codigo'], f'{i + 1:>2}  {renglon}', (ZONA_CODIGO.x + 12, y), NEGRO if i == paso['renglon'] else GRIS_CLARO)

    dibujar_estructura(pantalla, fuentes, aprender, paso)

    # ---- La tabla comparativa de los cinco algoritmos en este mapa, siempre visible.
    pygame.draw.rect(pantalla, (30, 32, 38), ZONA_TABLA, border_radius=8)
    columnas = [ZONA_TABLA.x + 300, ZONA_TABLA.x + 400, ZONA_TABLA.x + 500, ZONA_TABLA.right - 16]
    escribir(pantalla, fuentes['chica'], f'En el mapa "{nombre_del_mapa}"', (ZONA_TABLA.x + 12, ZONA_TABLA.y + 6), GRIS_CLARO)
    for x, titulo in zip(columnas, ['Exploradas', 'Pasos', 'Costo', 'Puntaje']):
        escribir(pantalla, fuentes['chica'], titulo, (x, ZONA_TABLA.y + 6), GRIS_CLARO, 'derecha')
    puntajes = [datos[3] for datos in aprender['tabla'].values() if datos[3] is not None]
    mejor = min(puntajes) if puntajes else None
    for i, (nombre, datos) in enumerate(aprender['tabla'].items()):
        y = ZONA_TABLA.y + 30 + i * 24
        gana = datos[3] is not None and datos[3] == mejor
        if nombre == aprender['algoritmo']:
            pygame.draw.rect(pantalla, (64, 66, 74), (ZONA_TABLA.x + 6, y - 1, ZONA_TABLA.width - 12, 23), border_radius=4)
        dibujar_ficha(pantalla, COLOR_DE[nombre], pygame.Rect(ZONA_TABLA.x + 14, y + 2, 12, 16))
        escribir(pantalla, fuentes['chica'], nombre, (ZONA_TABLA.x + 36, y), (120, 230, 140) if gana else BLANCO)
        escribir(pantalla, fuentes['chica'], datos[0], (columnas[0], y), BLANCO, 'derecha')
        if datos[3] is None:
            escribir(pantalla, fuentes['chica'], 'sin ruta', (columnas[3], y), GRIS, 'derecha')
        else:
            escribir(pantalla, fuentes['chica'], datos[1], (columnas[1], y), BLANCO, 'derecha')
            escribir(pantalla, fuentes['chica'], datos[2], (columnas[2], y), BLANCO, 'derecha')
            escribir(pantalla, fuentes['chica'], datos[3], (columnas[3], y), (120, 230, 140) if gana else BLANCO, 'derecha')
    pie = 'En verde, el mejor: puntaje = costo x 10 000 + exploradas; gana el más bajo.' if mejor is not None else 'Ningún algoritmo puede llegar: no hay mejor.'
    escribir(pantalla, fuentes['chica'], pie, (ZONA_TABLA.x + 12, ZONA_TABLA.bottom - 26), (120, 230, 140) if mejor is not None else GRIS_CLARO)

# ============================================================================
# 12. PORTADA Y MENÚ
# ============================================================================

# Los modos del programa: clave, nombre y una línea que lo describe.
MODOS = [('gemas', 'Atrapa gemas', 'Carrera contra los cinco algoritmos.'),
         ('bandera', 'Captura la bandera', 'Uno contra uno, a tres puntos.'),
         ('laberinto', 'Maze Runner', 'Un laberinto que cambia cada 3 segundos.'),
         ('aprender', 'Aprender', 'Cada algoritmo, paso a paso.'),
         ('mirar_gemas', 'Mirar: atrapa gemas', 'Compiten solo los algoritmos.'),
         ('mirar_bandera', 'Mirar: captura la bandera', 'Elige el algoritmo de cada lado.'),
         ('mirar_laberinto', 'Mirar: Maze Runner', 'Sigue de cerca a quien quieras.'),
         ('salir', 'Salir', 'Cierra el programa.')]
DURACION_DE_TRANSICION = 0.55            # segundos que tarda la caja elegida en llenar la pantalla


def zonas_del_menu():
    """Calcula el rectángulo de cada caja del menú.

    Salida: lista de rectángulos, uno por modo, en dos filas de cuatro cajas centradas.
    """
    ancho, alto, espacio = 280, 150, 16
    izquierda = (ANCHO - 4 * ancho - 3 * espacio) // 2
    return [pygame.Rect(izquierda + (i % 4) * (ancho + espacio), 270 + (i // 4) * (alto + espacio), ancho, alto)
            for i in range(len(MODOS))]


def dibujar_fondo_con_partida(pantalla, fuentes, estado, t, oscurecer):
    """Dibuja de fondo la partida que se juega sola, oscurecida para que el texto se lea.

    Entradas: la pantalla, las fuentes, el estado, el tiempo y cuánto oscurecer (0 a 255).
    """
    dibujar_gemas(pantalla, fuentes, estado['demo'], t, estado['entorno'], estado['efectos'], con_interfaz=False)
    velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    velo.fill((0, 0, 0, oscurecer))
    pantalla.blit(velo, (0, 0))


def dibujar_titulo(pantalla, fuentes, y):
    """Escribe el título y el subtítulo del proyecto, centrados.

    Entradas: la pantalla, las fuentes y la altura del título.
    """
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):                # borde negro para que resalte sobre la partida
        escribir(pantalla, fuentes['enorme'], 'Maze Runner', (ANCHO // 2 + dx, y + dy), NEGRO, 'centro')
    escribir(pantalla, fuentes['enorme'], 'Maze Runner', (ANCHO // 2, y), BLANCO, 'centro')
    pygame.draw.rect(pantalla, ROJO, (ANCHO // 2 - 300, y + 78, 600, 8))
    escribir(pantalla, fuentes['grande'], 'Proyecto de matemáticas discretas', (ANCHO // 2, y + 116), BLANCO, 'centro')


def dibujar_portada(pantalla, fuentes, estado, t):
    """Dibuja la portada: el título arriba y, de fondo, una partida que se juega sola.

    Entradas: la pantalla, las fuentes, el estado y el tiempo en segundos.
    """
    dibujar_fondo_con_partida(pantalla, fuentes, estado, t, 120)
    dibujar_titulo(pantalla, fuentes, 150)
    if int(t * 2) % 2 == 0:                          # el letrero parpadea dos veces por segundo
        escribir(pantalla, fuentes['grande'], 'Presiona cualquier tecla', (ANCHO // 2, 600), DORADO, 'centro')


def dibujar_menu(pantalla, fuentes, estado, t):
    """Dibuja el menú: los modos en cajas centradas, con la elegida resaltada.

    Entradas: la pantalla, las fuentes, el estado y el tiempo en segundos.
    Al entrar al menú las cajas suben a su lugar una tras otra.
    """
    dibujar_fondo_con_partida(pantalla, fuentes, estado, t, 175)
    escribir(pantalla, fuentes['titulo'], 'Maze Runner', (ANCHO // 2, 96), BLANCO, 'centro')
    escribir(pantalla, fuentes['normal'], 'Proyecto de matemáticas discretas', (ANCHO // 2, 150), GRIS_CLARO, 'centro')
    escribir(pantalla, fuentes['chica'], 'Elige un modo con las flechas y Enter, o con el ratón.   Esc: portada.', (ANCHO // 2, 216), GRIS_CLARO, 'centro')
    for i, ((clave, nombre, descripcion), zona) in enumerate(zip(MODOS, zonas_del_menu())):
        # Cada caja llega un poco después que la anterior.
        llegada = min(1.0, max(0.0, (estado['tiempo_en_menu'] - i * 0.04) / 0.3))
        zona = zona.move(0, int((1 - llegada) * 60))
        elegida = i == estado['elegida']
        if elegida:
            # La caja recién elegida (con el cursor o con las flechas) se apachurra y rebota:
            # primero se ensancha y se aplasta, luego se estira, y se asienta un poco más grande.
            k = min(1.0, (estado['tiempo_en_menu'] - estado['elegida_desde']) / 0.45)
            vaiven = sin(k * pi * 3) * (1 - k)
            zona = zona.inflate(int(zona.width * (0.04 + 0.10 * vaiven)), int(zona.height * (0.04 - 0.18 * vaiven)))
        pygame.draw.rect(pantalla, ROJO if elegida else (34, 36, 42), zona, border_radius=14)
        pygame.draw.rect(pantalla, BLANCO if elegida else (96, 98, 104), zona, 3 if elegida else 1, border_radius=14)
        # El nombre y la descripción se parten en los renglones que hagan falta para caber en la
        # caja, y el bloque completo se centra a lo alto.
        titulo = partir_texto(fuentes['normal'], nombre, zona.width - 28)
        texto = partir_texto(fuentes['chica'], descripcion, zona.width - 28)
        y = zona.centery - (len(titulo) * 26 + 10 + len(texto) * 20) // 2 + 13
        for renglon in titulo:
            escribir(pantalla, fuentes['normal'], renglon, (zona.centerx, y), BLANCO, 'centro')
            y += 26
        y += 6
        for renglon in texto:
            escribir(pantalla, fuentes['chica'], renglon, (zona.centerx, y), BLANCO if elegida else GRIS_CLARO, 'centro')
            y += 20


def dibujar_transicion(pantalla, fuentes, estado, t):
    """Dibuja la transición al elegir un modo: su caja crece hasta llenar la pantalla.

    Entradas: la pantalla, las fuentes, el estado y el tiempo en segundos.
    """
    dibujar_menu(pantalla, fuentes, estado, t)
    transicion = estado['transicion']
    avance = min(1.0, transicion['t'] / DURACION_DE_TRANSICION)
    avance = avance * avance * (3 - 2 * avance)      # arranca y termina suave
    caja = zonas_del_menu()[transicion['indice']]
    # Cada lado de la caja viaja desde su lugar hasta el borde de la pantalla.
    zona = pygame.Rect(caja.x * (1 - avance), caja.y * (1 - avance),
                       caja.width + (ANCHO - caja.width) * avance, caja.height + (ALTO - caja.height) * avance)
    pygame.draw.rect(pantalla, mezclar(ROJO, NEGRO, avance), zona, border_radius=int(14 * (1 - avance)))
    escribir(pantalla, fuentes['titulo'], MODOS[transicion['indice']][1], zona.center, mezclar(BLANCO, NEGRO, avance * 0.6), 'centro')


# ============================================================================
# 13. EL PROGRAMA
# ============================================================================

# Las teclas de movimiento y el movimiento (cambio de fila, cambio de columna) de cada una.
TECLAS_DE_MOVIMIENTO = {pygame.K_UP: (-1, 0), pygame.K_w: (-1, 0), pygame.K_RIGHT: (0, 1), pygame.K_d: (0, 1),
                        pygame.K_DOWN: (1, 0), pygame.K_s: (1, 0), pygame.K_LEFT: (0, -1), pygame.K_a: (0, -1)}
# Las teclas 1 a 6 eligen al rival en captura la bandera, y el algoritmo en el modo Aprender.
TECLAS_DE_NUMERO = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]


def crear_estado():
    """Prepara todo lo que cambia mientras corre el programa.

    Salida: un diccionario con
        'pantalla':    'portada', 'menu', 'transicion', 'juego' o 'aprender'
        'elegida':     el número de la caja resaltada en el menú
        'juego':       la partida en curso, o None
        'modo':        la clave del modo que se está jugando
        'aprender':    el estado del modo Aprender, o None
        'demo':        la partida que se juega sola detrás de la portada y del menú
        'rival':       el rival elegido para captura la bandera. Se conserva de una
                       partida a otra y empieza en A*.
        'izquierda':   el algoritmo del lado izquierdo al solo mirar; empieza en BFS
        'direcciones': los movimientos oprimidos, del más viejo al más reciente
        'arrastrando': True mientras se arrastra la vista con el ratón
        'transicion':  la transición en curso: {'indice', 't'}
        'tiempo_en_menu': segundos desde que se abrió el menú
        'elegida_desde': valor de 'tiempo_en_menu' cuando se resaltó la caja actual (para su rebote)
        'entorno':     el ambiente: hora del día, nubes y pájaros
        'efectos':     las partículas y los fuegos artificiales
        'abierto':     False cuando hay que cerrar el programa
    """
    return {'pantalla': 'portada', 'elegida': 0, 'juego': None, 'modo': None, 'aprender': None,
            'demo': crear_gemas(con_jugador=False), 'rival': 'A*', 'izquierda': 'BFS', 'direcciones': [],
            'arrastrando': False, 'transicion': None, 'tiempo_en_menu': 0.0, 'elegida_desde': 0.0,
            'entorno': crear_entorno(), 'efectos': crear_efectos(), 'abierto': True}


def empezar(estado, modo):
    """Empieza una partida nueva del modo indicado.

    Entradas: el estado y la clave del modo.
    """
    estado['modo'] = modo
    estado['direcciones'] = []
    estado['efectos'] = crear_efectos()
    if modo == 'aprender':
        estado['aprender'] = crear_aprender()
        estado['pantalla'] = 'aprender'
        return
    if modo == 'gemas':
        estado['juego'] = crear_gemas()
    elif modo == 'mirar_gemas':
        estado['juego'] = crear_gemas(con_jugador=False)
    elif modo == 'bandera':
        estado['juego'] = crear_bandera(estado['rival'])
    elif modo == 'mirar_bandera':
        estado['juego'] = crear_bandera(estado['rival'], izquierda=estado['izquierda'])
    elif modo == 'laberinto':
        estado['juego'] = crear_laberinto()
    else:
        estado['juego'] = crear_laberinto(con_jugador=False)
    estado['pantalla'] = 'juego'


def elegir(estado, indice):
    """Elige una caja del menú: empieza la transición hacia ese modo, o cierra el programa.

    Entradas: el estado y el número de la caja.
    """
    if MODOS[indice][0] == 'salir':
        estado['abierto'] = False
    else:
        estado['elegida'] = indice
        estado['transicion'] = {'indice': indice, 't': 0.0}
        estado['pantalla'] = 'transicion'


def resaltar(estado, numero):
    """Resalta una caja del menú. Si es otra que la que estaba, empieza su rebote.

    Entradas: el estado y el número de la caja.
    """
    if numero != estado['elegida']:
        estado['elegida'] = numero
        estado['elegida_desde'] = estado['tiempo_en_menu']


def al_menu(estado):
    """Regresa al menú desde cualquier modo."""
    estado['pantalla'] = 'menu'
    estado['juego'] = None
    estado['aprender'] = None
    estado['transicion'] = None                      # sin restos de la caja que creció al elegir el modo
    estado['tiempo_en_menu'] = 0.0
    estado['elegida_desde'] = 0.0
    estado['direcciones'] = []


def terminada(juego):
    """Dice si una partida ya terminó: se anunció el resultado o alguien llegó a 3 puntos."""
    return juego['fase'] == 'final' if juego['tipo'] == 'bandera' else juego['anuncio']


def mapa_visible(juego):
    """Da el mapa que se está viendo, para saber su tamaño al mover la cámara."""
    return juego['mapas'][0] if juego['tipo'] == 'gemas' else juego['mapa']


def seguir_a(juego, indice, zoom_minimo):
    """Hace que la cámara siga a un corredor.

    Entradas: la partida, el número del corredor (o None para la vista general)
              y el acercamiento mínimo que debe quedar.
    """
    camara = juego['camara']
    if indice is None:
        juego['camara'] = crear_camara()             # vista general: todo el tablero
        return
    camara.update({'seguir': indice, 'libre': False, 'zoom': max(camara['zoom'], zoom_minimo)})


def mover_camara(juego, df, dc):
    """Desplaza la vista. Al hacerlo deja de seguir al personaje.

    Entradas: la partida y cuántas casillas se mueve la vista hacia abajo y hacia la derecha.
    """
    camara = juego['camara']
    mapa = mapa_visible(juego)
    if camara['centro'] is None or not camara['libre']:
        # Se parte de lo que se estaba viendo: el personaje seguido o el centro del tablero.
        if camara['seguir'] is not None:
            camara['centro'] = posicion(juego['corredores'][camara['seguir']])
        else:
            camara['centro'] = ((mapa['filas'] - 1) / 2, (mapa['columnas'] - 1) / 2)
    f, c = camara['centro']
    camara['centro'] = (min(mapa['filas'] - 1, max(0, f + df)), min(mapa['columnas'] - 1, max(0, c + dc)))
    camara['libre'] = True


def atender_juego(estado, evento):
    """Atiende un evento durante una partida.

    Entradas: el estado y el evento.
    """
    juego = estado['juego']
    modo = estado['modo']
    camara = juego['camara']
    mirando = modo.startswith('mirar')
    # El acercamiento al seguir a alguien: en atrapa gemas el tablero ya se ve grande.
    zoom_al_seguir = 1.0 if juego['tipo'] == 'gemas' and mirando else (2.4 if juego['tipo'] == 'laberinto' else ACERCAMIENTO)
    cuantos = len(juego['corredores'])

    if evento.type == pygame.KEYDOWN:
        mayusculas = evento.mod & pygame.KMOD_SHIFT if hasattr(evento, 'mod') else 0
        if evento.key == pygame.K_ESCAPE:            # Esc: al menú
            al_menu(estado)
        elif evento.key == pygame.K_r:               # R: reinicia en cualquier momento
            empezar(estado, modo)
        elif evento.key in (pygame.K_SPACE, pygame.K_RETURN) and terminada(juego):
            empezar(estado, modo)                    # otra partida, cuando ya terminó
        elif evento.key == pygame.K_c and not mirando:
            # C: acerca la vista al jugador, o la regresa.
            seguir_a(juego, None if camara['seguir'] is not None else juego['corredores'].index(juego['jugador']), zoom_al_seguir)
        elif evento.key == pygame.K_TAB and mirando:
            # Tab: pasa a seguir al siguiente personaje.
            seguir_a(juego, 0 if camara['seguir'] is None else (camara['seguir'] + 1) % cuantos, zoom_al_seguir)
            juego['cartel_cerrado'] = True
        elif evento.key == pygame.K_0 and mirando:   # 0: vista general
            seguir_a(juego, None, 1.0)
        elif juego['tipo'] == 'bandera' and evento.key in TECLAS_DE_NUMERO:
            numero = TECLAS_DE_NUMERO.index(evento.key)
            if mirando and mayusculas and numero < len(ALGORITMOS):
                estado['izquierda'] = list(ALGORITMOS)[numero]       # Mayús + número: el lado izquierdo
            else:
                estado['rival'] = OPCIONES_DE_RIVAL[numero]          # se conserva para las partidas siguientes
            empezar(estado, modo)
        elif (juego['tipo'] == 'laberinto' and not mirando and juego['jugador']['final'] is not None
              and evento.key in (pygame.K_LEFT, pygame.K_RIGHT)):
            # Cuando el jugador ya terminó, las flechas pasan la vista de un competidor a otro.
            paso = 1 if evento.key == pygame.K_RIGHT else -1
            seguir_a(juego, ((camara['seguir'] or 0) + paso) % cuantos, zoom_al_seguir)
            juego['cartel_cerrado'] = True

    elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
        if juego['tipo'] == 'bandera':
            for opcion, zona in zip(OPCIONES_DE_RIVAL, zonas_de_rival(mirando)):
                if zona.collidepoint(evento.pos):
                    estado['rival'] = opcion
                    empezar(estado, modo)
                    return
            if mirando:
                for nombre, zona in zip(ALGORITMOS, zonas_de_izquierda()):
                    if zona.collidepoint(evento.pos):
                        estado['izquierda'] = nombre
                        empezar(estado, modo)
                        return
        if juego['tipo'] == 'laberinto' and not mirando:
            if BOTON_ACERCAR.collidepoint(evento.pos):
                seguir_a(juego, None if camara['seguir'] is not None else 0, zoom_al_seguir)
                return
            if juego['jugador']['final'] is not None:
                for zona, paso in ((BOTON_ANTERIOR, -1), (BOTON_SIGUIENTE, 1)):
                    if zona.collidepoint(evento.pos):
                        seguir_a(juego, ((camara['seguir'] or 0) + paso) % cuantos, zoom_al_seguir)
                        juego['cartel_cerrado'] = True
                        return
        if mirando:
            estado['arrastrando'] = True             # empieza a arrastrar la vista
            if juego['tipo'] == 'gemas' and camara['seguir'] is None:
                # En la vista general, un clic sobre un tablero lo abre en grande.
                for numero in range(cuantos):
                    if zona_de_tablero_de_gemas(numero).collidepoint(evento.pos):
                        seguir_a(juego, numero, 1.0)
    elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
        estado['arrastrando'] = False
    elif evento.type == pygame.MOUSEMOTION and estado['arrastrando'] and mirando:
        # Arrastrar desplaza la vista: los pixeles se convierten en casillas.
        ancho, alto = camara['casilla_px']
        mover_camara(juego, -evento.rel[1] / alto, -evento.rel[0] / ancho)
    elif evento.type == pygame.MOUSEWHEEL and mirando:
        # La rueda acerca y aleja.
        if juego['tipo'] == 'gemas' and camara['seguir'] is None:
            seguir_a(juego, 0, 1.0)
        camara = juego['camara']
        camara['zoom'] = min(4.0, max(1.0, camara['zoom'] * (1.15 ** evento.y)))


def atender_aprender(estado, evento):
    """Atiende un evento en el modo Aprender.

    Entradas: el estado y el evento.
    """
    aprender = estado['aprender']

    def hacer(tipo, valor):
        """Ejecuta lo que corresponde a un botón o a su tecla."""
        if tipo == 'algoritmo':
            estado['aprender'] = crear_aprender(valor, aprender['numero_de_mapa'])
            estado['aprender']['velocidad'] = aprender['velocidad']
        elif tipo == 'mapa':
            estado['aprender'] = crear_aprender(aprender['algoritmo'], valor)
            estado['aprender']['velocidad'] = aprender['velocidad']
        elif valor == 'reiniciar':
            aprender.update({'paso': 0, 'auto': False})
        elif valor == 'anterior':
            aprender.update({'paso': max(0, aprender['paso'] - 1), 'auto': False})
        elif valor == 'siguiente':
            aprender.update({'paso': min(len(aprender['pasos']) - 1, aprender['paso'] + 1), 'auto': False})
        elif valor == 'auto':
            if aprender['paso'] == len(aprender['pasos']) - 1:
                aprender['paso'] = 0                 # si ya estaba al final, el automático empieza de nuevo
            aprender['auto'] = not aprender['auto']
        elif valor == 'velocidad':
            # Cambia a la siguiente velocidad; se puede hacer mientras se reproduce.
            aprender['velocidad'] = (aprender['velocidad'] + 1) % len(VELOCIDADES_DE_APRENDER)

    if evento.type == pygame.KEYDOWN:
        if evento.key == pygame.K_ESCAPE:
            al_menu(estado)
        elif evento.key in TECLAS_DE_NUMERO[:5]:
            hacer('algoritmo', list(ALGORITMOS)[TECLAS_DE_NUMERO.index(evento.key)])
        elif evento.key == pygame.K_m:
            hacer('mapa', (aprender['numero_de_mapa'] + 1) % len(MAPAS_DE_APRENDER))
        else:
            tecla = {pygame.K_r: 'reiniciar', pygame.K_LEFT: 'anterior', pygame.K_RIGHT: 'siguiente',
                     pygame.K_SPACE: 'auto', pygame.K_v: 'velocidad'}.get(evento.key)
            if tecla:
                hacer('boton', tecla)
    elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
        for (tipo, valor), zona in zonas_de_aprender().items():
            if zona.collidepoint(evento.pos):
                hacer(tipo, valor)
                break


def atender(estado, evento):
    """Atiende un evento del teclado o del ratón, según la pantalla en la que se esté.

    Entradas: el estado y el evento que entregó pygame.
    """
    if evento.type == pygame.QUIT:
        estado['abierto'] = False
        return

    # Las teclas de movimiento se anotan al oprimirse y se borran al soltarse.
    if evento.type == pygame.KEYDOWN and evento.key in TECLAS_DE_MOVIMIENTO:
        direccion = TECLAS_DE_MOVIMIENTO[evento.key]
        if direccion in estado['direcciones']:
            estado['direcciones'].remove(direccion)
        estado['direcciones'].append(direccion)      # la más reciente queda al final
    elif evento.type == pygame.KEYUP and evento.key in TECLAS_DE_MOVIMIENTO:
        direccion = TECLAS_DE_MOVIMIENTO[evento.key]
        if direccion in estado['direcciones']:
            estado['direcciones'].remove(direccion)

    if estado['pantalla'] == 'juego':
        atender_juego(estado, evento)
    elif estado['pantalla'] == 'aprender':
        atender_aprender(estado, evento)
    elif estado['pantalla'] == 'portada':
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                estado['abierto'] = False
            else:
                al_menu(estado)                      # cualquier otra tecla abre el menú
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            al_menu(estado)
    elif estado['pantalla'] == 'menu':
        if evento.type == pygame.KEYDOWN:
            # Las flechas mueven la selección por las dos filas de cajas.
            columna, fila = estado['elegida'] % 4, estado['elegida'] // 4
            if evento.key in (pygame.K_LEFT, pygame.K_a):
                columna = (columna - 1) % 4
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                columna = (columna + 1) % 4
            elif evento.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                fila = 1 - fila
            elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                elegir(estado, estado['elegida'])
                return
            elif evento.key == pygame.K_ESCAPE:
                estado['pantalla'] = 'portada'
                return
            resaltar(estado, fila * 4 + columna)
        elif evento.type == pygame.MOUSEMOTION:
            for i, zona in enumerate(zonas_del_menu()):
                if zona.collidepoint(evento.pos):
                    resaltar(estado, i)
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, zona in enumerate(zonas_del_menu()):
                if zona.collidepoint(evento.pos):
                    elegir(estado, i)
                    break


def actualizar(estado, segundos):
    """Avanza un cuadro de lo que esté en pantalla.

    Entradas: el estado y los segundos que pasaron desde el cuadro anterior.
    """
    actualizar_entorno(estado['entorno'], segundos)
    actualizar_efectos(estado['efectos'], segundos)
    pantalla = estado['pantalla']

    if pantalla in ('portada', 'menu', 'transicion'):
        # La partida de fondo se juega sola. Cuando todos terminan, empieza otra.
        demo = estado['demo']
        actualizar_gemas(demo, segundos, [])
        finales = [corredor['final'] for corredor in demo['corredores']]
        if None not in finales and demo['reloj'] > max(finales) + 4:
            estado['demo'] = crear_gemas(con_jugador=False)
        estado['tiempo_en_menu'] += segundos
        if pantalla == 'transicion':
            estado['transicion']['t'] += segundos
            if estado['transicion']['t'] >= DURACION_DE_TRANSICION:
                empezar(estado, MODOS[estado['transicion']['indice']][0])
        return

    if pantalla == 'aprender':
        actualizar_aprender(estado['aprender'], segundos)
        return

    juego = estado['juego']
    direcciones = estado['direcciones']
    if estado['modo'].startswith('mirar'):
        # Al solo mirar, W A S D y las flechas mueven la vista en lugar de un personaje.
        for df, dc in direcciones:
            mover_camara(juego, df * 7 * segundos / juego['camara']['zoom'], dc * 7 * segundos / juego['camara']['zoom'])
        direcciones = []
    if juego['tipo'] == 'gemas':
        actualizar_gemas(juego, segundos, direcciones)
    elif juego['tipo'] == 'bandera':
        actualizar_bandera(juego, segundos, direcciones)
    else:
        actualizar_laberinto(juego, segundos, direcciones)


def dibujar(pantalla, fuentes, estado, t):
    """Dibuja la pantalla que toque.

    Entradas: la pantalla, las fuentes, el estado y el tiempo en segundos desde que abrió el programa.
    """
    if estado['pantalla'] == 'portada':
        dibujar_portada(pantalla, fuentes, estado, t)
    elif estado['pantalla'] == 'menu':
        dibujar_menu(pantalla, fuentes, estado, t)
    elif estado['pantalla'] == 'transicion':
        dibujar_transicion(pantalla, fuentes, estado, t)
    elif estado['pantalla'] == 'aprender':
        dibujar_aprender(pantalla, fuentes, estado['aprender'], t)
    elif estado['juego']['tipo'] == 'gemas':
        dibujar_gemas(pantalla, fuentes, estado['juego'], t, estado['entorno'], estado['efectos'])
    elif estado['juego']['tipo'] == 'bandera':
        dibujar_bandera_juego(pantalla, fuentes, estado['juego'], t, estado['entorno'], estado['efectos'])
    else:
        dibujar_laberinto(pantalla, fuentes, estado['juego'], t, estado['entorno'], estado['efectos'])


def principal():
    """Abre la ventana y corre el programa hasta que se cierre.

    En cada vuelta del ciclo se hacen tres cosas: atender el teclado y el
    ratón, avanzar lo que esté en pantalla y volver a dibujar todo.
    """
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption('Maze Runner: proyecto de matemáticas discretas')
    fuentes = crear_fuentes()
    estado = crear_estado()
    reloj = pygame.time.Clock()
    t = 0.0

    while estado['abierto']:
        # Espera para ir a 60 cuadros por segundo y da el tiempo que pasó. Se limita a una
        # décima de segundo para que, si la ventana se traba, los personajes no den un salto.
        segundos = min(reloj.tick(60) / 1000, 0.1)
        t += segundos
        for evento in pygame.event.get():
            atender(estado, evento)
        actualizar(estado, segundos)
        dibujar(pantalla, fuentes, estado, t)
        pygame.display.flip()                        # pasa a la ventana lo que se acaba de dibujar

    pygame.quit()


if __name__ == '__main__':
    principal()
