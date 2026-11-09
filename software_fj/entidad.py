"""
entidad.py
----------
Clase abstracta EntidadBase: representa cualquier entidad general del sistema
(clientes, servicios y reservas heredan de ella).

Aporta lo que todas comparten: un identificador único, la fecha de creación
y la obligación de saber describirse y validarse.
"""

from abc import ABC, abstractmethod  # ABC permite crear clases abstractas
from datetime import datetime         # Para guardar la fecha de creación
from itertools import count           # Generador de números consecutivos para los IDs


class EntidadBase(ABC):
    """Entidad general del sistema. No se puede instanciar directamente."""

    # Un contador por prefijo, para que haya CLI-0001, SRV-0001, RES-0001...
    _contadores = {}

    # Prefijo del identificador; las subclases lo cambian (CLI, SRV, RES)
    PREFIJO = "ENT"

    def __init__(self):
        # ID único y legible, por ejemplo "CLI-0001" (atributo protegido con _)
        contador = EntidadBase._contadores.setdefault(self.PREFIJO, count(1))  # Contador de este prefijo
        self._id = f"{self.PREFIJO}-{next(contador):04d}"
        # Momento exacto en que se creó la entidad
        self._fecha_creacion = datetime.now()

    @property
    def id(self):
        """Identificador de solo lectura (no tiene setter, no se puede cambiar)."""
        return self._id

    @property
    def fecha_creacion(self):
        """Fecha de creación de solo lectura."""
        return self._fecha_creacion

    @abstractmethod
    def describir(self):
        """Cada entidad debe devolver un texto que la describa."""

    @abstractmethod
    def validar(self):
        """Cada entidad debe revisar que sus datos sean coherentes; lanza excepción si no."""

    def __str__(self):
        # Al imprimir cualquier entidad se usa su propia descripción (polimorfismo)
        return self.describir()

    def __repr__(self):
        # Representación técnica, útil al depurar
        return f"<{type(self).__name__} {self._id}>"
