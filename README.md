# Software FJ — Sistema Integral de Gestión de Clientes, Servicios y Reservas

Proyecto de la **Fase 4 – Prácticas simuladas** del curso **Programación (213023)** de la UNAD.

Sistema orientado a objetos en Python, **sin base de datos**, que gestiona los clientes, los servicios
(reserva de salas, alquiler de equipos y asesorías especializadas) y las reservas de la empresa
Software FJ. Tiene manejo avanzado de excepciones y registra todos los eventos y errores en un archivo de logs
sin detenerse nunca.

## Cómo ejecutarlo

Requisito: Python 3.10 o superior (no usa librerías externas).

```bash
python main.py
```

El programa simula 29 operaciones (válidas e inválidas), muestra el resultado de cada una en consola
y al final imprime un reporte. Los eventos quedan en `logs/software_fj.log`.

## Estructura del proyecto

```
software_fj/
├── main.py                  # Simulación de las 29 operaciones
├── README.md
├── logs/
│   └── software_fj.log      # Se genera al ejecutar
└── software_fj/             # Paquete con el sistema
    ├── __init__.py
    ├── excepciones.py       # Jerarquía de excepciones personalizadas
    ├── registro.py          # Configuración del archivo de logs
    ├── entidad.py           # Clase abstracta EntidadBase
    ├── cliente.py           # Clase Cliente (encapsulación y validaciones)
    ├── servicios.py         # Clase abstracta Servicio + 3 servicios especializados
    ├── reserva.py           # Clase Reserva (confirmar, cancelar, procesar)
    └── sistema.py           # SistemaGestion: listas internas y red de seguridad
```

## Diagrama de clases (resumen)

```
EntidadBase (abstracta)
├── Cliente
├── Servicio (abstracta)
│   ├── ReservaSala
│   ├── AlquilerEquipo
│   └── AsesoriaEspecializada
└── Reserva  ── usa ──> Cliente y Servicio

SistemaGestion ── contiene listas de ──> Cliente, Servicio, Reserva

SoftwareFJError
├── DatoInvalidoError          ├── ServicioNoDisponibleError
├── ParametroFaltanteError     ├── ReservaInvalidaError
├── ClienteInvalidoError       ├── OperacionNoPermitidaError
├── ServicioInvalidoError      └── CalculoInconsistenteError
```

## Requisitos del enunciado y dónde se cumplen

| Requisito | Dónde está |
|---|---|
| Clase abstracta para entidades generales | `EntidadBase` en `entidad.py` (métodos abstractos `describir()` y `validar()`) |
| Cliente con validaciones y datos encapsulados | `cliente.py`: atributos privados `__nombre`, `__documento`, `__correo`, `__telefono` con propiedades que validan |
| Servicio abstracto + 3 servicios especializados | `servicios.py`: `ReservaSala`, `AlquilerEquipo`, `AsesoriaEspecializada` |
| Polimorfismo y métodos sobrescritos | Cada servicio sobrescribe `calcular_costo()`, `describir()` y `validar_parametros()` |
| Reserva con confirmación, cancelación y procesamiento | `reserva.py`: `confirmar()`, `cancelar()`, `procesar()` |
| Métodos sobrecargados | `calcular_costo(duracion, impuesto=None, descuento=None)` con parámetros opcionales y `cotizar()` con `@singledispatchmethod` (acepta número, tupla o diccionario) |
| Excepciones personalizadas | `excepciones.py` (9 clases) |
| `try/except` | `SistemaGestion.registrar_cliente()`, `crear_servicio()` |
| `try/except/else` | `Reserva.confirmar()` |
| `try/except/finally` | `Reserva.cancelar()` |
| `try/except/else/finally` | `Reserva.procesar()` y `SistemaGestion.ejecutar()` |
| Encadenamiento de excepciones (`raise ... from ...`) | Duración en letras, tipo de servicio inexistente, impuesto mal escrito, datos de cliente inválidos |
| Archivo de logs | `registro.py` → `logs/software_fj.log` |
| Listas internas, sin base de datos | `SistemaGestion._clientes`, `_servicios`, `_reservas` |
| Al menos 10 operaciones, válidas e inválidas | `main.py` simula 29 |
| El sistema no se detiene ante errores | `SistemaGestion.ejecutar()` atrapa todo, lo registra y continúa (incluso errores inesperados de Python) |

## Nota sobre la sobrecarga en Python

Python no permite definir dos métodos con el mismo nombre y distintos parámetros, como Java o C#.
Por eso la sobrecarga se logra de dos formas idiomáticas:

1. **Parámetros opcionales:** `calcular_costo(2)`, `calcular_costo(2, impuesto=0.19)`,
   `calcular_costo(2, descuento=0.1)` o `calcular_costo(2, 0.19, 0.1)`.
2. **`functools.singledispatchmethod`:** `cotizar(4)`, `cotizar((4, 0.15))` y
   `cotizar({"duracion": 4, "personas": 10})` ejecutan versiones distintas del método según el tipo del argumento.
