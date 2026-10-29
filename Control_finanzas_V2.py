import json
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk

ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transacciones.json")
FORMATO_FECHA = "%d/%m/%Y"
FORMATO_HORA = "%H:%M"
MONTO_MAXIMO = 999999999999

CATEGORIAS = ("Comida", "Transporte", "Salud", "Servicios", "Arriendo", "Personal", "Ocio", "Salario")
PERIODOS = ("Todo", "Semana", "Mes", "Mes pasado")

AERO_BLUE_BG = "#d0e8f7"
AERO_BLUE_TOP = "#1fa2ff"
AERO_BLUE_BOTTOM = "#1262ab"
AERO_GREEN_TOP = "#34d058"
AERO_GREEN_BOTTOM = "#1be85d"
AERO_ROJO_TOP = "#ff5f56"
AERO_ROJO_BOTTOM = "#c0392b"
TEXTO_DARK = "#1a364a"
GRIS_TEXTO = "#4a6275"
BORDE_CRISTAL = "#ffffff"
SHADOW_COLOR = "#a2c4dd"
FUENTE = "Trebuchet MS"
MARGEN = 25

def dinero(valor):
    texto = f"{abs(valor):,}".replace(",", ".")
    if valor < 0:
        return "-$" + texto
    return "$" + texto

def leer_monto(texto):
    mensaje = "El valor debe ser un número entero, por ejemplo 25000 o 25.000."
    texto = texto.replace("$", "").replace(" ", "")

    partes = texto.split(".")
    if len(partes) > 1:
        if len(partes[0]) < 1 or len(partes[0]) > 3:
            raise ValueError(mensaje)
        for parte in partes[1:]:
            if len(parte) != 3:
                raise ValueError(mensaje)
    numero = "".join(partes)

    if not (numero.isascii() and numero.isdigit()):
        raise ValueError(mensaje)
    valor = int(numero)
    if valor <= 0:
        raise ValueError("El valor debe ser mayor a cero.")
    if valor > MONTO_MAXIMO:
        raise ValueError("El valor es demasiado grande.")
    return valor

def leer_fecha(fecha, hora):
    try:
        momento = datetime.strptime(fecha.strip() + " " + hora.strip(), FORMATO_FECHA + " " + FORMATO_HORA)
    except ValueError:
        raise ValueError("La fecha o la hora no es válida.\nEjemplo: 27/10/2026 y 14:30")
    if momento.year < 2000 or momento > datetime.now() + timedelta(days=1):
        raise ValueError("La fecha es muy antigua o está en el futuro.")
    return momento

def limpiar_texto(texto, maximo, nombre, obligatorio):
    texto = " ".join(texto.split())
    if obligatorio and texto == "":
        raise ValueError("Escribe una " + nombre + ".")
    if len(texto) > maximo:
        raise ValueError("La " + nombre + " puede tener máximo " + str(maximo) + " letras.")
    return texto

def rango_periodo(periodo):
    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    lunes = hoy - timedelta(days=hoy.weekday())
    primer_dia_mes = hoy.replace(day=1)
    primer_dia_mes_siguiente = (primer_dia_mes + timedelta(days=32)).replace(day=1)
    primer_dia_mes_pasado = (primer_dia_mes - timedelta(days=1)).replace(day=1)

    if periodo == "Semana":
        return lunes, lunes + timedelta(days=7)
    if periodo == "Mes":
        return primer_dia_mes, primer_dia_mes_siguiente
    if periodo == "Mes pasado":
        return primer_dia_mes_pasado, primer_dia_mes
    return None

def obtener_fecha(transaccion):
    return (transaccion.fecha, transaccion.id)

def obtener_total(par):
    return par[1]

class Transaccion:
    tipo = ""
    signo = 1

    def __init__(self, id_transaccion, categoria, monto, descripcion, fecha):
        self.id = id_transaccion
        self.categoria = categoria
        self.monto = monto
        self.descripcion = descripcion
        self.fecha = fecha

    def valor(self):
        return self.signo * self.monto

    def a_diccionario(self):
        return {
            "tipo": self.tipo,
            "categoria": self.categoria,
            "monto": self.monto,
            "descripcion": self.descripcion,
            "fecha": self.fecha.strftime("%Y-%m-%d %H:%M"),
        }

class Ingreso(Transaccion):
    tipo = "ingreso"
    signo = 1

class Gasto(Transaccion):
    tipo = "gasto"
    signo = -1

CLASES = {"ingreso": Ingreso, "gasto": Gasto}

