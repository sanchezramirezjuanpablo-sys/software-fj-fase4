"""
servicios.py
------------
Clase abstracta Servicio y sus tres servicios especializados:
    - ReservaSala            (se cobra por hora)
    - AlquilerEquipo         (se cobra por día y por unidad)
    - AsesoriaEspecializada  (se cobra por hora según el nivel del asesor)

Cada subclase sobrescribe calcular_costo(), describir() y validar_parametros()
(polimorfismo). Además, Servicio ofrece dos formas de "sobrecarga":
    1. calcular_costo() con parámetros opcionales (impuesto y descuento).
    2. cotizar() con @singledispatchmethod, que cambia de comportamiento
       según el tipo de dato recibido (número, tupla o diccionario).
"""

import math                                     # isfinite() para detectar resultados imposibles
from abc import abstractmethod                  # Para declarar métodos abstractos
from functools import singledispatchmethod      # Sobrecarga por tipo de argumento

from .entidad import EntidadBase                # Clase abstracta padre
from .excepciones import (                      # Excepciones propias que usa este módulo
    CalculoInconsistenteError,
    DatoInvalidoError,
    ParametroFaltanteError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
)
from .registro import obtener_logger            # Logger del módulo

log = obtener_logger("servicios")  # Logger para este archivo

IVA = 0.19  # Impuesto por defecto en Colombia (19 %)


def formato_pesos(valor):
    """Convierte 1234567.8 en '$ 1.234.568' (formato de pesos colombianos)."""
    return "$ " + f"{valor:,.0f}".replace(",", ".")


