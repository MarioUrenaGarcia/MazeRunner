"""MazeLab, avance 1: una salida y BFS. Ejecutar: python main.py.

Lee primero algorithms.py. Aquí conectamos esa lógica con Tkinter.
Tkinter utiliza eventos: botones y clics llaman funciones (callbacks).
"""
import tkinter as tk
from tkinter import ttk
from algorithms import bfs

FILAS, COLUMNAS, TAMANO = 11, 17, 38


class MazeLab:
    """Agrupa el estado y las acciones de la ventana.

    `self` identifica esta instancia; self.inicio, por ejemplo, es su inicio.
    __init__ se ejecuta al crear el objeto MazeLab(ventana).
    """
    def __init__(self, ventana):
        self.ventana = ventana
        ventana.title('MazeLab · Primer avance: BFS')
        self.inicio = (1, 1)
        self.salida = (9, 15)
        self.muros = set()
        self.busqueda = None  # None significa que todavía no hay búsqueda.
        self.temporizador = None
        self.estado = None
        self.pausado = True

        # Las variables de Tkinter se conectan con los controles de pantalla.
        self.pincel = tk.StringVar(value='Muro')
        self.mensaje = tk.StringVar(value='')
        self.cola_texto = tk.StringVar(value='Cola: todavía vacía.')
        marco = ttk.Frame(ventana, padding=12)
        marco.pack()
        ttk.Label(marco, text='MazeLab · BFS', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        ttk.Label(marco, text='Una casilla libre = vértice. Un movimiento = arista de costo 1.').pack(anchor='w')
        botones = ttk.Frame(marco)
        botones.pack(pady=8)
        # command recibe la función SIN paréntesis: se ejecutará al pulsar.
        for texto, funcion in [('Ejemplo', self.ejemplo), ('Vaciar', self.vaciar),
                               ('Ejecutar BFS', self.ejecutar), ('Pausar', self.pausar),
                               ('Paso', self.paso), ('Reiniciar búsqueda', self.reiniciar)]:
            ttk.Button(botones, text=texto, command=funcion).pack(side='left', padx=2)
        ttk.Combobox(marco, textvariable=self.pincel,
                     values=['Muro', 'Borrar', 'Inicio', 'Salida'], state='readonly').pack(anchor='w')
        self.lienzo = tk.Canvas(marco, width=COLUMNAS*TAMANO, height=FILAS*TAMANO, highlightthickness=0)
        self.lienzo.pack(pady=8)
        self.lienzo.bind('<Button-1>', self.editar)
        self.lienzo.bind('<B1-Motion>', self.editar)
        ttk.Label(marco, text='S verde: inicio · E rosa: salida · Amarillo: cola · Azul: procesados · Violeta: ruta').pack(anchor='w')
        ttk.Label(marco, textvariable=self.mensaje, wraplength=650).pack(anchor='w', pady=5)
        ttk.Label(marco, textvariable=self.cola_texto, wraplength=650).pack(anchor='w')
        self.ejemplo()

    def reiniciar(self):
        """Cancela la animación y limpia la búsqueda, conservando el tablero."""
        if self.temporizador is not None:
            self.ventana.after_cancel(self.temporizador)
        self.temporizador = None
        self.busqueda = None
        self.estado = None
        self.pausado = True
        self.mensaje.set('Listo. Pulsa Paso para examinar una extracción de la cola.')
        self.cola_texto.set('Cola: todavía vacía. Coordenadas: (fila, columna), desde 0.')
        self.dibujar()

    def ejemplo(self):
        """Mapa fijo: permite repetir exactamente la demostración.

        La generación aleatoria queda para otra entrega, así estudiamos
        solamente BFS y no otro algoritmo de generación de laberintos.
        """
        self.inicio, self.salida = (1, 1), (9, 15)
        self.muros = set()
        for fila in range(FILAS):
            for columna in range(COLUMNAS):
                if fila in (0, FILAS-1) or columna in (0, COLUMNAS-1):
                    self.muros.add((fila, columna))
        for columna, huecos in [(4, (2, 8)), (8, (3, 7)), (12, (2, 9))]:
            for fila in range(1, FILAS-1):
                if fila not in huecos:
                    self.muros.add((fila, columna))
        self.reiniciar()

    def vaciar(self):
        self.muros.clear()
        self.reiniciar()

    def dibujar(self):
        """Traduce el estado del programa en colores; no realiza BFS."""
        self.lienzo.delete('all')
        pendientes = set(self.estado['cola']) if self.estado else set()
        procesados = set(self.estado['extraidos']) if self.estado else set()
        camino = set(self.estado['camino']) if self.estado else set()
        for fila in range(FILAS):
            for columna in range(COLUMNAS):
                casilla = (fila, columna)
                color = '#f1f5f9'
                if casilla in self.muros:
                    color = '#263449'
                elif casilla in camino:
                    color = '#a78bfa'
                elif casilla in procesados:
                    color = '#93c5fd'
                elif casilla in pendientes:
                    color = '#fde68a'
                letra = ''
                if casilla == self.inicio:
                    color, letra = '#22c55e', 'S'
                elif casilla == self.salida:
                    color, letra = '#fb7185', 'E'
                x, y = columna*TAMANO, fila*TAMANO
                self.lienzo.create_rectangle(x, y, x+TAMANO, y+TAMANO, fill=color, outline='#cbd5e1')
                if letra:
                    self.lienzo.create_text(x+TAMANO/2, y+TAMANO/2, text=letra)

    def editar(self, evento):
        """Convierte píxeles del clic en una casilla de la cuadrícula."""
        casilla = (evento.y // TAMANO, evento.x // TAMANO)
        if not (0 <= casilla[0] < FILAS and 0 <= casilla[1] < COLUMNAS):
            return
        herramienta = self.pincel.get()
        if herramienta == 'Inicio' and casilla != self.salida:
            self.inicio = casilla
            self.muros.discard(casilla)
        elif herramienta == 'Salida' and casilla != self.inicio:
            self.salida = casilla  # Reemplaza la anterior: siempre hay una sola.
            self.muros.discard(casilla)
        elif casilla not in (self.inicio, self.salida):
            if herramienta == 'Muro':
                self.muros.add(casilla)
            elif herramienta == 'Borrar':
                self.muros.discard(casilla)
        self.reiniciar()

    def avanzar(self):
        """next solicita un estado al generador BFS (ver yield)."""
        if self.estado and self.estado['terminado']:
            return  # Conservar el resultado hasta reiniciar.
        if self.busqueda is None:
            self.busqueda = bfs(FILAS, COLUMNAS, self.muros, self.inicio, self.salida)
        self.estado = next(self.busqueda)
        cantidad = len(self.estado['extraidos'])
        self.cola_texto.set('Cola, primero → último: ' + str(self.estado['cola']))
        self.mensaje.set(f'Extraído: {self.estado["actual"]}. Nodos extraídos: {cantidad}.')
        if self.estado['terminado']:
            if self.estado['camino']:
                pasos = len(self.estado['camino']) - 1
                self.mensaje.set(f'Salida encontrada: {pasos} aristas; {cantidad} nodos extraídos (incluye inicio y meta).')
            else:
                self.mensaje.set(f'Sin camino: cola agotada después de extraer {cantidad} nodos.')
        self.dibujar()

    def paso(self):
        self.pausar()
        self.avanzar()

    def ejecutar(self):
        self.pausar()  # Evita programar dos animaciones simultáneas.
        self.pausado = False
        self.animar()

    def pausar(self):
        self.pausado = True
        if self.temporizador is not None:
            self.ventana.after_cancel(self.temporizador)
            self.temporizador = None

    def animar(self):
        self.temporizador = None
        if self.pausado:
            return
        self.avanzar()
        if not self.estado['terminado']:
            # after espera sin bloquear la ventana; vuelve a llamar a animar.
            self.temporizador = self.ventana.after(120, self.animar)


# Solo abrir la ventana cuando este archivo sea el programa principal.
if __name__ == '__main__':
    ventana = tk.Tk()
    aplicacion = MazeLab(ventana)
    ventana.mainloop()  # Atiende clics y botones hasta cerrar la ventana.
