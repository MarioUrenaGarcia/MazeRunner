"""MazeRunner, fase 3: dos juegos contra los algoritmos de búsqueda.

Un menú y dos juegos en los que se compite contra rivales que se mueven con
los cinco algoritmos de la fase 1. El tablero se ve desde arriba e inclinado.

    Atrapa gemas         Cada competidor corre en su propio tablero de 9 x 9,
                         todos idénticos, y recoge las mismas 8 gemas en el
                         mismo orden, una a la vez. Se compite contra los cinco
                         algoritmos. Gana quien termine primero.

    Captura la bandera   En un tablero de 17 x 11, hay que robar la bandera del
                         rival y llevarla a donde está la propia. Gana el
                         primero que junte tres puntos.

Reglas comunes:
    - Entrar a llano cuesta 1, a bosque 3 y a agua 5. En los juegos ese costo
      es tiempo: cruzar agua tarda cinco veces más que cruzar llano. Por eso
      la ruta más barata es también la más rápida.
    - El jugador avanza a 5.0 casillas por segundo y los rivales a 4.4
      (4.3 en captura la bandera).
    - Cada vez que un rival planea una ruta se queda quieto pensando 0.008
      segundos por cada casilla que exploró. El que explora de más pierde tiempo.
    - El terreno se sortea en manchas de dos casillas: 5 muros, 5 árboles y
      5 charcos. Nunca encierra a nadie.
    - Siempre se ve dibujada la ruta que planea cada rival.

Controles:
    Flechas o W A S D    mover al personaje, casilla por casilla
    C                    acercar la vista al personaje, o regresarla
    R                    reiniciar la partida
    Espacio o Enter      otra partida, cuando ya terminó
    Esc                  regresar al menú
    1 a 6                elegir rival en captura la bandera

Para ejecutarlo:  python fase3_juegos.py
"""

import heapq                              # cola de prioridad: siempre entrega el elemento más pequeño
import random                             # gemas, banderas y terrenos distintos en cada partida
from collections import deque             # cola: se saca por un extremo y se mete por el otro
from math import ceil, hypot, sin

import pygame                             # ventana, dibujo y teclado

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
            'ruta': [], 'objetivo': None, 'pensando': 0.0, 'replanear': False, 'pasos': 0, 'planes': 0}


def empezar_paso(corredor, mapa, vecina):
    """Hace que un corredor empiece a caminar hacia una casilla vecina.

    Entradas: el corredor, el mapa y la casilla vecina.
    Salida:   True si empezó a caminar; False si la casilla es muro o está fuera del mapa.
    """
    terreno = mapa['terreno'].get(vecina, '#')
    if terreno == '#':
        return False
    corredor['destino'] = vecina
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
        'corredores': los competidores. Cada uno lleva además 'siguiente'
                      (cuántas gemas ha recogido) y 'final' (en qué momento terminó)
        'jugador':    el corredor del jugador, o None al solo mirar
        'reloj':      segundos de carrera
        'cuenta':     segundos que faltan de la cuenta regresiva
        'fase':       'cuenta' o 'carrera'
        'anuncio':    True cuando ya se anunció el resultado
        'acercar':    True si la vista está acercada al jugador
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
        corredor.update({'siguiente': 0, 'final': None})
        corredores.append(corredor)

    return {'tipo': 'gemas', 'gemas': gemas, 'mapas': mapas, 'corredores': corredores,
            'jugador': corredores[0] if con_jugador else None,
            'reloj': 0.0, 'cuenta': CUENTA_REGRESIVA, 'fase': 'cuenta', 'anuncio': False, 'acercar': False}


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
    if juego['fase'] == 'cuenta':
        juego['cuenta'] -= segundos
        if juego['cuenta'] <= 0:
            juego['fase'] = 'carrera'
        return

    juego['reloj'] += segundos
    for corredor in juego['corredores']:
        if corredor['final'] is not None:
            continue                                 # ya terminó: se queda en su tablero
        avanzar(corredor, segundos)

        # La gema se recoge al estar a menos de media casilla de ella.
        if distancia(posicion(corredor), juego['gemas'][corredor['siguiente']]) < RADIO_DE_RECOGER:
            corredor['siguiente'] += 1               # con esto su tablero pasa al terreno de la gema que sigue
            corredor['objetivo'] = None              # el rival tendrá que planear hacia la gema nueva
            corredor['ruta'] = []
            if corredor['siguiente'] == CANTIDAD_DE_GEMAS:
                corredor['final'] = juego['reloj']
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
    """Ordena a los competidores de atrapa gemas del primero al último.

    Entrada: la partida.
    Salida:  la lista de corredores ordenada: primero quien ya terminó (por su
             tiempo), luego quien lleva más gemas y luego quien está más cerca
             de su siguiente gema.
    """
    def orden(corredor):
        """La clave para ordenar: mientras más chica, mejor lugar."""
        if corredor['final'] is not None:
            return (0, corredor['final'], 0)
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