class Servicio(EntidadBase):
    """Servicio general que ofrece Software FJ. Es abstracta: no se instancia directo."""

    PREFIJO = "SRV"        # Los IDs de servicios serán SRV-0001, SRV-0002...
    UNIDAD = "hora"        # Unidad de cobro; las subclases la cambian si cobran distinto
    DURACION_MAXIMA = 12   # Máxima duración permitida por reserva (en la unidad de cobro)

    def __init__(self, nombre=None, tarifa=None):
        # Los dos datos son obligatorios para cualquier servicio
        if nombre is None or str(nombre).strip() == "":
            raise ParametroFaltanteError("nombre", type(self).__name__)
        if tarifa is None:
            raise ParametroFaltanteError("tarifa", type(self).__name__)
        try:
            tarifa = float(tarifa)  # Convertimos la tarifa a número
        except (TypeError, ValueError) as error:
            # Encadenamos: el error original (ValueError) queda guardado como causa
            raise ServicioInvalidoError(f"La tarifa {tarifa!r} no es un número") from error
        if tarifa <= 0 or not math.isfinite(tarifa):  # Debe ser positiva y finita
            raise ServicioInvalidoError(f"La tarifa debe ser mayor que cero (se recibió {tarifa})")
        super().__init__()                    # Asigna ID y fecha de creación
        self._nombre = str(nombre).strip()    # Nombre del servicio (protegido)
        self._tarifa = tarifa                 # Precio por unidad de cobro (protegido)
        self._disponible = True               # Todo servicio nace disponible
        log.info("Servicio creado: %s (%s)", self._nombre, self.id)  # Evento en el log

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def nombre(self):
        return self._nombre  # Nombre del servicio

    @property
    def tarifa(self):
        return self._tarifa  # Tarifa por unidad de cobro

    @property
    def disponible(self):
        return self._disponible  # True si se puede reservar

    def cambiar_disponibilidad(self, disponible):
        """Activa o desactiva el servicio (por mantenimiento, por ejemplo)."""
        self._disponible = bool(disponible)  # Guardamos el nuevo estado
        log.warning("Servicio %s marcado como %s", self.id, "DISPONIBLE" if disponible else "NO DISPONIBLE")

    # ------------------------------------------------------------------
    # Métodos abstractos: cada servicio los implementa a su manera
    # ------------------------------------------------------------------

    @abstractmethod
    def calcular_costo(self, duracion, impuesto=None, descuento=None, **detalles):
        """Costo total de usar el servicio 'duracion' unidades."""

    @abstractmethod
    def validar_parametros(self, duracion, **detalles):
        """Revisa que la duración y los detalles de la reserva tengan sentido."""

    # ------------------------------------------------------------------
    # Métodos comunes
    # ------------------------------------------------------------------

    def validar(self):
        """Revisa los datos propios del servicio (método de EntidadBase)."""
        if self._tarifa <= 0:  # Una tarifa no puede quedar en cero o negativa
            raise ServicioInvalidoError(f"{self.id} tiene una tarifa inválida")
        return True  # Datos correctos

    def verificar_disponibilidad(self, **detalles):
        """Lanza ServicioNoDisponibleError si no se puede reservar ahora."""
        if not self._disponible:  # Servicio apagado
            raise ServicioNoDisponibleError(self._nombre)

    def ocupar(self, **detalles):
        """Aparta el servicio al confirmar una reserva (las subclases lo amplían)."""
        self.verificar_disponibilidad(**detalles)  # Primero confirmamos que se pueda

    def liberar(self, **detalles):
        """Devuelve lo apartado al cancelar una reserva (por defecto no hay nada que devolver)."""

    def _validar_duracion(self, duracion):
        """Validación común de la duración, usada por todas las subclases."""
        if isinstance(duracion, bool) or not isinstance(duracion, (int, float)):  # Debe ser número
            raise DatoInvalidoError("duracion", duracion, "debe ser un número")
        if not 0 < duracion <= self.DURACION_MAXIMA:  # Dentro del rango permitido
            raise DatoInvalidoError(
                "duracion", duracion, f"debe estar entre 1 y {self.DURACION_MAXIMA} {self.UNIDAD}(s)"
            )

    @staticmethod
    def _aplicar_ajustes(subtotal, impuesto=None, descuento=None):
        """
        Aplica descuento e impuesto a un subtotal.
        Es la base de la "sobrecarga" de calcular_costo:
            _aplicar_ajustes(100)                 -> 100
            _aplicar_ajustes(100, impuesto=0.19)  -> 119
            _aplicar_ajustes(100, descuento=0.1)  -> 90
            _aplicar_ajustes(100, 0.19, 0.1)      -> 107.1
        """
        try:
            total = subtotal  # Partimos del subtotal
            if descuento is not None:  # Solo si se envió descuento
                if not 0 <= descuento < 1:  # Un descuento del 100 % o más no tiene sentido
                    raise DatoInvalidoError("descuento", descuento, "debe estar entre 0 y 0.99")
                total = total * (1 - descuento)  # Restamos el porcentaje
            if impuesto is not None:  # Solo si se envió impuesto
                if not 0 <= impuesto <= 0.5:  # Rango razonable de impuestos
                    raise DatoInvalidoError("impuesto", impuesto, "debe estar entre 0 y 0.5")
                total = total * (1 + impuesto)  # Sumamos el porcentaje
        except TypeError as error:
            # Ej.: impuesto="diecinueve". El TypeError original queda como causa
            raise CalculoInconsistenteError(
                f"No se pudo calcular el costo con impuesto={impuesto!r} y descuento={descuento!r}"
            ) from error
        if not math.isfinite(total) or total < 0:  # Resultado imposible
            raise CalculoInconsistenteError(f"El costo calculado no es válido: {total}")
        return round(total, 2)  # Redondeamos a centavos

    # ------------------------------------------------------------------
    # Sobrecarga por tipo con singledispatchmethod
    # ------------------------------------------------------------------

    @singledispatchmethod
    def cotizar(self, consulta):
        """Versión por defecto: el tipo de dato no es soportado."""
        raise DatoInvalidoError("consulta", consulta, "use un número, una tupla (duración, descuento) o un diccionario")

    @cotizar.register(int)
    @cotizar.register(float)
    def _(self, consulta):
        # cotizar(3) -> costo de 3 unidades con IVA incluido
        return self.calcular_costo(consulta, impuesto=IVA)

    @cotizar.register(tuple)
    def _(self, consulta):
        # cotizar((3, 0.10)) -> 3 unidades con 10 % de descuento y con IVA
        duracion, descuento = consulta  # Desempaquetamos la tupla
        return self.calcular_costo(duracion, impuesto=IVA, descuento=descuento)

    @cotizar.register(dict)
    def _(self, consulta):
        # cotizar({"duracion": 3, "impuesto": 0, ...}) -> control total de los parámetros
        datos = dict(consulta)  # Copia para no modificar el diccionario original
        if "duracion" not in datos:  # La duración es obligatoria
            raise ParametroFaltanteError("duracion", "cotizar")
        duracion = datos.pop("duracion")  # Sacamos la duración
        return self.calcular_costo(duracion, **datos)  # El resto son parámetros opcionales