class GestorFinanzas:
    def __init__(self, archivo=ARCHIVO):
        self.archivo = archivo
        self.transacciones = {}
        self.siguiente_id = 1
        self.avisos = []
        self.cargar()

    def cargar(self):
        if not os.path.exists(self.archivo):
            return
        try:
            with open(self.archivo, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            guardadas = datos["transacciones"]
            siguiente = int(datos["siguiente_id"])
            if not isinstance(guardadas, dict):
                raise ValueError("formato incorrecto")
        except (OSError, ValueError, KeyError, TypeError):
            self.respaldar_archivo()
            return

        omitidas = 0
        for clave in guardadas:
            try:
                d = guardadas[clave]
                try:
                    fecha = datetime.strptime(d.get("fecha", ""), "%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    fecha = datetime.now()
                clase = CLASES[d["tipo"]]
                t = clase(int(clave), str(d["categoria"]).strip(), int(round(d["monto"])),
                          str(d.get("descripcion", "")), fecha)
                if t.categoria == "" or t.monto <= 0 or t.monto > MONTO_MAXIMO:
                    raise ValueError("registro incorrecto")
                self.transacciones[t.id] = t
            except (KeyError, ValueError, TypeError, AttributeError, OverflowError):
                omitidas = omitidas + 1
        if omitidas > 0:
            self.avisos.append("Se omitieron " + str(omitidas) + " registro(s) dañado(s) del archivo.")

        self.siguiente_id = siguiente
        for id_existente in self.transacciones:
            if id_existente >= self.siguiente_id:
                self.siguiente_id = id_existente + 1

    def respaldar_archivo(self):
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        copia = self.archivo.replace(".json", "_dañado_" + marca + ".json")
        try:
            os.replace(self.archivo, copia)
            self.avisos.append("El archivo de datos estaba dañado.\nSe guardó una copia: " + os.path.basename(copia))
        except OSError:
            self.avisos.append("El archivo de datos está dañado y no se pudo respaldar.")

    def guardar(self):
        diccionario = {}
        for id_t in self.transacciones:
            diccionario[str(id_t)] = self.transacciones[id_t].a_diccionario()
        datos = {"siguiente_id": self.siguiente_id, "transacciones": diccionario}

        temporal = self.archivo + ".tmp"
        try:
            with open(temporal, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, indent=2, ensure_ascii=False)
            os.replace(temporal, self.archivo)
        except OSError as error:
            raise ValueError("No se pudo guardar el archivo: " + str(error))

    def crear_transaccion(self, id_t, tipo, categoria, monto, descripcion, fecha, hora):
        if tipo not in CLASES:
            raise ValueError("Elige si es ingreso o gasto.")
        categoria = limpiar_texto(categoria, 30, "categoría", True).capitalize()
        descripcion = limpiar_texto(descripcion, 100, "descripción", False)
        valor = leer_monto(monto)
        momento = leer_fecha(fecha, hora)
        clase = CLASES[tipo]
        return clase(id_t, categoria, valor, descripcion, momento)

    def agregar(self, tipo, categoria, monto, descripcion, fecha, hora):
        nueva = self.crear_transaccion(self.siguiente_id, tipo, categoria, monto, descripcion, fecha, hora)
        self.transacciones[nueva.id] = nueva
        self.siguiente_id = self.siguiente_id + 1
        self.guardar()

    def editar(self, id_t, tipo, categoria, monto, descripcion, fecha, hora):
        if id_t not in self.transacciones:
            raise ValueError("Esa transacción ya no existe.")
        self.transacciones[id_t] = self.crear_transaccion(id_t, tipo, categoria, monto, descripcion, fecha, hora)
        self.guardar()

    def eliminar(self, id_t):
        if id_t not in self.transacciones:
            raise ValueError("Esa transacción ya no existe.")
        del self.transacciones[id_t]
        self.guardar()

    def calcular_saldo(self):
        saldo = 0
        for t in self.transacciones.values():
            saldo = saldo + t.valor()
        return saldo

    def filtrar(self, periodo):
        rango = rango_periodo(periodo)
        lista = []
        for t in self.transacciones.values():
            if rango is None or (t.fecha >= rango[0] and t.fecha < rango[1]):
                lista.append(t)
        lista.sort(key=obtener_fecha, reverse=True)
        return lista

    def calcular_totales(self, lista):
        ingresos = 0
        gastos = 0
        for t in lista:
            if t.tipo == "ingreso":
                ingresos = ingresos + t.monto
            else:
                gastos = gastos + t.monto
        return ingresos, gastos

    def gastos_por_categoria(self, lista):
        acumulado = {}
        for t in lista:
            if t.tipo == "gasto":
                if t.categoria in acumulado:
                    acumulado[t.categoria] = acumulado[t.categoria] + t.monto
                else:
                    acumulado[t.categoria] = t.monto
        resultado = list(acumulado.items())
        resultado.sort(key=obtener_total, reverse=True)
        return resultado

    def resumen_por_semana_o_mes(self, lista, agrupar):
        grupos = {}
        for t in lista:
            dia = t.fecha.date()
            if agrupar == "Mes":
                clave = (dia.year, dia.month)
            else:
                clave = dia - timedelta(days=dia.weekday())
            if clave not in grupos:
                grupos[clave] = [0, 0]
            if t.tipo == "ingreso":
                grupos[clave][0] = grupos[clave][0] + t.monto
            else:
                grupos[clave][1] = grupos[clave][1] + t.monto

        claves = list(grupos.keys())
        claves.sort(reverse=True)
        filas = []
        for clave in claves:
            if agrupar == "Mes":
                nombre = f"{clave[1]:02d}/{clave[0]}"
            else:
                domingo = clave + timedelta(days=6)
                nombre = f"{clave:%d/%m} al {domingo:%d/%m/%Y}"
            filas.append((nombre, grupos[clave][0], grupos[clave][1]))
        return filas

def puntos_redondeados(x1, y1, x2, y2, radio):
    return [x1 + radio, y1, x2 - radio, y1, x2, y1, x2, y1 + radio,
            x2, y2 - radio, x2, y2, x2 - radio, y2, x1 + radio, y2,
            x1, y2, x1, y2 - radio, x1, y1 + radio, x1, y1]

class BotonAero(tk.Canvas):

    def __init__(self, padre, texto, comando, c_top="#1fa2ff", c_bot="#1262ab", color_texto="white",
                 alto=48, radio=16, ancho=110, tamano=10, subtitulo="", es_chip=False):
        super().__init__(padre, width=ancho, height=alto, bg="#e8f4fc", highlightthickness=0, cursor="hand2")
        self.texto = texto
        self.subtitulo = subtitulo
        self.comando = comando
        self.c_top = c_top
        self.c_bot = c_bot
        self.color_texto = color_texto
        self.radio = radio
        self.tamano = tamano
        self.es_chip = es_chip
        self.activo = True

        self.bind("<Configure>", self.redibujar)
        self.bind("<Button-1>", lambda e: self.comando())
        self.bind("<Enter>", self.al_entrar)
        self.bind("<Leave>", self.al_salir)

    def redibujar(self, evento=None):
        self.delete("all")
        ancho = self.winfo_width()
        alto = self.winfo_height()
        if ancho < 10 or alto < 10:
            return

        self.create_polygon(puntos_redondeados(2, 4, ancho - 2, alto, self.radio), smooth=True, fill="#b5d3e7", outline="")

        pasos = 14
        for i in range(pasos):
            y1 = 1 + (i * (alto - 4) / pasos)
            y2 = 1 + ((i + 1) * (alto - 4) / pasos)
            factor = i / (pasos - 1)
            color_paso = self.interpolar_color(self.c_top, self.c_bot, factor)
            self.create_polygon(puntos_redondeados(2, 1, ancho - 2, alto - 3, self.radio), smooth=True, fill=color_paso, outline="")

        self.create_polygon(puntos_redondeados(2, 1, ancho - 2, alto - 3, self.radio), smooth=True, fill="", outline="#ffffff", width=2)

        reflejo_h = int((alto - 4) * 0.45)
        self.create_polygon(puntos_redondeados(4, 3, ancho - 4, 3 + reflejo_h, max(2, self.radio - 4)),
                            smooth=True, fill="#ffffff", outline="", stipple="gray25")

        if self.subtitulo == "":
            self.create_text(ancho / 2 + 1, alto / 2 + 1, text=self.texto, fill="#082b42", font=(FUENTE, self.tamano, "bold"))
            self.create_text(ancho / 2, alto / 2, text=self.texto, fill=self.color_texto, font=(FUENTE, self.tamano, "bold"))
        else:
            self.create_text(ancho / 2 + 1, alto / 2 - 10, text=self.texto, fill="#082b42", font=(FUENTE, self.tamano, "bold"))
            self.create_text(ancho / 2, alto / 2 - 11, text=self.texto, fill=self.color_texto, font=(FUENTE, self.tamano, "bold"))
            self.create_text(ancho / 2, alto / 2 + 16, text=self.subtitulo, fill="#e1f2fd", font=(FUENTE, 9), width=ancho - 20, justify="center")

    def interpolar_color(self, c1, c2, factor):
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def al_entrar(self, e):
        self.config(cursor="hand2")

    def al_salir(self, e):
        pass

    def marcar(self, activo):
        if activo:
            self.c_top = "#1fa2ff"
            self.c_bot = "#1262ab"
            self.color_texto = "white"
        else:
            self.c_top = "#ffffff"
            self.c_bot = "#dcebf5"
            self.color_texto = TEXTO_DARK
        self.redibujar()

class CanalAero(BotonAero):
    def __init__(self, padre, texto, subtitulo, comando, c_top, c_bot):
        super().__init__(padre, texto, comando, c_top=c_top, c_bot=c_bot, color_texto="white",
                         alto=125, radio=24, tamano=12, subtitulo=subtitulo)

class GrupoChips(tk.Frame):
    def __init__(self, padre, opciones, variable, al_cambiar=None, columnas=0):
        super().__init__(padre, bg="#e8f4fc")
        self.variable = variable
        self.al_cambiar = al_cambiar
        self.chips = {}
        if columnas == 0:
            columnas = len(opciones)

        posicion = 0
        for opcion in opciones:
            chip = BotonAero(self, opcion, lambda opcion=opcion: self.elegir(opcion), alto=36, radio=18, tamano=9, es_chip=True)
            chip.grid(row=posicion // columnas, column=posicion % columnas, sticky="ew", padx=3, pady=3)
            self.chips[opcion] = chip
            posicion = posicion + 1
        for columna in range(columnas):
            self.columnconfigure(columna, weight=1)
        self.actualizar()

    def elegir(self, opcion):
        self.variable.set(opcion)
        self.actualizar()
        if self.al_cambiar is not None:
            self.al_cambiar()

    def actualizar(self):
        for opcion in self.chips:
            self.chips[opcion].marcar(opcion == self.variable.get())

class Entrada(tk.Entry):
    def __init__(self, padre, variable, ancho=20):
        super().__init__(padre, textvariable=variable, width=ancho, bg="white", fg=TEXTO_DARK, relief="flat",
                         font=(FUENTE, 11), highlightthickness=2, highlightbackground="#a8d3f0",
                         highlightcolor="#1fa2ff", insertbackground=TEXTO_DARK)

class TarjetaSaldo(tk.Canvas):
    def __init__(self, padre):
        super().__init__(padre, height=155, bg="#e8f4fc", highlightthickness=0)
        self.saldo = 0
        self.bind("<Configure>", self.redibujar)

    def mostrar_saldo(self, saldo):
        self.saldo = saldo
        self.redibujar()

    def redibujar(self, evento=None):
        self.delete("all")
        ancho = self.winfo_width()
        if ancho < 10:
            return

        if self.saldo < 0:
            c_top, c_bot = "#ff6b6b", "#c0392b"
        else:
            c_top, c_bot = "#56ccf2", "#2f80ed"

        self.create_polygon(puntos_redondeados(2, 5, ancho - 2, 152, 28), smooth=True, fill="#aed2eb", outline="")

        for i in range(12):
            y1 = 1 + (i * 146 / 12)
            factor = i / 11
            color_paso = self.interpolar(c_top, c_bot, factor)
            self.create_polygon(puntos_redondeados(2, 1, ancho - 2, 147, 28), smooth=True, fill=color_paso, outline="")

        self.create_polygon(puntos_redondeados(2, 1, ancho - 2, 147, 28), smooth=True, fill="", outline="#ffffff", width=2)
        self.create_polygon(puntos_redondeados(6, 4, ancho - 6, 68, 22), smooth=True, fill="#ffffff", outline="", stipple="gray25")

        self.create_text(ancho / 2 + 1, 38, text="Saldo disponible", fill="#07304d", font=(FUENTE, 11, "bold"))
        self.create_text(ancho / 2, 37, text="Saldo disponible", fill="#ffffff", font=(FUENTE, 11, "bold"))

        self.create_text(ancho / 2 + 2, 84, text=dinero(self.saldo), fill="#07304d", font=(FUENTE, 30, "bold"))
        self.create_text(ancho / 2, 82, text=dinero(self.saldo), fill="#ffffff", font=(FUENTE, 30, "bold"))

        if self.saldo < 0:
            self.create_text(ancho / 2, 126, text="Gastaste más de lo que registraste como ingreso.",
                             fill="#fff0f0", font=(FUENTE, 9), width=ancho - 40)

    def interpolar(self, c1, c2, f):
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        return f"#{int(r1+(r2-r1)*f):02x}{int(g1+(g2-g1)*f):02x}{int(b1+(b2-b1)*f):02x}"

class BarraMes(tk.Canvas):
    def __init__(self, padre):
        super().__init__(padre, height=76, bg="#e8f4fc", highlightthickness=0)
        self.ingresos = 0
        self.gastos = 0
        self.bind("<Configure>", self.redibujar)

    def mostrar(self, ingresos, gastos):
        self.ingresos = ingresos
        self.gastos = gastos
        self.redibujar()

    def redibujar(self, evento=None):
        self.delete("all")
        ancho = self.winfo_width()
        if ancho < 10:
            return
        self.create_polygon(puntos_redondeados(2, 2, ancho - 2, 74, 30), smooth=True, fill="#ffffff", outline="#bce0fd", width=2)
        self.create_line(ancho / 2, 16, ancho / 2, 60, fill="#d0e5f5", width=2)
        self.create_text(ancho * 0.25, 24, text="Ingresos del mes", fill=GRIS_TEXTO, font=(FUENTE, 9))
        self.create_text(ancho * 0.25, 48, text=dinero(self.ingresos), fill="#109648", font=(FUENTE, 14, "bold"))
        self.create_text(ancho * 0.75, 24, text="Gastos del mes", fill=GRIS_TEXTO, font=(FUENTE, 9))
        self.create_text(ancho * 0.75, 48, text=dinero(self.gastos), fill="#d63031", font=(FUENTE, 14, "bold"))

class Pantalla(tk.Frame):
    def __init__(self, app):
        super().__init__(app.contenedor, bg="#e8f4fc")
        self.app = app
        self.gestor = app.gestor

    def actualizar(self):
        pass

    def poner_titulo(self, texto):
        etiqueta = tk.Label(self, text=texto, bg="#e8f4fc", fg=TEXTO_DARK, font=(FUENTE, 20, "bold"))
        etiqueta.pack(anchor="w", padx=MARGEN, pady=(24, 12))
        return etiqueta

    def poner_subtitulo(self, texto):
        tk.Label(self, text=texto, bg="#e8f4fc", fg=GRIS_TEXTO, font=(FUENTE, 10, "bold")).pack(anchor="w", padx=MARGEN, pady=(14, 4))

    def poner_boton_volver(self):
        BotonAero(self, "Volver", self.app.ir_al_inicio, c_top="#ffffff", c_bot="#dcebf5", color_texto=TEXTO_DARK,
                  alto=42).pack(side="bottom", fill="x", padx=MARGEN, pady=(0, 20))

    def poner_filtro_periodo(self):
        filtro = GrupoChips(self, PERIODOS, self.app.periodo, self.actualizar)
        filtro.pack(fill="x", padx=MARGEN - 3, pady=(0, 10))

class PantallaInicio(Pantalla):
    def __init__(self, app):
        super().__init__(app)
        self.poner_titulo("Control de Finanzas")

        self.barra = BarraMes(self)
        self.barra.pack(side="bottom", fill="x", padx=MARGEN, pady=(0, 24))

        self.tarjeta = TarjetaSaldo(self)
        self.tarjeta.pack(fill="x", padx=MARGEN, pady=(0, 14))

        fichas = tk.Frame(self, bg="#e8f4fc")
        fichas.pack(fill="both", expand=True, padx=MARGEN - 6, pady=(0, 14))
        for numero in range(2):
            fichas.columnconfigure(numero, weight=1)
            fichas.rowconfigure(numero, weight=1)

        CanalAero(fichas, "Nuevo Ingreso", "Plata que entra", self.nuevo_ingreso, AERO_GREEN_TOP, AERO_GREEN_BOTTOM).grid(
            row=0, column=0, sticky="nsew", padx=6, pady=6)
        CanalAero(fichas, "Nuevo Gasto", "Plata que sale", self.nuevo_gasto, AERO_ROJO_TOP, AERO_ROJO_BOTTOM).grid(
            row=0, column=1, sticky="nsew", padx=6, pady=6)
        CanalAero(fichas, "Movimientos", "Lo registrado", self.app.ir_al_historial, AERO_BLUE_TOP, AERO_BLUE_BOTTOM).grid(
            row=1, column=0, sticky="nsew", padx=6, pady=6)
        CanalAero(fichas, "Resumen", "Tus estadísticas", self.app.ir_a_estadisticas, AERO_BLUE_TOP, AERO_BLUE_BOTTOM).grid(
            row=1, column=1, sticky="nsew", padx=6, pady=6)

    def nuevo_ingreso(self):
        self.app.abrir_formulario("Ingreso", None, "inicio")

    def nuevo_gasto(self):
        self.app.abrir_formulario("Gasto", None, "inicio")

    def actualizar(self):
        self.tarjeta.mostrar_saldo(self.gestor.calcular_saldo())
        ingresos, gastos = self.gestor.calcular_totales(self.gestor.filtrar("Mes"))
        self.barra.mostrar(ingresos, gastos)

class PantallaFormulario(Pantalla):
    def __init__(self, app):
        super().__init__(app)
        self.transaccion = None
        self.origen = "inicio"
        self.tipo = tk.StringVar(value="Gasto")
        self.categoria = tk.StringVar()
        self.monto = tk.StringVar()
        self.descripcion = tk.StringVar()
        self.fecha = tk.StringVar()
        self.hora = tk.StringVar()

        self.titulo = self.poner_titulo("Nuevo movimiento")
        self.grupo_tipo = GrupoChips(self, ("Ingreso", "Gasto"), self.tipo)
        self.grupo_tipo.pack(fill="x", padx=MARGEN - 3)

        self.poner_subtitulo("Categoría")
        self.poner_campo(self.categoria)
        self.grupo_categoria = GrupoChips(self, CATEGORIAS, self.categoria, columnas=4)
        self.grupo_categoria.pack(fill="x", padx=MARGEN - 3, pady=(6, 0))

        self.poner_subtitulo("Valor")
        self.poner_campo(self.monto)
        self.poner_subtitulo("Descripción (opcional)")
        self.poner_campo(self.descripcion)

        self.poner_subtitulo("Fecha y hora")
        fila = tk.Frame(self, bg="#e8f4fc")
        fila.pack(fill="x", padx=MARGEN)
        Entrada(fila, self.fecha, ancho=12).pack(side="left", ipady=5)
        Entrada(fila, self.hora, ancho=7).pack(side="left", ipady=5, padx=8)
        BotonAero(fila, "Ahora", self.poner_fecha_actual, c_top="#ffffff", c_bot="#dcebf5",
                  color_texto=TEXTO_DARK, ancho=75, alto=34).pack(side="left")

        BotonAero(self, "Guardar", self.guardar, c_top=AERO_BLUE_TOP, c_bot=AERO_BLUE_BOTTOM, alto=46).pack(fill="x", padx=MARGEN, pady=(24, 8))
        BotonAero(self, "Cancelar", self.cancelar, c_top="#ffffff", c_bot="#dcebf5", color_texto=TEXTO_DARK, alto=42).pack(fill="x", padx=MARGEN)

    def poner_campo(self, variable):
        entrada = Entrada(self, variable)
        entrada.pack(fill="x", padx=MARGEN, ipady=6)
        entrada.bind("<Return>", lambda e: self.guardar())

    def poner_fecha_actual(self):
        ahora = datetime.now()
        self.fecha.set(ahora.strftime(FORMATO_FECHA))
        self.hora.set(ahora.strftime(FORMATO_HORA))

    def preparar(self, tipo, transaccion, origen):
        self.transaccion = transaccion
        self.origen = origen
        if transaccion is None:
            self.titulo.configure(text="Nuevo movimiento")
            self.tipo.set(tipo)
            self.categoria.set("")
            self.monto.set("")
            self.descripcion.set("")
            self.poner_fecha_actual()
        else:
            self.titulo.configure(text="Editar movimiento")
            self.tipo.set(transaccion.tipo.capitalize())
            self.categoria.set(transaccion.categoria)
            self.monto.set(str(transaccion.monto))
            self.descripcion.set(transaccion.descripcion)
            self.fecha.set(transaccion.fecha.strftime(FORMATO_FECHA))
            self.hora.set(transaccion.fecha.strftime(FORMATO_HORA))
        self.grupo_tipo.actualizar()
        self.grupo_categoria.actualizar()

    def guardar(self):
        tipo = self.tipo.get().lower()
        try:
            if self.transaccion is None:
                self.gestor.agregar(tipo, self.categoria.get(), self.monto.get(),
                                    self.descripcion.get(), self.fecha.get(), self.hora.get())
            else:
                self.gestor.editar(self.transaccion.id, tipo, self.categoria.get(), self.monto.get(),
                                   self.descripcion.get(), self.fecha.get(), self.hora.get())
        except ValueError as error:
            messagebox.showwarning("Revisa los datos", str(error), parent=self.app)
            return
        self.app.mostrar(self.origen)

    def cancelar(self):
        self.app.mostrar(self.origen)

class PantallaHistorial(Pantalla):
    def __init__(self, app):
        super().__init__(app)
        self.poner_boton_volver()
        botones = tk.Frame(self, bg="#e8f4fc")
        botones.pack(side="bottom", fill="x", padx=MARGEN, pady=(6, 10))

        BotonAero(botones, "Editar", self.editar, c_top="#ffffff", c_bot="#dcebf5", color_texto=TEXTO_DARK, alto=38).pack(side="left", expand=True, fill="x", padx=(0, 4))
        BotonAero(botones, "Eliminar", self.eliminar, c_top="#ffffff", c_bot="#dcebf5", color_texto=TEXTO_DARK, alto=38).pack(side="left", expand=True, fill="x", padx=(4, 0))

        self.lbl_detalle = tk.Label(self, bg="#e8f4fc", fg=GRIS_TEXTO, font=(FUENTE, 9), anchor="w", justify="left", wraplength=420)
        self.lbl_detalle.pack(side="bottom", fill="x", padx=MARGEN)

        self.poner_titulo("Movimientos")
        self.poner_filtro_periodo()
        self.lbl_resumen = tk.Label(self, bg="#e8f4fc", fg=GRIS_TEXTO, font=(FUENTE, 9), anchor="w", justify="left", wraplength=440)
        self.lbl_resumen.pack(fill="x", padx=MARGEN, pady=(0, 8))

        marco = tk.Frame(self, bg="#e8f4fc")
        marco.pack(fill="both", expand=True, padx=MARGEN)
        self.tabla = ttk.Treeview(marco, columns=("categoria", "fecha", "valor"), show="headings", selectmode="browse")
        self.tabla.heading("categoria", text="Categoría")
        self.tabla.heading("fecha", text="Fecha")
        self.tabla.heading("valor", text="Valor")
        self.tabla.column("categoria", width=120, anchor="w")
        self.tabla.column("fecha", width=130, anchor="w")
        self.tabla.column("valor", width=110, anchor="e")

        self.tabla.tag_configure("ingreso", foreground="#109648")
        self.tabla.tag_configure("gasto", foreground="#d63031")
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="left", fill="y")
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

    def actualizar(self):
        lista = self.gestor.filtrar(self.app.periodo.get())
        ingresos, gastos = self.gestor.calcular_totales(lista)
        self.lbl_resumen.configure(text="Ingresos: " + dinero(ingresos) + "  |  Gastos: " + dinero(gastos)
                                   + "  |  Dif: " + dinero(ingresos - gastos))
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for t in lista:
            valor = ("+" if t.tipo == "ingreso" else "-") + dinero(t.monto)
            self.tabla.insert("", "end", iid=str(t.id), tags=(t.tipo,),
                              values=("✦ " + t.categoria, t.fecha.strftime("%d/%m/%Y %H:%M"), valor))
        if len(lista) > 0:
            self.lbl_detalle.configure(text="Selecciona un movimiento para ver más detalles.")
        else:
            self.lbl_detalle.configure(text="No hay movimientos registrados.")

    def obtener_seleccionada(self):
        seleccion = self.tabla.selection()
        if len(seleccion) == 0:
            return None
        return self.gestor.transacciones.get(int(seleccion[0]))

    def al_seleccionar(self, evento):
        t = self.obtener_seleccionada()
        if t is not None:
            txt = "Descripción: " + (t.descripcion if t.descripcion != "" else "(sin descripción)")
            self.lbl_detalle.configure(text=txt)

    def editar(self):
        t = self.obtener_seleccionada()
        if t is None:
            messagebox.showinfo("Atención", "Selecciona un movimiento primero.", parent=self.app)
            return
        self.app.abrir_formulario(t.tipo.capitalize(), t, "historial")

    def eliminar(self):
        t = self.obtener_seleccionada()
        if t is None:
            messagebox.showinfo("Atención", "Selecciona un movimiento primero.", parent=self.app)
            return
        if messagebox.askyesno("Eliminar", "¿Eliminar " + t.categoria + " por " + dinero(t.monto) + "?", parent=self.app):
            self.gestor.eliminar(t.id)
            self.actualizar()

class PantallaEstadisticas(Pantalla):
    def __init__(self, app):
        super().__init__(app)
        self.poner_boton_volver()
        self.agrupar = tk.StringVar(value="Semana")

        self.poner_titulo("Resumen")
        self.poner_filtro_periodo()
        self.lbl_mayor = tk.Label(self, bg="#e8f4fc", fg=TEXTO_DARK, font=(FUENTE, 12, "bold"), anchor="w")
        self.lbl_mayor.pack(fill="x", padx=MARGEN, pady=(2, 6))
        self.zona_categorias = tk.Frame(self, bg="#e8f4fc")
        self.zona_categorias.pack(fill="x", padx=MARGEN)

        fila = tk.Frame(self, bg="#e8f4fc")
        fila.pack(fill="x", padx=MARGEN - 3, pady=(18, 4))
        tk.Label(fila, text="Ver por", bg="#e8f4fc", fg=GRIS_TEXTO, font=(FUENTE, 10, "bold")).pack(side="left", padx=3)
        GrupoChips(fila, ("Semana", "Mes"), self.agrupar, self.actualizar).pack(side="left", padx=6)
        self.zona_resumen = tk.Frame(self, bg="#e8f4fc")
        self.zona_resumen.pack(fill="both", expand=True, padx=MARGEN)

    def borrar_contenido(self, zona):
        for widget in zona.winfo_children():
            widget.destroy()

    def actualizar(self):
        lista = self.gestor.filtrar(self.app.periodo.get())
        ingresos, gastos = self.gestor.calcular_totales(lista)
        self.borrar_contenido(self.zona_categorias)
        self.borrar_contenido(self.zona_resumen)

        por_categoria = self.gestor.gastos_por_categoria(lista)
        if len(por_categoria) == 0:
            self.lbl_mayor.configure(text="No hay gastos en este periodo.")
        else:
            nombre = por_categoria[0][0]
            porcentaje = round(por_categoria[0][1] * 100 / gastos) if gastos > 0 else 0
            self.lbl_mayor.configure(text="Mayor gasto: " + nombre + " (" + str(porcentaje) + "%)")
        for categoria, total in por_categoria[:6]:
            porcentaje_cat = (total * 100 / gastos) if gastos > 0 else 0
            self.poner_fila_categoria(categoria, total, porcentaje_cat)

        filas = self.gestor.resumen_por_semana_o_mes(lista, self.agrupar.get())
        for nombre, ing, gas in filas[:6]:
            diferencia = ing - gas
            color = "#109648" if diferencia >= 0 else "#d63031"
            fila = tk.Frame(self.zona_resumen, bg="#e8f4fc")
            fila.pack(fill="x", pady=(6, 0))
            tk.Label(fila, text=nombre, bg="#e8f4fc", fg=TEXTO_DARK, font=(FUENTE, 10, "bold")).pack(side="left")
            tk.Label(fila, text=dinero(diferencia), bg="#e8f4fc", fg=color, font=(FUENTE, 10, "bold")).pack(side="right")
            tk.Label(self.zona_resumen, text="Ingresos " + dinero(ing) + "  ·  Gastos " + dinero(gas),
                     bg="#e8f4fc", fg=GRIS_TEXTO, font=(FUENTE, 8), anchor="w").pack(fill="x")

    def poner_fila_categoria(self, nombre, total, porcentaje):
        fila = tk.Frame(self.zona_categorias, bg="#e8f4fc")
        fila.pack(fill="x", pady=3)
        tk.Label(fila, text=nombre, width=11, anchor="w", bg="#e8f4fc", fg=TEXTO_DARK, font=(FUENTE, 10)).pack(side="left")
        fondo_barra = tk.Frame(fila, bg="#cbe3f5", width=140, height=12)
        fondo_barra.pack(side="left")
        fondo_barra.pack_propagate(False)
        ancho_barra = max(4, int(140 * porcentaje / 100))
        tk.Frame(fondo_barra, bg="#d63031").place(x=0, y=0, width=ancho_barra, height=12)
        tk.Label(fila, text=dinero(total) + "  " + str(round(porcentaje)) + "%", bg="#e8f4fc", fg=GRIS_TEXTO, font=(FUENTE, 9)).pack(side="right")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Control de Finanzas - Frutiger Aero Edition")
        self.geometry("520x800")
        self.minsize(480, 740)
        self.configure(bg="#bce0fd")
        self.gestor = GestorFinanzas()
        self.periodo = tk.StringVar(value="Todo")
        self.configurar_tabla()

        self.contenedor = tk.Frame(self, bg="#e8f4fc", highlightbackground="#ffffff", highlightthickness=3)
        self.contenedor.pack(fill="both", expand=True, padx=16, pady=16)

        self.pantallas = {
            "inicio": PantallaInicio(self),
            "formulario": PantallaFormulario(self),
            "historial": PantallaHistorial(self),
            "estadisticas": PantallaEstadisticas(self),
        }
        for nombre in self.pantallas:
            self.pantallas[nombre].place(relx=0, rely=0, relwidth=1, relheight=1)
        self.mostrar("inicio")

        if len(self.gestor.avisos) > 0:
            self.after(300, self.mostrar_avisos)

    def mostrar_avisos(self):
        messagebox.showwarning("Aviso al abrir", "\n".join(self.gestor.avisos), parent=self)

    def mostrar(self, nombre):
        pantalla = self.pantallas[nombre]
        pantalla.actualizar()
        pantalla.tkraise()

    def ir_al_inicio(self):
        self.mostrar("inicio")

    def ir_al_historial(self):
        self.mostrar("historial")

    def ir_a_estadisticas(self):
        self.mostrar("estadisticas")

    def abrir_formulario(self, tipo, transaccion, origen):
        self.pantallas["formulario"].preparar(tipo, transaccion, origen)
        self.mostrar("formulario")

    def configurar_tabla(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("Treeview", rowheight=32, font=(FUENTE, 10), borderwidth=0, background="#ffffff", fieldbackground="#ffffff")
        estilo.configure("Treeview.Heading", font=(FUENTE, 9, "bold"), background="#d8ecfa", foreground=TEXTO_DARK, relief="flat")
        estilo.map("Treeview.Heading", background=[("active", "#c3e2f9")])
        estilo.map("Treeview", background=[("selected", "#1fa2ff")], foreground=[("selected", "#ffffff")])

if __name__ == "__main__":
    App().mainloop()
