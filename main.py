"""
main.py
-------
Simulación del Sistema Integral de Gestión de Software FJ.

Ejecuta 29 operaciones completas, mezclando casos válidos e inválidos:
registro de clientes, creación de servicios, reservas exitosas y fallidas,
cálculos con sobrecarga y errores inesperados. El programa NUNCA se detiene:
cada error queda registrado en logs/software_fj.log.

Ejecución:  python main.py
"""

import sys  # Para ajustar la codificación de la consola

from software_fj.registro import ARCHIVO_LOG, configurar_registro  # Archivo de logs
from software_fj.servicios import formato_pesos                   # Formato de pesos
from software_fj.sistema import SistemaGestion                    # Gestor principal


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Tildes y símbolos en cualquier consola
    except (AttributeError, ValueError):
        pass  # Consolas antiguas: se sigue con la codificación que tengan
    configurar_registro(reiniciar=True)  # Empezamos con un archivo de logs limpio
    sistema = SistemaGestion()           # Creamos el sistema (listas vacías)
    op = sistema.ejecutar                # Atajo para no escribir sistema.ejecutar cada vez

    print("SISTEMA INTEGRAL DE GESTIÓN - SOFTWARE FJ")
    print("Simulación de operaciones (válidas e inválidas)")

    # ------------------------------------------------------------------
    # 1. CLIENTES
    # ------------------------------------------------------------------
    op(1, "Registrar cliente válido: Laura Gómez", sistema.registrar_cliente,
       nombre="laura gómez", documento="1012345678", correo="Laura.Gomez@correo.com", telefono="300 123 4567")

    op(2, "Registrar cliente válido: Carlos Pérez", sistema.registrar_cliente,
       nombre="Carlos Pérez", documento="80123456", correo="carlos.perez@empresa.co")

    op(3, "Registrar cliente con correo inválido (error esperado)", sistema.registrar_cliente,
       nombre="Ana Ruiz", documento="52987654", correo="ana.ruiz-arroba-correo")

    op(4, "Registrar cliente sin documento (error esperado)", sistema.registrar_cliente,
       nombre="Pedro Díaz", correo="pedro@correo.com")

    op(5, "Registrar cliente con documento repetido (error esperado)", sistema.registrar_cliente,
       nombre="Laura Copia", documento="1012345678", correo="otra@correo.com")

    # ------------------------------------------------------------------
    # 2. SERVICIOS
    # ------------------------------------------------------------------
    sala = op(6, "Crear servicio: Sala de juntas (capacidad 10)", sistema.crear_servicio,
              "sala", nombre="Sala de Juntas Norte", tarifa=80_000, capacidad=10)

    equipos = op(7, "Crear servicio: alquiler de 3 proyectores", sistema.crear_servicio,
                 "equipo", nombre="Proyectores Epson", tarifa=45_000, tipo_equipo="Proyector", unidades=3)

    asesoria = op(8, "Crear servicio: asesoría experta en ciberseguridad", sistema.crear_servicio,
                  "asesoria", nombre="Auditoría de Ciberseguridad", tarifa=150_000,
                  area="Ciberseguridad", nivel="Experto")

    op(9, "Crear servicio con tarifa negativa (error esperado)", sistema.crear_servicio,
       "sala", nombre="Sala Fantasma", tarifa=-5000, capacidad=4)

    op(10, "Crear servicio de un tipo que no existe (error esperado)", sistema.crear_servicio,
       "catering", nombre="Almuerzos", tarifa=30_000)

    # Los IDs de los servicios creados (si alguno falló, usamos un ID que no existe)
    id_sala = sala.id if sala else "SRV-XXXX"
    id_equipos = equipos.id if equipos else "SRV-XXXX"
    id_asesoria = asesoria.id if asesoria else "SRV-XXXX"

    # ------------------------------------------------------------------
    # 3. RESERVAS
    # ------------------------------------------------------------------
    r1 = op(11, "Reserva válida: Laura, sala 3 horas para 8 personas", sistema.crear_reserva,
            "1012345678", id_sala, 3, personas=8)
    if r1:  # Solo si se creó, la confirmamos y procesamos con IVA y 10 % de descuento
        op(12, "Confirmar y procesar la reserva de Laura (IVA + 10 % dto.)",
           lambda: r1.confirmar().procesar(descuento=0.10))

    op(13, "Reserva con duración escrita en letras (error esperado)", sistema.crear_reserva,
       "80123456", id_sala, "tres")

    op(14, "Reserva de sala para 40 personas (error esperado: no caben)", sistema.crear_reserva,
       "80123456", id_sala, 2, personas=40)

    op(15, "Reserva de un cliente que no existe (error esperado)", sistema.crear_reserva,
       "99999999", id_asesoria, 2)

    # Reserva de equipos: Carlos aparta 2 de los 3 proyectores
    r2 = op(16, "Reserva válida: Carlos, 2 proyectores por 5 días (confirmada)",
            sistema.reservar, "80123456", id_equipos, 5, cantidad=2)

    # Laura pide otros 2 proyectores, pero solo queda 1 libre
    op(17, "Reserva de 2 proyectores cuando solo queda 1 (error esperado)",
       sistema.reservar, "1012345678", id_equipos, 1, cantidad=2)

    # Procesar con un impuesto mal escrito: TypeError encadenado en CalculoInconsistenteError
    if r2:
        op(18, "Procesar con impuesto 'diecinueve' (error esperado: cálculo inconsistente)",
           r2.procesar, impuesto="diecinueve")
        op(19, "Procesar de nuevo la reserva de Carlos con el IVA correcto", r2.procesar)

    # Asesoría: se confirma, se cancela y luego se intenta procesar
    r3 = op(20, "Reserva de asesoría (4 h), confirmarla y cancelarla",
            lambda: sistema.reservar("1012345678", id_asesoria, 4).cancelar("el cliente reprogramó"))
    if r3:
        op(21, "Procesar una reserva cancelada (error esperado: operación no permitida)", r3.procesar)

    # Servicio en mantenimiento
    if asesoria:
        asesoria.cambiar_disponibilidad(False)  # La asesoría queda fuera de servicio
        op(22, "Reservar la asesoría mientras está en mantenimiento (error esperado)",
           sistema.reservar, "80123456", id_asesoria, 2)
        asesoria.cambiar_disponibilidad(True)  # Vuelve a estar disponible

    # ------------------------------------------------------------------
    # 4. SOBRECARGA DE MÉTODOS (cotizaciones)
    # ------------------------------------------------------------------
    if sala:
        op(23, "Cotizar sala: calcular_costo(2) sin impuesto ni descuento",
           lambda: formato_pesos(sala.calcular_costo(2)))
        op(24, "Cotizar sala: calcular_costo(2, impuesto=0.19, descuento=0.05)",
           lambda: formato_pesos(sala.calcular_costo(2, impuesto=0.19, descuento=0.05)))
        op(25, "Cotizar sala: cotizar(4) -> número (IVA incluido)",
           lambda: formato_pesos(sala.cotizar(4)))
        op(26, "Cotizar sala: cotizar((4, 0.15)) -> tupla (duración, descuento)",
           lambda: formato_pesos(sala.cotizar((4, 0.15))))
        op(27, "Cotizar sala: cotizar({'duracion': 4, 'personas': 10}) -> diccionario",
           lambda: formato_pesos(sala.cotizar({"duracion": 4, "personas": 10})))
        op(28, "Cotizar con un tipo no soportado: cotizar('cuatro') (error esperado)",
           sala.cotizar, "cuatro")

    # ------------------------------------------------------------------
    # 5. ERROR INESPERADO: el sistema sigue funcionando
    # ------------------------------------------------------------------
    op(29, "Llamar una operación con argumentos equivocados (error inesperado)",
       sistema.crear_reserva, "80123456")  # Faltan argumentos: TypeError de Python

    sistema.reporte()  # Resumen final de todo lo que quedó en memoria
    print(f"\nLos eventos y errores quedaron registrados en: {ARCHIVO_LOG}")


# Solo se ejecuta la simulación si se corre este archivo directamente
if __name__ == "__main__":
    main()