# ======================================================================
# Servicio 1: Reserva de salas
# ======================================================================

class ReservaSala(Servicio):
    """Alquiler de salas de reuniones o capacitación, cobrado por hora."""

    UNIDAD = "hora"         # Se cobra por hora
    DURACION_MAXIMA = 12    # Máximo 12 horas seguidas
    CARGO_ASEO = 20_000     # Cargo fijo de aseo por cada reserva

    def __init__(self, nombre=None, tarifa=None, capacidad=None):
        if capacidad is None:  # La capacidad es obligatoria para una sala
            raise ParametroFaltanteError("capacidad", "ReservaSala")
        super().__init__(nombre, tarifa)  # Validaciones comunes de Servicio
        if not isinstance(capacidad, int) or capacidad <= 0:  # Número entero positivo
            raise ServicioInvalidoError(f"La capacidad de la sala debe ser un entero positivo ({capacidad!r})")
        self._capacidad = capacidad  # Número máximo de personas

    def validar_parametros(self, duracion, personas=1, **detalles):
        self._validar_duracion(duracion)  # Regla común de duración
        if not isinstance(personas, int) or personas <= 0:  # Personas válidas
            raise DatoInvalidoError("personas", personas, "debe ser un entero positivo")
        if personas > self._capacidad:  # No caben
            raise DatoInvalidoError("personas", personas, f"la sala '{self._nombre}' admite máximo {self._capacidad}")
        return True  # Todo bien

    def calcular_costo(self, duracion, impuesto=None, descuento=None, personas=1, **detalles):
        self.validar_parametros(duracion, personas)  # Validamos antes de calcular
        subtotal = self._tarifa * duracion + self.CARGO_ASEO  # Horas × tarifa + aseo
        return self._aplicar_ajustes(subtotal, impuesto, descuento)  # Descuento e impuesto opcionales

    def describir(self):
        estado = "disponible" if self._disponible else "NO disponible"  # Texto del estado
        return (f"Sala {self.id}: {self._nombre} | {self._capacidad} personas | "
                f"{formato_pesos(self._tarifa)}/hora | {estado}")


# ======================================================================
# Servicio 2: Alquiler de equipos
# ======================================================================