def crear_bandera(eleccion='A*'):
    """Prepara una partida de captura la bandera.

    Entrada: la elección de rival: el nombre de un algoritmo o 'Azar'.

    Salida: un diccionario con
        'tipo':      'bandera'
        'eleccion':  lo que se eligió como rival; con 'Azar', el rival cambia tras cada punto
        'mapa':      el terreno actual, siempre en espejo
        'secuencia': 16 posiciones para la bandera del jugador, sorteadas al empezar.
                     La del rival está siempre en la casilla espejo.
        'turno':     qué posición de la secuencia toca; avanza con cada punto y cada choque
        'jugador':   el corredor del lado izquierdo
        'rival':     el corredor del lado derecho
                     Los dos llevan además 'salida', 'lleva' (True si carga la
                     bandera del otro) y 'puntos'.
        'reloj', 'cuenta', 'fase' ('cuenta', 'carrera' o 'final')
        'pausa':     segundos de pausa tras un choque
        'aviso':     texto que se muestra un momento, y 'aviso_resta' los segundos que le quedan
        'acercar':   True si la vista está acercada al jugador
    """
    # La bandera del jugador va en su mitad: lejos de su salida y fuera de las tres columnas centrales.
    centro = COLUMNAS_BANDERA // 2
    posibles = [(f, c) for f in range(FILAS_BANDERA) for c in range(centro - 1)
                if estimacion((f, c), SALIDA_IZQUIERDA) >= DISTANCIA_A_LA_SALIDA]
    secuencia = [random.choice(posibles) for posicion_numero in range(POSICIONES_DE_BANDERA)]

    nombre = random.choice(list(ALGORITMOS)) if eleccion == 'Azar' else eleccion
    jugador = crear_corredor('Tú', SALIDA_IZQUIERDA, velocidad=VELOCIDAD_JUGADOR)
    rival = crear_corredor(nombre, SALIDA_DERECHA, ALGORITMOS[nombre], VELOCIDAD_RIVAL_BANDERA)
    jugador.update({'salida': SALIDA_IZQUIERDA, 'lleva': False, 'puntos': 0})
    rival.update({'salida': SALIDA_DERECHA, 'lleva': False, 'puntos': 0})

    juego = {'tipo': 'bandera', 'eleccion': eleccion, 'mapa': None, 'secuencia': secuencia, 'turno': 0,
             'jugador': jugador, 'rival': rival, 'reloj': 0.0, 'cuenta': CUENTA_REGRESIVA, 'fase': 'cuenta',
             'pausa': 0.0, 'aviso': '', 'aviso_resta': 0.0, 'acercar': False}
    cambiar_terreno(juego)                           # el terreno cambia al empezar
    return juego


