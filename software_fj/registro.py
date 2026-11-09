"""
registro.py
-----------
Configura el archivo de logs del sistema.

Todos los módulos piden su logger con obtener_logger(); así, cada evento
y cada error queda escrito en logs/software_fj.log con fecha, nivel y módulo.
"""

import logging          # Módulo estándar de Python para registrar eventos
from pathlib import Path  # Para construir rutas de carpetas sin depender del sistema operativo

# Carpeta "logs" ubicada en la raíz del proyecto (un nivel arriba de este paquete)
CARPETA_LOGS = Path(__file__).resolve().parent.parent / "logs"
# Ruta completa del archivo de logs
ARCHIVO_LOG = CARPETA_LOGS / "software_fj.log"

# Bandera para no configurar el logging dos veces
_configurado = False


def configurar_registro(reiniciar=False):
    """Prepara el archivo de logs. Si reiniciar=True, lo vacía al empezar."""
    global _configurado  # Vamos a modificar la bandera global
    if _configurado:  # Si ya se configuró antes, no hacemos nada
        return
    try:
        # Creamos la carpeta de logs si no existe (exist_ok evita error si ya está)
        CARPETA_LOGS.mkdir(parents=True, exist_ok=True)
        # "w" vacía el archivo al iniciar; "a" agrega al final
        modo = "w" if reiniciar else "a"
        # Manejador que escribe en el archivo con codificación UTF-8 (tildes y ñ)
        manejador = logging.FileHandler(ARCHIVO_LOG, mode=modo, encoding="utf-8")
    except OSError as error:
        # Si no se puede escribir el archivo (permisos, disco lleno), seguimos solo en consola
        manejador = logging.StreamHandler()
        print(f"Aviso: no se pudo abrir el archivo de logs ({error}); se usará la consola.")
    # Formato de cada línea: fecha | nivel | módulo | mensaje
    formato = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)-22s | %(message)s",
                                datefmt="%Y-%m-%d %H:%M:%S")
    manejador.setFormatter(formato)  # Aplicamos el formato al manejador
    raiz = logging.getLogger("software_fj")  # Logger principal del proyecto
    raiz.setLevel(logging.DEBUG)  # Registramos desde DEBUG en adelante
    raiz.addHandler(manejador)  # Conectamos el manejador al logger
    _configurado = True  # Marcamos que ya quedó configurado


def obtener_logger(nombre):
    """Devuelve un logger hijo, por ejemplo 'software_fj.cliente'.
    El archivo se configura una sola vez con configurar_registro()."""
    return logging.getLogger(f"software_fj.{nombre}")  # Logger con el nombre del módulo