class AlquilerEquipo(Servicio):
    """Alquiler de equipos (portátiles, proyectores...), cobrado por día y por unidad."""

    UNIDAD = "día"          # Se cobra por día
    DURACION_MAXIMA = 30    # Máximo 30 días
    SEGURO = 0.05           # Seguro del 5 % sobre el valor del alquiler

    def __init__(self, nombre=None, tarifa=None, tipo_equipo=None, unidades=None):
        for campo, valor in (("tipo_equipo", tipo_equipo), ("unidades", unidades)):  # Datos obligatorios
            if valor is None:
                raise ParametroFaltanteError(campo, "AlquilerEquipo")
        super().__init__(nombre, tarifa)  # Validaciones comunes de Servicio
        if not isinstance(unidades, int) or unidades <= 0:  # Inventario válido
            raise ServicioInvalidoError(f"Las unidades disponibles deben ser un entero positivo ({unidades!r})")
        self._tipo_equipo = str(tipo_equipo)    # Ej.: "Proyector"
        self._unidades_totales = unidades       # Inventario total
        self._unidades_libres = unidades        # Unidades que no están alquiladas

    @property
    def unidades_libres(self):
        return self._unidades_libres  # Cuántas unidades quedan libres

    def validar_parametros(self, duracion, cantidad=1, **detalles):
        self._validar_duracion(duracion)  # Regla común de duración
        if not isinstance(cantidad, int) or cantidad <= 0:  # Cantidad válida
            raise DatoInvalidoError("cantidad", cantidad, "debe ser un entero positivo")
        if cantidad > self._unidades_totales:  # Más de las que existen
            raise DatoInvalidoError("cantidad", cantidad, f"solo existen {self._unidades_totales} unidades")
        return True  # Todo bien

    def verificar_disponibilidad(self, cantidad=1, **detalles):
        super().verificar_disponibilidad()  # Primero, que el servicio esté activo
        if cantidad > self._unidades_libres:  # Inventario insuficiente en este momento
            raise ServicioNoDisponibleError(
                f"{self._nombre} (pidió {cantidad}, quedan {self._unidades_libres})"
            )

    def ocupar(self, cantidad=1, **detalles):
        super().ocupar(cantidad=cantidad)  # Verifica disponibilidad
        self._unidades_libres -= cantidad  # Descontamos del inventario
        log.info("%s: se apartaron %d unidades, quedan %d", self.id, cantidad, self._unidades_libres)

    def liberar(self, cantidad=1, **detalles):
        # Devolvemos al inventario sin pasar del total
        self._unidades_libres = min(self._unidades_totales, self._unidades_libres + cantidad)
        log.info("%s: se liberaron %d unidades, quedan %d", self.id, cantidad, self._unidades_libres)

    def calcular_costo(self, duracion, impuesto=None, descuento=None, cantidad=1, **detalles):
        self.validar_parametros(duracion, cantidad)  # Validamos antes de calcular
        alquiler = self._tarifa * duracion * cantidad  # Días × unidades × tarifa
        subtotal = alquiler * (1 + self.SEGURO)  # Sumamos el seguro
        return self._aplicar_ajustes(subtotal, impuesto, descuento)  # Descuento e impuesto opcionales

    def describir(self):
        estado = "disponible" if self._disponible else "NO disponible"  # Texto del estado
        return (f"Equipo {self.id}: {self._nombre} ({self._tipo_equipo}) | "
                f"{self._unidades_libres}/{self._unidades_totales} libres | "
                f"{formato_pesos(self._tarifa)}/día | {estado}")


# ======================================================================
# Servicio 3: Asesorías especializadas
# ======================================================================

class AsesoriaEspecializada(Servicio):
    """Asesoría con un experto, cobrada por hora según el nivel del asesor."""

    UNIDAD = "hora"         # Se cobra por hora
    DURACION_MAXIMA = 8     # Máximo una jornada de 8 horas
    # Multiplicador de la tarifa según el nivel
    NIVELES = {"basico": 1.0, "avanzado": 1.3, "experto": 1.6}

    def __init__(self, nombre=None, tarifa=None, area=None, nivel="basico"):
        if area is None:  # El área de la asesoría es obligatoria
            raise ParametroFaltanteError("area", "AsesoriaEspecializada")
        super().__init__(nombre, tarifa)  # Validaciones comunes de Servicio
        nivel = str(nivel).lower()  # Aceptamos "Experto", "EXPERTO"...
        if nivel not in self.NIVELES:  # Solo niveles conocidos
            raise ServicioInvalidoError(f"Nivel '{nivel}' no existe. Use: {', '.join(self.NIVELES)}")
        self._area = str(area)   # Ej.: "Ciberseguridad"
        self._nivel = nivel      # Nivel del asesor

    def validar_parametros(self, duracion, **detalles):
        self._validar_duracion(duracion)  # Solo aplica la regla común de duración
        return True  # Todo bien

    def calcular_costo(self, duracion, impuesto=None, descuento=None, **detalles):
        self.validar_parametros(duracion)  # Validamos antes de calcular
        subtotal = self._tarifa * self.NIVELES[self._nivel] * duracion  # Horas × tarifa × nivel
        return self._aplicar_ajustes(subtotal, impuesto, descuento)  # Descuento e impuesto opcionales

    def describir(self):
        estado = "disponible" if self._disponible else "NO disponible"  # Texto del estado
        return (f"Asesoría {self.id}: {self._nombre} | área {self._area} | nivel {self._nivel} | "
                f"{formato_pesos(self._tarifa)}/hora | {estado}")
