"""
excepciones.py
--------------
Jerarquía de excepciones personalizadas del sistema Software FJ.

Todas heredan de SoftwareFJError, así el programa principal puede
atrapar cualquier error propio del negocio con un solo except,
sin ocultar los errores inesperados de Python.
"""


class SoftwareFJError(Exception):
    """Excepción base de todo el sistema Software FJ."""

    def __init__(self, mensaje, codigo="SFJ-000"):
        # Guardamos un código corto para identificar el tipo de error en el log
        self.codigo = codigo
        # Llamamos al constructor de Exception para que el mensaje se muestre normalmente
        super().__init__(mensaje)

    def __str__(self):
        # Representación del error: "[código] mensaje"
        return f"[{self.codigo}] {super().__str__()}"


# ---------------------------------------------------------------------------
# Errores de datos
# ---------------------------------------------------------------------------

class DatoInvalidoError(SoftwareFJError):
    """Un dato tiene formato o valor incorrecto (correo mal escrito, número negativo...)."""

    def __init__(self, campo, valor, motivo):
        # Guardamos qué campo falló y con qué valor, útil para depurar
        self.campo = campo
        self.valor = valor
        # Armamos un mensaje claro con el campo, el valor recibido y el motivo
        super().__init__(f"Dato inválido en '{campo}' ({valor!r}): {motivo}", "SFJ-100")


class ParametroFaltanteError(SoftwareFJError):
    """Falta un parámetro obligatorio para crear un objeto u operar."""

    def __init__(self, parametro, contexto):
        # Nombre del parámetro que no llegó
        self.parametro = parametro
        # Mensaje indicando qué falta y dónde
        super().__init__(f"Falta el parámetro obligatorio '{parametro}' en {contexto}", "SFJ-101")


# ---------------------------------------------------------------------------
# Errores de entidades
# ---------------------------------------------------------------------------

class ClienteInvalidoError(SoftwareFJError):
    """No se pudo registrar o usar un cliente."""

    def __init__(self, mensaje):
        # Código propio de los errores de clientes
        super().__init__(mensaje, "SFJ-200")


class ServicioInvalidoError(SoftwareFJError):
    """Un servicio no se pudo crear o sus parámetros no son válidos."""

    def __init__(self, mensaje):
        # Código propio de los errores de servicios
        super().__init__(mensaje, "SFJ-300")


class ServicioNoDisponibleError(SoftwareFJError):
    """Se intentó reservar un servicio que está fuera de servicio o agotado."""

    def __init__(self, nombre_servicio):
        # Guardamos el nombre del servicio no disponible
        self.nombre_servicio = nombre_servicio
        # Mensaje para el usuario
        super().__init__(f"El servicio '{nombre_servicio}' no está disponible en este momento", "SFJ-301")


# ---------------------------------------------------------------------------
# Errores de reservas y operaciones
# ---------------------------------------------------------------------------

class ReservaInvalidaError(SoftwareFJError):
    """La reserva tiene datos incorrectos (duración, cliente o servicio)."""

    def __init__(self, mensaje):
        # Código propio de los errores de reservas
        super().__init__(mensaje, "SFJ-400")


class OperacionNoPermitidaError(SoftwareFJError):
    """La operación no se puede hacer en el estado actual (ej. cancelar algo ya procesado)."""

    def __init__(self, operacion, estado_actual):
        # Operación que se intentó hacer
        self.operacion = operacion
        # Estado en el que estaba el objeto
        self.estado_actual = estado_actual
        # Mensaje explicando por qué no se permite
        super().__init__(
            f"No se puede '{operacion}' una reserva en estado {estado_actual}", "SFJ-401"
        )


class CalculoInconsistenteError(SoftwareFJError):
    """El cálculo de un costo dio un resultado imposible (negativo, infinito, etc.)."""

    def __init__(self, mensaje):
        # Código propio de los errores de cálculo
        super().__init__(mensaje, "SFJ-500")
