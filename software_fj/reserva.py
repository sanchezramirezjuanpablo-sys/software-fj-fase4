"""
reserva.py
----------
Clase Reserva: une un cliente, un servicio y una duración, y controla
su ciclo de vida con estados:

    PENDIENTE --confirmar()--> CONFIRMADA --procesar()--> PROCESADA
        |                          |
        +------cancelar()----------+--> CANCELADA

Aquí se usan las tres variantes de bloques de excepciones que pide la guía:
    try/except/else     -> confirmar()
    try/except/finally  -> cancelar()
    try/except/else/finally + encadenamiento (raise ... from ...) -> procesar()
"""

from .cliente import Cliente                     # Para comprobar el tipo del cliente
from .entidad import EntidadBase                 # Clase abstracta padre
from .excepciones import (                       # Excepciones propias
    CalculoInconsistenteError,
    DatoInvalidoError,
    OperacionNoPermitidaError,
    ReservaInvalidaError,
    ServicioNoDisponibleError,
)
from .registro import obtener_logger             # Logger del módulo
from .servicios import IVA, Servicio, formato_pesos  # Clase Servicio, IVA y formato de pesos

log = obtener_logger("reserva")  # Logger para este archivo

# Estados posibles de una reserva
PENDIENTE = "PENDIENTE"
CONFIRMADA = "CONFIRMADA"
PROCESADA = "PROCESADA"
CANCELADA = "CANCELADA"


class Reserva(EntidadBase):
    """Reserva de un servicio hecha por un cliente."""

    PREFIJO = "RES"  # Los IDs de reservas serán RES-0001, RES-0002...

    def __init__(self, cliente, servicio, duracion, **detalles):
        # El cliente debe ser un objeto Cliente de verdad
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError(f"El cliente {cliente!r} no es válido")
        # El servicio debe ser cualquier subclase de Servicio (polimorfismo)
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError(f"El servicio {servicio!r} no es válido")
        try:
            duracion = float(duracion)  # Aceptamos "3" o 3, pero no "tres"
        except (TypeError, ValueError) as error:
            # Encadenamiento: guardamos el error original de Python como causa
            raise ReservaInvalidaError(f"La duración {duracion!r} no es un número") from error
        try:
            servicio.validar_parametros(duracion, **detalles)  # Cada servicio valida a su manera
        except DatoInvalidoError as error:
            # Convertimos el error de dato en un error de reserva, conservando la causa
            raise ReservaInvalidaError(f"Los datos de la reserva no sirven para {servicio.nombre}") from error
        super().__init__()                # Asigna ID y fecha de creación
        self._cliente = cliente           # Quién reserva
        self._servicio = servicio         # Qué reserva
        self._duracion = duracion         # Cuánto tiempo
        self._detalles = detalles         # Datos extra: personas, cantidad...
        self._estado = PENDIENTE          # Toda reserva empieza pendiente
        self._costo_total = None          # Se conoce al procesar
        log.info("Reserva %s creada: %s -> %s (%s %s)", self.id, cliente.nombre,
                 servicio.nombre, duracion, servicio.UNIDAD)

    # ------------------------------------------------------------------
    # Propiedades de solo lectura
    # ------------------------------------------------------------------

    @property
    def cliente(self):
        return self._cliente  # Cliente de la reserva

    @property
    def servicio(self):
        return self._servicio  # Servicio reservado

    @property
    def estado(self):
        return self._estado  # Estado actual

    @property
    def costo_total(self):
        return self._costo_total  # None hasta que se procese

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def confirmar(self):
        """Aparta el servicio. Usa try/except/else."""
        if self._estado != PENDIENTE:  # Solo se confirma lo que está pendiente
            raise OperacionNoPermitidaError("confirmar", self._estado)
        try:
            self._servicio.ocupar(**self._detalles)  # Puede lanzar ServicioNoDisponibleError
        except ServicioNoDisponibleError:
            # Registramos el fallo y dejamos que el error siga hacia arriba
            log.error("Reserva %s no se pudo confirmar: servicio no disponible", self.id)
            raise
        else:
            # El bloque else solo corre si NO hubo excepción
            self._estado = CONFIRMADA
            log.info("Reserva %s CONFIRMADA", self.id)
        return self  # Permite encadenar: reserva.confirmar().procesar()

    def cancelar(self, motivo="sin motivo"):
        """Cancela la reserva y libera el servicio. Usa try/except/finally."""
        estado_anterior = self._estado  # Lo guardamos para el log
        try:
            if self._estado in (PROCESADA, CANCELADA):  # Ya no se puede cancelar
                raise OperacionNoPermitidaError("cancelar", self._estado)
            if self._estado == CONFIRMADA:  # Si estaba confirmada, devolvemos lo apartado
                self._servicio.liberar(**self._detalles)
            self._estado = CANCELADA  # Nuevo estado
            log.info("Reserva %s CANCELADA (%s)", self.id, motivo)
        except OperacionNoPermitidaError:
            log.error("Intento de cancelar %s en estado %s", self.id, self._estado)
            raise  # Avisamos al que llamó
        finally:
            # finally corre SIEMPRE, haya error o no: dejamos rastro del intento
            log.debug("Intento de cancelación de %s: %s -> %s", self.id, estado_anterior, self._estado)
        return self

    def procesar(self, impuesto=IVA, descuento=None):
        """
        Calcula el costo final y cierra la reserva.
        Usa try/except/else/finally y encadenamiento de excepciones.
        """
        if self._estado != CONFIRMADA:  # Solo se procesa lo confirmado
            raise OperacionNoPermitidaError("procesar", self._estado)
        try:
            costo = self._servicio.calcular_costo(  # Polimorfismo: cada servicio calcula distinto
                self._duracion, impuesto=impuesto, descuento=descuento, **self._detalles
            )
        except CalculoInconsistenteError:
            log.error("Cálculo inconsistente al procesar %s", self.id)
            raise  # Ya es un error propio; lo dejamos subir tal cual
        except (DatoInvalidoError, ArithmeticError, TypeError) as error:
            # Cualquier otro problema de cálculo se convierte en CalculoInconsistenteError
            raise CalculoInconsistenteError(f"No se pudo procesar {self.id}: {error}") from error
        else:
            # Sin errores: guardamos el costo y cerramos la reserva
            self._costo_total = costo
            self._estado = PROCESADA
            log.info("Reserva %s PROCESADA por %s", self.id, formato_pesos(costo))
        finally:
            # Siempre queda registro del intento, salga bien o mal
            log.debug("Intento de procesar %s terminó en estado %s", self.id, self._estado)
        return self

    # ------------------------------------------------------------------
    # Métodos obligatorios de EntidadBase
    # ------------------------------------------------------------------

    def describir(self):
        costo = formato_pesos(self._costo_total) if self._costo_total is not None else "por calcular"
        extra = ", ".join(f"{k}={v}" for k, v in self._detalles.items())  # Ej.: "personas=8"
        extra = f" ({extra})" if extra else ""  # Solo si hay detalles
        return (f"Reserva {self.id}: {self._cliente.nombre} -> {self._servicio.nombre} | "
                f"{self._duracion:g} {self._servicio.UNIDAD}(s){extra} | {self._estado} | {costo}")

    def validar(self):
        self._cliente.validar()  # El cliente sigue siendo válido
        self._servicio.validar_parametros(self._duracion, **self._detalles)  # Parámetros coherentes
        return True