def bandera_de(juego, corredor):
    """Da la casilla donde está la bandera de un personaje cuando nadie la carga.

    Entradas: la partida y el corredor dueño de la bandera.
    Salida:   la casilla. La del jugador sale de la secuencia; la del rival es su espejo.
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
    juego['mapa'] = sortear_terreno(FILAS_BANDERA, COLUMNAS_BANDERA, prohibidas, fijas + personajes, espejo=True)
    rival['replanear'] = True                        # con terreno nuevo, el rival vuelve a planear


def avisar(juego, texto, segundos=1.6):
    """Muestra un aviso en pantalla durante un momento.

    Entradas: la partida, el texto y cuántos segundos se muestra.
    """
    juego['aviso'] = texto
    juego['aviso_resta'] = segundos


def objetivo_del_rival(juego):
    """Decide a dónde quiere ir el rival de captura la bandera.

    Entrada: la partida.
    Salida:  una casilla.
        Si lleva la bandera del jugador, va a donde está la suya para anotar.
        Si el jugador lleva la suya, lo persigue: su objetivo es la casilla del jugador.
        Si nadie lleva nada, va a robar la bandera del jugador.
    """
    jugador, rival = juego['jugador'], juego['rival']
    if rival['lleva']:
        return bandera_de(juego, rival)
    if jugador['lleva']:
        return jugador['destino'] or jugador['casilla']
    return bandera_de(juego, jugador)


def revisar_banderas(juego, quien, otro):
    """Revisa si un personaje roba una bandera o anota, según la casilla que pisa.

    Entradas:
        juego: la partida
        quien: el corredor que se revisa
        otro:  su contrincante
    """
    if quien['destino'] is not None:
        return                                       # va a medio paso: todavía no pisa la casilla
    if not quien['lleva'] and quien['casilla'] == bandera_de(juego, otro):
        quien['lleva'] = True                        # pisó la bandera del otro: se la roba
        cambiar_terreno(juego)                       # el terreno cambia cuando alguien roba
        if quien is juego['rival']:
            avisar(juego, f"{quien['nombre']} robó tu bandera")
    elif quien['lleva'] and quien['casilla'] == bandera_de(juego, quien):
        quien['puntos'] += 1                         # pisó su propia bandera cargando la del otro: punto
        quien['lleva'] = False
        otro['lleva'] = False                        # quien cargaba una bandera la pierde
        if quien['puntos'] >= PUNTOS_PARA_GANAR:
            juego['fase'] = 'final'
            return
        juego['turno'] += 1                          # las dos banderas saltan a la siguiente posición
        rival = juego['rival']
        if juego['eleccion'] == 'Azar':
            # En Azar, el rival cambia de algoritmo después de cada punto.
            nombre = random.choice([n for n in ALGORITMOS if n != rival['nombre']])
            rival.update({'nombre': nombre, 'algoritmo': ALGORITMOS[nombre], 'color': COLOR_DE[nombre]})
        cambiar_terreno(juego)                       # el terreno cambia cuando alguien anota
        avisar(juego, 'Punto para ti' if quien is juego['jugador'] else f"Punto para {quien['nombre']}")


def actualizar_bandera(juego, segundos, direcciones):
    """Avanza un cuadro de captura la bandera.

    Entradas:
        juego:       el diccionario de la partida
        segundos:    el tiempo que pasó desde el cuadro anterior
        direcciones: las direcciones que el jugador tiene oprimidas
    """
    juego['aviso_resta'] = max(0.0, juego['aviso_resta'] - segundos)
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

    mover_jugador(jugador, juego['mapa'], direcciones)
    conducir_rival(rival, juego['mapa'], objetivo_del_rival(juego), segundos)


# ============================================================================
# 6. DIBUJO DEL TABLERO
# El tablero se ve desde arriba e inclinado: las casillas son más anchas que
# altas, y los muros, los árboles y los personajes tienen altura. Se dibuja de
# la fila del fondo a la de enfrente, para que lo de adelante tape lo de atrás.
# ============================================================================

ANCHO, ALTO = 1280, 720
ACERCAMIENTO = 1.9                       # cuánto se agranda el tablero con la tecla C

COLOR_TERRENO = {'.': (236, 229, 196), 'B': (120, 178, 110), 'A': (104, 172, 232), '#': (92, 92, 98)}


def crear_vista(zona, mapa, centro=None):
    """Define dónde y de qué tamaño se dibuja un tablero dentro de una zona de la pantalla.

    Entradas:
        zona:   el rectángulo de la pantalla reservado para el tablero
        mapa:   el mapa que se va a dibujar
        centro: None para ver el tablero completo. Si se da una posición
                (fila, columna), el tablero se dibuja acercado y centrado en ella.

    Salida: diccionario con
        'x', 'y':  esquina superior izquierda del piso del tablero, en pixeles
        'ancho':   ancho de una casilla
        'alto':    alto de una casilla en pantalla. Es 3/4 del ancho: esa es la inclinación.
        'altura':  cuántos pixeles se levantan los muros
        'escala':  tamaño relativo; sirve para dibujar personajes, gemas y banderas
        'zona':    la misma zona, para recortar lo que se salga de ella
    """
    # El tamaño de casilla más grande con el que el tablero completo cabe en la zona.
    ancho = int(min(zona.width / mapa['columnas'], zona.height / (mapa['filas'] * 0.75)))
    if centro is not None:
        ancho = int(ancho * ACERCAMIENTO)
    alto = ancho * 3 // 4
    total_x, total_y = mapa['columnas'] * ancho, mapa['filas'] * alto
    if centro is None:
        x, y = zona.centerx - total_x // 2, zona.centery - total_y // 2
    else:
        # El personaje queda al centro de la zona, sin dejar que se vea más allá del borde del tablero.
        x = zona.centerx - (centro[1] + 0.5) * ancho
        y = zona.centery - (centro[0] + 0.5) * alto
        x = min(zona.x, max(zona.right - total_x, x))
        y = min(zona.y, max(zona.bottom - total_y, y))
    return {'x': x, 'y': y, 'ancho': ancho, 'alto': alto, 'altura': ancho * 2 // 5, 'escala': ancho / 48, 'zona': zona}


def en_pantalla(vista, fila, columna):
    """Convierte una posición del tablero en un punto de la pantalla.

    Entradas: la vista y la posición (fila, columna), que puede tener decimales.
    Salida:   el pixel (x, y) del centro del piso de esa posición.
    """
    return (vista['x'] + (columna + 0.5) * vista['ancho'], vista['y'] + (fila + 0.5) * vista['alto'])


def dibujar_piso(pantalla, vista, mapa, t):
    """Dibuja el piso del tablero: una losa por casilla, del color de su terreno.

    Entradas: la pantalla, la vista, el mapa y el tiempo t en segundos (para animar el agua).
    """
    w, h = vista['ancho'], vista['alto']
    for (f, c), terreno in mapa['terreno'].items():
        x, y = vista['x'] + c * w, vista['y'] + f * h
        color = COLOR_TERRENO['.'] if terreno == '#' else COLOR_TERRENO[terreno]
        pygame.draw.rect(pantalla, color, (x, y, w, h))
        pygame.draw.rect(pantalla, (0, 0, 0), (x, y, w, h), 1)       # borde fino de la casilla
        if terreno == 'A':
            # Dos ondas claras que se mueven de lado a lado.
            corrimiento = sin(t * 2 + f + c) * w * 0.08
            for k in (0.35, 0.68):
                pygame.draw.line(pantalla, (190, 222, 250), (x + w * 0.2 + corrimiento, y + h * k),
                                 (x + w * 0.8 + corrimiento, y + h * k), max(1, int(2 * vista['escala'])))


def dibujar_bloque(pantalla, vista, fila, columna, terreno):
    """Dibuja lo que tiene altura en una casilla: el bloque de un muro o los árboles de un bosque.

    Entradas: la pantalla, la vista, la casilla y su terreno.
    """
    w, h, alto = vista['ancho'], vista['alto'], vista['altura']
    x, y = vista['x'] + columna * w, vista['y'] + fila * h
    if terreno == '#':
        # Un bloque: la cara de arriba, levantada, y la cara de enfrente, más oscura.
        pygame.draw.rect(pantalla, (58, 58, 64), (x, y - alto + h, w, alto))        # cara de enfrente
        pygame.draw.rect(pantalla, COLOR_TERRENO['#'], (x, y - alto, w, h))          # cara de arriba
        pygame.draw.rect(pantalla, NEGRO, (x, y - alto, w, h + alto), 1)
    elif terreno == 'B':
        # Dos arbolitos: un tronco y una copa triangular.
        for dx, dy in ((0.3, 0.45), (0.7, 0.8)):
            bx, by = x + w * dx, y + h * dy
            pygame.draw.rect(pantalla, (110, 78, 48), (bx - w * 0.03, by - alto * 0.3, w * 0.06, alto * 0.3))
            pygame.draw.polygon(pantalla, (46, 125, 60), [(bx - w * 0.17, by - alto * 0.25),
                                                          (bx + w * 0.17, by - alto * 0.25), (bx, by - alto * 1.25)])


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


def dibujar_personaje(pantalla, vista, corredor, t, bandera=None):
    """Dibuja un personaje: sombra, cuerpo, cabeza y, si la carga, una bandera.

    Entradas:
        pantalla, vista
        corredor: el personaje
        t:        tiempo en segundos, para el saltito al caminar
        bandera:  el color de la bandera que carga, o None

    Mientras un rival piensa su ruta, lleva encima un globito con puntos suspensivos.
    """
    s = vista['escala']
    fila, columna = posicion(corredor)
    x, y = en_pantalla(vista, fila, columna)
    # Mientras camina da saltitos: sube y baja siguiendo una onda.
    salto = abs(sin(t * 12)) * 5 * s if corredor['destino'] is not None else 0

    pygame.draw.ellipse(pantalla, (70, 72, 66), (x - 14 * s, y - 5 * s, 28 * s, 10 * s))     # sombra en el piso
    cuerpo = pygame.Rect(x - 11 * s, y - 28 * s - salto, 22 * s, 26 * s)
    pygame.draw.rect(pantalla, corredor['color'], cuerpo, border_radius=int(6 * s))
    pygame.draw.rect(pantalla, NEGRO, cuerpo, max(1, int(2 * s)), border_radius=int(6 * s))
    cabeza = (x, y - 36 * s - salto)
    pygame.draw.circle(pantalla, (255, 224, 189), cabeza, 10 * s)
    pygame.draw.circle(pantalla, NEGRO, cabeza, 10 * s, max(1, int(2 * s)))
    for dx in (-4, 4):                                                # los ojos
        pygame.draw.circle(pantalla, NEGRO, (x + dx * s, y - 37 * s - salto), max(1, 1.6 * s))
    if bandera:
        dibujar_bandera(pantalla, vista, (x + 12 * s, y - 20 * s - salto), bandera, 0.7)
    if corredor['pensando'] > 0:
        # El globito de pensar: un óvalo blanco con tres puntos.
        globo = pygame.Rect(0, 0, 30 * s, 18 * s)
        globo.center = (x + 16 * s, y - 56 * s)
        pygame.draw.ellipse(pantalla, BLANCO, globo)
        pygame.draw.ellipse(pantalla, NEGRO, globo, max(1, int(2 * s)))
        for dx in (-7, 0, 7):
            pygame.draw.circle(pantalla, NEGRO, (globo.centerx + dx * s, globo.centery), max(1, 2 * s))


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


def dibujar_tablero(pantalla, vista, mapa, planos, altos, t):
    """Dibuja un tablero completo, respetando qué tapa a qué.

    Entradas:
        pantalla, vista, mapa
        planos: lista de funciones que dibujan cosas pegadas al piso (salidas, rutas, marcas)
        altos:  lista de pares (fila, funcion) con las cosas que tienen altura
                (personajes, gemas, banderas). La fila dice en qué momento se dibuja cada una.
        t:      tiempo en segundos

    Orden: primero todo el piso, luego lo pegado al piso y al final, fila por
    fila desde el fondo, los bloques de esa fila y las cosas paradas en ella.
    Así un muro de enfrente tapa a un personaje que está detrás. Lo que se sale
    de la zona del tablero se recorta: hace falta cuando la vista está acercada.
    """
    zona = vista['zona']
    # El recorte se extiende hacia arriba una casilla: es lo que sobresalen los muros
    # y los personajes de la primera fila.
    pantalla.set_clip(zona.x, zona.y - vista['ancho'], zona.width, zona.height + vista['ancho'])
    dibujar_piso(pantalla, vista, mapa, t)
    for dibujar in planos:
        dibujar()
    for fila in range(mapa['filas']):
        for columna in range(mapa['columnas']):
            terreno = mapa['terreno'][(fila, columna)]
            if terreno in '#B':
                dibujar_bloque(pantalla, vista, fila, columna, terreno)
        for fila_de_la_cosa, dibujar in altos:
            # Una cosa a medio paso entre dos filas se dibuja con la fila a la que está más cerca.
            if round(fila_de_la_cosa) == fila:
                dibujar()
    pantalla.set_clip(None)                          # se quita el recorte


# ============================================================================
# 7. LA INTERFAZ, AL ESTILO DE UN JUEGO DE CARRERAS
# ============================================================================

def crear_fuentes():
    """Prepara los tipos de letra.

    Salida: diccionario {'enorme', 'titulo', 'grande', 'normal', 'chica'}.
    """
    nombres = 'segoeui,arial,dejavusans'             # se usa el primero que exista en la computadora
    return {'enorme': pygame.font.SysFont(nombres, 150, bold=True),
            'titulo': pygame.font.SysFont(nombres, 60, bold=True),
            'grande': pygame.font.SysFont(nombres, 34, bold=True),
            'normal': pygame.font.SysFont(nombres, 22, bold=True),
            'chica': pygame.font.SysFont(nombres, 17)}


def escribir(pantalla, fuente, texto, posicion_del_texto, color=BLANCO, ancla='izquierda'):
    """Escribe un texto.

    Entradas:
        pantalla, fuente, texto
        posicion_del_texto: el punto (x, y) de referencia
        color:              color de la letra
        ancla:              'izquierda' (el punto es la esquina superior izquierda),
                            'derecha' (esquina superior derecha) o 'centro' (el centro del texto)
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


