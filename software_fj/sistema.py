"""
sistema.py
----------
SistemaGestion: el "cerebro" de Software FJ. Guarda todo en listas internas
(sin base de datos) y ofrece las operaciones del negocio.

El método ejecutar() es la red de seguridad: corre cualquier operación,
atrapa todos sus errores, los registra en el log y deja que el programa
siga funcionando.
"""

from .cliente import Cliente                     # Clase Cliente
from .excepciones import (                       # Excepciones propias
    ClienteInvalidoError,
    DatoInvalidoError,
    ParametroFaltanteError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)
from .registro import configurar_registro, obtener_logger  # Configuración y logger del módulo
from .reserva import PROCESADA, Reserva          # Clase Reserva y estado PROCESADA
from .servicios import AlquilerEquipo, AsesoriaEspecializada, ReservaSala, formato_pesos

log = obtener_logger("sistema")  # Logger para este archivo

# Tipos de servicio que el sistema sabe crear (nombre corto -> clase)
TIPOS_SERVICIO = {
    "sala": ReservaSala,
    "equipo": AlquilerEquipo,
    "asesoria": AsesoriaEspecializada,
}


class SistemaGestion:
    """Gestiona clientes, servicios y reservas de Software FJ en memoria."""

    def __init__(self):
        configurar_registro()   # Garantiza que exista el archivo de logs
        self._clientes = []     # Lista interna de clientes
        self._servicios = []    # Lista interna de servicios
        self._reservas = []     # Lista interna de reservas
        self._exitosas = 0      # Operaciones que salieron bien
        self._fallidas = 0      # Operaciones que fallaron (controladas)
        log.info("=== Sistema Software FJ iniciado ===")

    # ------------------------------------------------------------------
    # Red de seguridad: ninguna operación puede tumbar el programa
    # ------------------------------------------------------------------

    def ejecutar(self, numero, descripcion, operacion, *args, **kwargs):
        """Corre operacion(*args, **kwargs) de forma segura y muestra el resultado."""
        print(f"\n[{numero:02d}] {descripcion}")  # Encabezado de la operación
        resultado = None  # Valor por defecto si algo falla
        try:
            resultado = operacion(*args, **kwargs)  # Intentamos la operación
        except SoftwareFJError as error:
            # Error de negocio esperado: se registra y se informa
            self._fallidas += 1
            causa = f" | causa: {type(error.__cause__).__name__}: {error.__cause__}" if error.__cause__ else ""
            log.error("Op %02d '%s' falló: %s%s", numero, descripcion, error, causa)
            print(f"   ✘ {type(error).__name__}: {error}")
            if error.__cause__:  # Mostramos el error original encadenado
                print(f"     ↳ causado por {type(error.__cause__).__name__}: {error.__cause__}")
        except Exception as error:  # noqa: BLE001 - red de seguridad a propósito
            # Error inesperado de Python: se guarda con todo el detalle (traceback)
            self._fallidas += 1
            log.critical("Op %02d '%s': error inesperado", numero, descripcion, exc_info=True)
            print(f"   ✘ Error inesperado ({type(error).__name__}: {error}). El sistema sigue activo.")
        else:
            # Sin errores
            self._exitosas += 1
            log.info("Op %02d '%s' completada", numero, descripcion)
            if resultado is not None:  # Mostramos lo que devolvió la operación
                print(f"   ✔ {resultado}")
            else:
                print("   ✔ Operación completada")
        finally:
            # Siempre se ejecuta: dejamos constancia de que la operación terminó
            log.debug("Op %02d finalizada (exitosas=%d, fallidas=%d)", numero, self._exitosas, self._fallidas)
        return resultado

    # ------------------------------------------------------------------
    # Clientes
    # ------------------------------------------------------------------

    def registrar_cliente(self, **datos):
        """Crea un cliente y lo guarda. No permite documentos repetidos."""
        documento = str(datos.get("documento", "")).strip()  # Documento recibido
        if any(c.documento == documento for c in self._clientes):  # ¿Ya existe?
            raise ClienteInvalidoError(f"Ya existe un cliente con el documento terminado en {documento[-4:]}")
        try:
            cliente = Cliente(**datos)  # Puede lanzar DatoInvalidoError o ParametroFaltanteError
        except (DatoInvalidoError, ParametroFaltanteError) as error:
            # Encadenamos: el error de dato queda como causa del error de cliente
            raise ClienteInvalidoError("No se pudo registrar el cliente") from error
        except TypeError as error:
            # Se envió un campo que Cliente no conoce (ej. "edad")
            raise ClienteInvalidoError("Se enviaron campos desconocidos para el cliente") from error
        self._clientes.append(cliente)  # Lo guardamos en la lista
        return cliente

    def buscar_cliente(self, documento):
        """Devuelve el cliente con ese documento o lanza ClienteInvalidoError."""
        for cliente in self._clientes:  # Recorremos la lista
            if cliente.documento == str(documento):
                return cliente
        raise ClienteInvalidoError(f"No hay ningún cliente registrado con el documento {documento}")

    # ------------------------------------------------------------------
    # Servicios
    # ------------------------------------------------------------------

    def crear_servicio(self, tipo, **datos):
        """Crea un servicio del tipo indicado ('sala', 'equipo' o 'asesoria')."""
        try:
            clase = TIPOS_SERVICIO[tipo]  # KeyError si el tipo no existe
        except KeyError as error:
            raise ServicioInvalidoError(
                f"El tipo de servicio '{tipo}' no existe. Opciones: {', '.join(TIPOS_SERVICIO)}"
            ) from error
        try:
            servicio = clase(**datos)  # Cada clase valida sus propios datos
        except ParametroFaltanteError as error:
            raise ServicioInvalidoError(f"No se pudo crear el servicio '{tipo}'") from error
        except TypeError as error:
            raise ServicioInvalidoError(f"Datos desconocidos para el servicio '{tipo}'") from error
        self._servicios.append(servicio)  # Lo guardamos en la lista
        return servicio

    def buscar_servicio(self, servicio_id):
        """Devuelve el servicio con ese ID o lanza ServicioInvalidoError."""
        for servicio in self._servicios:  # Recorremos la lista
            if servicio.id == servicio_id:
                return servicio
        raise ServicioInvalidoError(f"No existe el servicio {servicio_id}")

    # ------------------------------------------------------------------
    # Reservas
    # ------------------------------------------------------------------

    def crear_reserva(self, documento, servicio_id, duracion, **detalles):
        """Crea una reserva PENDIENTE para un cliente y un servicio registrados."""
        cliente = self.buscar_cliente(documento)          # Puede fallar si no existe
        servicio = self.buscar_servicio(servicio_id)      # Puede fallar si no existe
        reserva = Reserva(cliente, servicio, duracion, **detalles)  # Valida duración y detalles
        self._reservas.append(reserva)                    # La guardamos en la lista
        return reserva

    def reservar(self, documento, servicio_id, duracion, **detalles):
        """Crea la reserva y la confirma en un paso.
        Si el servicio no está disponible, la reserva queda CANCELADA y el error sube."""
        reserva = self.crear_reserva(documento, servicio_id, duracion, **detalles)  # Queda PENDIENTE
        try:
            reserva.confirmar()  # Intentamos apartar el servicio
        except ServicioNoDisponibleError:
            reserva.cancelar("rechazada: servicio no disponible")  # No dejamos reservas colgadas
            raise  # El que llamó se entera del error original
        return reserva

    # ------------------------------------------------------------------
    # Reporte final
    # ------------------------------------------------------------------

    def reporte(self):
        """Imprime el estado completo del sistema."""
        linea = "=" * 78  # Separador visual
        print(f"\n{linea}\nREPORTE FINAL - SOFTWARE FJ\n{linea}")
        print(f"\nClientes registrados ({len(self._clientes)}):")
        for c in self._clientes:  # Polimorfismo: cada objeto usa su propio describir()
            print("  -", c)
        print(f"\nServicios ({len(self._servicios)}):")
        for s in self._servicios:
            print("  -", s)
        print(f"\nReservas ({len(self._reservas)}):")
        for r in self._reservas:
            print("  -", r)
        # Sumamos solo las reservas procesadas (las que realmente se cobraron)
        ingresos = sum(r.costo_total for r in self._reservas if r.estado == PROCESADA)
        print(f"\nIngresos procesados: {formato_pesos(ingresos)}")
        print(f"Operaciones exitosas: {self._exitosas} | fallidas y controladas: {self._fallidas}")
        print(linea)
        log.info("Reporte: %d clientes, %d servicios, %d reservas, ingresos %s",
                 len(self._clientes), len(self._servicios), len(self._reservas), formato_pesos(ingresos))
