"""BFS (búsqueda en anchura): basado en la página 22 de la presentación.

Este archivo solo contiene la lógica: no dibuja ni crea ventanas.
Las coordenadas son parejas (fila, columna), empezando desde cero.
"""
from collections import deque  # Cola eficiente: primero en entrar, primero en salir.


def vecinos(casilla, filas, columnas, muros):
    """Devuelve las casillas a las que podemos movernos en un paso."""
    fila, columna = casilla  # Separar una pareja en dos variables.
    resultado = []  # Lista vacía; parecido a un arreglo que puede crecer.
    # El orden es fijo: arriba, derecha, abajo e izquierda.
    for cambio_fila, cambio_columna in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
        nueva = (fila + cambio_fila, columna + cambio_columna)
        dentro = 0 <= nueva[0] < filas and 0 <= nueva[1] < columnas
        if dentro and nueva not in muros:
            resultado.append(nueva)  # Agregar al final de la lista.
    return resultado


def bfs(filas, columnas, muros, inicio, salida):
    """Produce un estado por extracción de la cola, para poder animar BFS.

    `yield` entrega un estado y suspende la función. La siguiente llamada
    a next() continúa donde se quedó. No es lo mismo que return, que termina.
    Cada estado es un diccionario con nombres para sus datos.
    """
    # Página 22, líneas 1-2: preparar cola, Descubierto y Memoria.
    cola = deque([inicio])
    descubierto = {inicio}  # Conjunto (set): elementos sin repetir.
    memoria = {inicio: None}  # Diccionario: casilla -> antecesor.
    extraidos = []  # Orden de procesamiento, incluyendo la meta al encontrarla.

    # Línea 3: mientras queden nodos pendientes.
    while cola:
        actual = cola.popleft()  # Línea 4: sacar el PRIMERO, no el último.
        extraidos.append(actual)
        camino = []
        terminado = actual == salida  # Línea 5: prueba de meta.

        if terminado:
            # Línea 6: reconstruir siguiendo los antecesores hacia atrás.
            casilla = salida
            while casilla is not None:
                camino.append(casilla)
                casilla = memoria[casilla]
            camino.reverse()  # Ahora queda del inicio hacia la salida.
        else:
            # Líneas 7-9: descubrir sucesores y agregarlos a la cola.
            for vecino in vecinos(actual, filas, columnas, muros):
                if vecino not in descubierto:
                    descubierto.add(vecino)  # Se marca AL ENCOLAR.
                    memoria[vecino] = actual  # Recordar desde dónde llegamos.
                    cola.append(vecino)  # Insertar al FINAL de la cola.

        # Si se agotó la cola sin llegar, no existe un camino a la salida.
        terminado = terminado or not cola
        # Las copias evitan que un estado anterior cambie en el siguiente paso.
        yield {
            'actual': actual,
            'cola': list(cola),
            'descubiertos': set(descubierto),
            'extraidos': list(extraidos),
            'memoria': dict(memoria),
            'camino': camino,
            'terminado': terminado,
        }
        if terminado:
            return
