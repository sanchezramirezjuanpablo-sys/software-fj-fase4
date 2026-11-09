"""
Paquete software_fj
-------------------
Sistema integral de gestión de clientes, servicios y reservas de la
empresa Software FJ (curso Programación 213023, UNAD - Fase 4).
"""

from .cliente import Cliente                                   # Clase Cliente
from .entidad import EntidadBase                               # Clase abstracta general
from .reserva import Reserva                                   # Clase Reserva
from .servicios import (AlquilerEquipo, AsesoriaEspecializada,  # Servicios concretos
                        ReservaSala, Servicio)
from .sistema import SistemaGestion                            # Gestor principal

# Lo que se exporta al hacer "from software_fj import *"
__all__ = ["EntidadBase", "Cliente", "Servicio", "ReservaSala", "AlquilerEquipo",
           "AsesoriaEspecializada", "Reserva", "SistemaGestion"]