def dibujar_ficha(pantalla, color, zona):
    """Dibuja un cuadrito del color de un competidor, con borde blanco.

    Entradas: la pantalla, el color y el rectángulo.
    El borde hace falta porque el carbón de A* casi no se ve sobre el fondo oscuro.
    """
    pygame.draw.rect(pantalla, color, zona, border_radius=4)
    pygame.draw.rect(pantalla, BLANCO, zona, 2, border_radius=4)


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
    velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)        # oscurece el juego que queda detrás
    velo.fill((0, 0, 0, 150))
    pantalla.blit(velo, (0, 0))
    pygame.draw.rect(pantalla, NEGRO, zona, border_radius=12)
    pygame.draw.rect(pantalla, ROJO, zona, 5, border_radius=12)
    escribir(pantalla, fuentes['titulo'], titulo, (zona.centerx, zona.y + 56), BLANCO, 'centro')
    for i, (izquierda, derecha, color) in enumerate(renglones):
        y = zona.y + 112 + i * 38
        escribir(pantalla, fuentes['normal'], izquierda, (zona.x + 60, y), color)
        escribir(pantalla, fuentes['normal'], derecha, (zona.right - 60, y), color, 'derecha')
    escribir(pantalla, fuentes['chica'], pie, (zona.centerx, zona.bottom - 28), GRIS, 'centro')


# ---------------------------------------------------------------- atrapa gemas

def zona_de_tablero_de_gemas(numero):
    """Da el rectángulo de la pantalla donde va el tablero de un competidor.

    Entrada: el número del competidor, contando desde 0.
    Salida:  el rectángulo. Los tableros se acomodan en filas de tres.
    """
    return pygame.Rect(46 + (numero % 3) * 406, 122 + (numero // 3) * 310, 376, 256)


def dibujar_tablero_de_gemas(pantalla, juego, corredor, zona, t):
    """Dibuja el tablero de un competidor de atrapa gemas.

    Entradas: la pantalla, la partida, el corredor dueño del tablero, su zona y el tiempo.
    Cada competidor tiene su propio tablero y ve el terreno de la gema que busca.
    """
    mapa = mapa_de(juego, corredor)
    es_jugador = corredor is juego['jugador']
    # Con la tecla C, el tablero del jugador se acerca y lo sigue.
    vista = crear_vista(zona, mapa, posicion(corredor) if es_jugador and juego['acercar'] else None)
    radio = 9 * vista['escala']

    def salida():
        """Marca la casilla de salida con un punto verde."""
        centro = en_pantalla(vista, *SALIDA_GEMAS)
        pygame.draw.circle(pantalla, VERDE_INICIO, centro, radio)
        pygame.draw.circle(pantalla, NEGRO, centro, radio, max(1, int(2 * vista['escala'])))

    planos = [salida]
    if not es_jugador:
        planos.append(lambda: dibujar_ruta(pantalla, vista, corredor))       # la ruta que planeó el rival
    altos = [(posicion(corredor)[0], lambda: dibujar_personaje(pantalla, vista, corredor, t))]
    # Solo hay una gema a la vista: la que le toca a este competidor.
    if corredor['final'] is None:
        gema = juego['gemas'][corredor['siguiente']]
        altos.append((gema[0] - 0.1, lambda: dibujar_gema(pantalla, vista, gema, t)))
    dibujar_tablero(pantalla, vista, mapa, planos, altos, t)


def dibujar_gemas(pantalla, fuentes, juego, t):
    """Dibuja toda la pantalla de atrapa gemas.

    Entradas: la pantalla, las fuentes, la partida y el tiempo en segundos.
    Los tableros van en filas de tres, cada uno con el lugar que lleva su competidor.
    """
    pantalla.fill((36, 38, 44))
    dibujar_barra(pantalla, fuentes, 'Atrapa gemas', juego['reloj'])
    orden = clasificacion(juego)
    jugador = juego['jugador']

    if jugador is not None:
        escribir(pantalla, fuentes['normal'], f'Vas en el lugar {orden.index(jugador) + 1} de {len(orden)}',
                 (ANCHO // 2, 24), DORADO, 'centro')
    escribir(pantalla, fuentes['chica'], 'Flechas o W A S D: moverte.   C: acercar.   R: reiniciar.   Esc: menú.',
             (ANCHO // 2, 54), GRIS, 'centro')

    for numero, corredor in enumerate(juego['corredores']):
        zona = zona_de_tablero_de_gemas(numero)
        # Encabezado del tablero: el lugar que lleva, su color, su nombre y su avance.
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
        escribir(pantalla, fuentes['chica'], avance, (zona.right, y), GRIS, 'derecha')
        dibujar_tablero_de_gemas(pantalla, juego, corredor, zona, t)

    dibujar_cuenta(pantalla, fuentes, juego)

    if juego['anuncio']:
        # El cartel dice el lugar del jugador y los tiempos de quienes ya llegaron.
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


# ---------------------------------------------------------------- captura la bandera

ZONA_BANDERA = pygame.Rect(120, 190, 1040, 470)


def zonas_de_rival():
    """Da los rectángulos de los seis botones para elegir rival, al pie de la pantalla.

    Salida: lista de 6 rectángulos, en el mismo orden que OPCIONES_DE_RIVAL.
    """
    ancho = 150
    izquierda = (ANCHO - len(OPCIONES_DE_RIVAL) * (ancho + 8)) // 2
    return [pygame.Rect(izquierda + i * (ancho + 8), 672, ancho, 36) for i in range(len(OPCIONES_DE_RIVAL))]


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


def dibujar_bandera_juego(pantalla, fuentes, juego, t):
    """Dibuja toda la pantalla de captura la bandera.

    Entradas: la pantalla, las fuentes, la partida y el tiempo en segundos.
    """
    pantalla.fill((36, 38, 44))
    dibujar_barra(pantalla, fuentes, 'Captura la bandera', juego['reloj'])
    jugador, rival = juego['jugador'], juego['rival']
    mapa = juego['mapa']
    en_juego = juego['fase'] == 'carrera'
    vista = crear_vista(ZONA_BANDERA, mapa, posicion(jugador) if juego['acercar'] else None)

    # El marcador, al centro de la barra.
    escribir(pantalla, fuentes['grande'], f"Tú  {jugador['puntos']}", (ANCHO // 2 - 24, 14), (255, 110, 110), 'derecha')
    escribir(pantalla, fuentes['grande'], ':', (ANCHO // 2, 34), BLANCO, 'centro')
    escribir(pantalla, fuentes['grande'], f"{rival['puntos']}  {rival['nombre']}", (ANCHO // 2 + 24, 14))
    ancho_del_nombre = fuentes['grande'].size(f"{rival['puntos']}  {rival['nombre']}")[0]
    dibujar_ficha(pantalla, rival['color'], pygame.Rect(ANCHO // 2 + 34 + ancho_del_nombre, 24, 18, 26))

    def salidas():
        """Dibuja las dos salidas: un óvalo del color de su dueño, pegado al piso."""
        for corredor in (jugador, rival):
            x, y = en_pantalla(vista, *corredor['salida'])
            w, h = vista['ancho'] * 0.8, vista['alto'] * 0.8
            pygame.draw.ellipse(pantalla, corredor['color'], (x - w / 2, y - h / 2, w, h))
            pygame.draw.ellipse(pantalla, BLANCO, (x - w / 2, y - h / 2, w, h), 3)

    def rutas():
        """Dibuja la ruta planeada del rival y, si el jugador lleva la bandera, su ruta dorada."""
        dibujar_ruta(pantalla, vista, rival)
        if jugador['lleva'] and en_juego:
            dibujar_ruta(pantalla, vista, jugador, DORADO, ruta_dorada(juego))

    def destino_del_jugador():
        """Mientras el jugador lleva la bandera, hace latir con aros dorados el lugar a donde va."""
        if jugador['lleva'] and en_juego:
            x, y = en_pantalla(vista, *bandera_de(juego, jugador))
            for k in range(3):
                radio = (20 + ((t * 40 + k * 22) % 60)) * vista['escala']     # tres aros que crecen uno tras otro
                pygame.draw.ellipse(pantalla, DORADO, (x - radio, y - radio * 0.7, radio * 2, radio * 1.4), 4)

    altos = [(posicion(jugador)[0], lambda: dibujar_personaje(pantalla, vista, jugador, t, rival['color'] if jugador['lleva'] else None)),
             (posicion(rival)[0], lambda: dibujar_personaje(pantalla, vista, rival, t, jugador['color'] if rival['lleva'] else None))]
    # Cada bandera está clavada en su casilla mientras el otro no se la lleve.
    for dueño, otro in ((jugador, rival), (rival, jugador)):
        if not otro['lleva']:
            casilla = bandera_de(juego, dueño)
            pie = en_pantalla(vista, *casilla)
            altos.append((casilla[0] - 0.2, lambda pie=pie, dueño=dueño:
                          dibujar_bandera(pantalla, vista, pie, dueño['color'])))
    dibujar_tablero(pantalla, vista, mapa, [salidas, rutas, destino_del_jugador], altos, t)

    # Avisos fijos: qué hacer en este momento.
    if jugador['lleva'] and en_juego:
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
        mensaje, color = '¡Llevas la bandera! Llévala a donde está la tuya: sigue la ruta dorada.', DORADO
    elif rival['lleva'] and en_juego:
        mensaje, color = f"{rival['nombre']} te robó la bandera. Chócalo para recuperarla.", (255, 150, 150)
    else:
        mensaje, color = f"Roba la bandera de {rival['nombre']} y llévala a donde está la tuya.", BLANCO
    escribir(pantalla, fuentes['normal'], mensaje, (ANCHO // 2, 104), color, 'centro')
    escribir(pantalla, fuentes['chica'], f'A {PUNTOS_PARA_GANAR} puntos.   Flechas o W A S D: moverte.   C: acercar.   R: reiniciar.   Esc: menú.',
             (ANCHO // 2, 136), GRIS, 'centro')

    # Los botones para elegir rival. El elegido va en rojo.
    for numero, (opcion, zona) in enumerate(zip(OPCIONES_DE_RIVAL, zonas_de_rival())):
        pygame.draw.rect(pantalla, ROJO if opcion == juego['eleccion'] else GRIS_OSCURO, zona, border_radius=8)
        if opcion in COLOR_DE:
            dibujar_ficha(pantalla, COLOR_DE[opcion], pygame.Rect(zona.x + 8, zona.y + 8, 14, 20))
        escribir(pantalla, fuentes['chica'], f'{numero + 1}  {opcion}', (zona.centerx + 8, zona.centery), BLANCO, 'centro')
    escribir(pantalla, fuentes['chica'], 'Rival:', (zonas_de_rival()[0].x - 12, 680), GRIS, 'derecha')

    if juego['aviso_resta'] > 0 and juego['fase'] != 'final':
        # El aviso de choque, de robo o de punto, sobre una franja oscura.
        franja = pygame.Surface((ANCHO, 76), pygame.SRCALPHA)
        franja.fill((0, 0, 0, 190))
        pantalla.blit(franja, (0, ALTO // 2 - 38))
        escribir(pantalla, fuentes['grande'], juego['aviso'], (ANCHO // 2, ALTO // 2), DORADO, 'centro')
    dibujar_cuenta(pantalla, fuentes, juego)

    if juego['fase'] == 'final':
        gano = jugador['puntos'] > rival['puntos']
        renglones = [('Tú', jugador['puntos'], DORADO), (rival['nombre'], rival['puntos'], BLANCO),
                     ('Tiempo', texto_de_tiempo(juego['reloj']), GRIS)]
        dibujar_cartel(pantalla, fuentes, '¡Ganaste!' if gano else f"Ganó {rival['nombre']}", renglones,
                       'Espacio o Enter: otra partida.   R: reiniciar.   Esc: menú.')


# ---------------------------------------------------------------- menú

MENU_PRINCIPAL = ['Atrapa gemas', 'Captura la bandera', 'Salir']
DESCRIPCIONES = {'Atrapa gemas': 'Carrera contra los cinco algoritmos, cada quien en su tablero.',
                 'Captura la bandera': 'Uno contra uno: roba la bandera rival y llévala a donde está la tuya. A tres puntos.',
                 'Salir': 'Cierra el juego.'}


def zonas_del_menu(opciones):
    """Calcula el rectángulo de cada opción de un menú.

    Entrada: la lista de opciones.
    Salida:  lista de rectángulos, uno por opción, centrados en la pantalla.
             Sirven para dibujar el menú y para saber en cuál se hizo clic.
    """
    alto = 58
    return [pygame.Rect(ANCHO // 2 - 230, 300 + i * (alto + 10), 460, alto) for i in range(len(opciones))]


def dibujar_menu(pantalla, fuentes, titulo, subtitulo, opciones, elegida, pie):
    """Dibuja un menú: título, opciones y la opción elegida resaltada en rojo.

    Entradas: la pantalla, las fuentes, el título, el subtítulo, la lista de
              opciones, el número de la opción elegida y el texto de abajo.
    """
    pantalla.fill((24, 24, 28))
    pygame.draw.rect(pantalla, ROJO, (0, 0, ANCHO, 12))
    escribir(pantalla, fuentes['titulo'], titulo, (ANCHO // 2, 120), BLANCO, 'centro')
    escribir(pantalla, fuentes['normal'], subtitulo, (ANCHO // 2, 184), GRIS, 'centro')
    for i, (opcion, zona) in enumerate(zip(opciones, zonas_del_menu(opciones))):
        pygame.draw.rect(pantalla, ROJO if i == elegida else GRIS_OSCURO, zona, border_radius=10)
        escribir(pantalla, fuentes['grande'], opcion, zona.center, BLANCO, 'centro')
    escribir(pantalla, fuentes['chica'], pie, (ANCHO // 2, 676), GRIS, 'centro')


# ============================================================================
# 8. EL PROGRAMA
# ============================================================================

# Las teclas de movimiento y el movimiento (cambio de fila, cambio de columna) de cada una.
TECLAS_DE_MOVIMIENTO = {pygame.K_UP: (-1, 0), pygame.K_w: (-1, 0), pygame.K_RIGHT: (0, 1), pygame.K_d: (0, 1),
                        pygame.K_DOWN: (1, 0), pygame.K_s: (1, 0), pygame.K_LEFT: (0, -1), pygame.K_a: (0, -1)}
# Las teclas 1 a 6 eligen al rival en captura la bandera.
TECLAS_DE_RIVAL = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]


def crear_estado():
    """Prepara todo lo que cambia mientras corre el programa.

    Salida: un diccionario con
        'pantalla':    'menu' o 'juego'
        'elegida':     el número de la opción resaltada en el menú
        'juego':       la partida en curso, o None
        'rival':       el rival elegido para captura la bandera. Se conserva de
                       una partida a otra y empieza en A*.
        'direcciones': los movimientos que el jugador tiene oprimidos, del más viejo al más reciente
        'abierto':     False cuando hay que cerrar el programa
    """
    return {'pantalla': 'menu', 'elegida': 0, 'juego': None, 'rival': 'A*', 'direcciones': [], 'abierto': True}


def empezar(estado, tipo):
    """Empieza una partida nueva.

    Entradas: el estado y el tipo de juego: 'gemas' o 'bandera'.
    """
    estado['juego'] = crear_gemas() if tipo == 'gemas' else crear_bandera(estado['rival'])
    estado['pantalla'] = 'juego'
    estado['direcciones'] = []


def elegir(estado, opcion):
    """Hace lo que corresponde a una opción del menú.

    Entradas: el estado y el texto de la opción elegida.
    """
    if opcion == 'Atrapa gemas':
        empezar(estado, 'gemas')
    elif opcion == 'Captura la bandera':
        empezar(estado, 'bandera')
    elif opcion == 'Salir':
        estado['abierto'] = False


def elegir_rival(estado, opcion):
    """Cambia el rival de captura la bandera y empieza una partida contra él.

    Entradas: el estado y la opción: el nombre de un algoritmo o 'Azar'.
    """
    estado['rival'] = opcion                         # se conserva para las partidas siguientes
    empezar(estado, 'bandera')


def terminada(juego):
    """Dice si una partida ya terminó: se anunció el resultado o alguien llegó a 3 puntos."""
    return juego['anuncio'] if juego['tipo'] == 'gemas' else juego['fase'] == 'final'


def atender(estado, evento):
    """Atiende un evento del teclado o del ratón.

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
        juego = estado['juego']
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:        # Esc: al menú
                estado['pantalla'] = 'menu'
                estado['juego'] = None
            elif evento.key == pygame.K_r:           # R: reinicia en cualquier momento
                empezar(estado, juego['tipo'])
            elif evento.key in (pygame.K_SPACE, pygame.K_RETURN) and terminada(juego):
                empezar(estado, juego['tipo'])       # otra partida, cuando ya terminó
            elif evento.key == pygame.K_c:           # C: acerca la vista al jugador, o la regresa
                juego['acercar'] = not juego['acercar']
            elif juego['tipo'] == 'bandera' and evento.key in TECLAS_DE_RIVAL:
                elegir_rival(estado, OPCIONES_DE_RIVAL[TECLAS_DE_RIVAL.index(evento.key)])
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and juego['tipo'] == 'bandera':
            for opcion, zona in zip(OPCIONES_DE_RIVAL, zonas_de_rival()):
                if zona.collidepoint(evento.pos):
                    elegir_rival(estado, opcion)
                    break
        return

    # En el menú: flechas y Enter, o clic con el ratón.
    if evento.type == pygame.KEYDOWN:
        if evento.key in (pygame.K_UP, pygame.K_w):
            estado['elegida'] = (estado['elegida'] - 1) % len(MENU_PRINCIPAL)    # da la vuelta al llegar arriba
        elif evento.key in (pygame.K_DOWN, pygame.K_s):
            estado['elegida'] = (estado['elegida'] + 1) % len(MENU_PRINCIPAL)
        elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
            elegir(estado, MENU_PRINCIPAL[estado['elegida']])
        elif evento.key == pygame.K_ESCAPE:
            estado['abierto'] = False
    elif evento.type == pygame.MOUSEMOTION:
        for i, zona in enumerate(zonas_del_menu(MENU_PRINCIPAL)):
            if zona.collidepoint(evento.pos):
                estado['elegida'] = i
    elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
        for i, zona in enumerate(zonas_del_menu(MENU_PRINCIPAL)):
            if zona.collidepoint(evento.pos):
                elegir(estado, MENU_PRINCIPAL[i])
                break


def actualizar(estado, segundos):
    """Avanza un cuadro de la partida en curso, si la hay.

    Entradas: el estado y los segundos que pasaron desde el cuadro anterior.
    """
    juego = estado['juego']
    if estado['pantalla'] != 'juego' or juego is None:
        return
    if juego['tipo'] == 'gemas':
        actualizar_gemas(juego, segundos, estado['direcciones'])
    else:
        actualizar_bandera(juego, segundos, estado['direcciones'])


def dibujar(pantalla, fuentes, estado, t):
    """Dibuja la pantalla que toque: el menú o un juego.

    Entradas: la pantalla, las fuentes, el estado y el tiempo en segundos desde que abrió el programa.
    """
    if estado['pantalla'] == 'menu':
        opcion = MENU_PRINCIPAL[estado['elegida']]
        dibujar_menu(pantalla, fuentes, 'MazeRunner', 'Fase 3: juega contra los algoritmos', MENU_PRINCIPAL,
                     estado['elegida'], DESCRIPCIONES[opcion] + '   Flechas y Enter, o el ratón.')
    elif estado['juego']['tipo'] == 'gemas':
        dibujar_gemas(pantalla, fuentes, estado['juego'], t)
    else:
        dibujar_bandera_juego(pantalla, fuentes, estado['juego'], t)


def principal():
    """Abre la ventana y corre el programa hasta que se cierre.

    En cada vuelta del ciclo se hacen tres cosas: atender el teclado y el
    ratón, avanzar la partida y volver a dibujar todo.
    """
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption('MazeRunner, fase 3: juegos')
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
