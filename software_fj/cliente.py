"""
cliente.py
----------
Clase Cliente: guarda los datos personales de forma encapsulada
(atributos privados con doble guion bajo) y los valida en cada asignación
mediante propiedades (getters y setters).
"""

import re  # Expresiones regulares para validar correo y teléfono

from .entidad import EntidadBase                              # Clase abstracta padre
from .excepciones import DatoInvalidoError, ParametroFaltanteError  # Errores propios
from .registro import obtener_logger                          # Logger del módulo

log = obtener_logger("cliente")  # Logger para este archivo

# Patrón de correo: texto@texto.dominio
PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
# Patrón de celular colombiano: 10 dígitos que empiezan por 3
PATRON_TELEFONO = re.compile(r"^3\d{9}$")


class Cliente(EntidadBase):
    """Cliente de Software FJ con datos personales protegidos."""

    PREFIJO = "CLI"  # Los IDs de clientes serán CLI-0001, CLI-0002...

    def __init__(self, nombre=None, documento=None, correo=None, telefono=None):
        # Revisamos que no falte ningún dato obligatorio antes de crear el objeto
        for campo, valor in (("nombre", nombre), ("documento", documento), ("correo", correo)):
            if valor is None or str(valor).strip() == "":  # Vacío o ausente
                raise ParametroFaltanteError(campo, "Cliente")
        super().__init__()  # Asigna ID y fecha de creación
        # Usamos los setters: cada asignación pasa por su validación
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono  # El teléfono es opcional
        log.info("Cliente creado: %s (%s)", self.__nombre, self.id)  # Evento en el log

    # ------------------------------------------------------------------
    # Propiedades: única forma de leer y modificar los datos privados
    # ------------------------------------------------------------------

    @property
    def nombre(self):
        return self.__nombre  # Devuelve el nombre guardado

    @nombre.setter
    def nombre(self, valor):
        valor = str(valor).strip()  # Quitamos espacios de los extremos
        # Solo letras (con tildes y ñ) y espacios, mínimo 3 caracteres
        if len(valor) < 3 or not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+", valor):
            raise DatoInvalidoError("nombre", valor, "debe tener al menos 3 letras y no llevar números ni símbolos")
        self.__nombre = valor.title()  # Guardamos con mayúscula inicial en cada palabra

    @property
    def documento(self):
        return self.__documento  # Devuelve el número de documento

    @documento.setter
    def documento(self, valor):
        valor = str(valor).strip()  # Lo tratamos siempre como texto
        if not valor.isdigit() or not 6 <= len(valor) <= 10:  # Solo dígitos, de 6 a 10
            raise DatoInvalidoError("documento", valor, "debe tener entre 6 y 10 dígitos numéricos")
        self.__documento = valor  # Guardamos el documento validado

    @property
    def correo(self):
        return self.__correo  # Devuelve el correo

    @correo.setter
    def correo(self, valor):
        valor = str(valor).strip().lower()  # Correos en minúscula
        if not PATRON_CORREO.match(valor):  # Debe cumplir el patrón usuario@dominio.ext
            raise DatoInvalidoError("correo", valor, "no tiene un formato de correo válido")
        self.__correo = valor  # Guardamos el correo validado

    @property
    def telefono(self):
        return self.__telefono  # Devuelve el teléfono (puede ser None)

    @telefono.setter
    def telefono(self, valor):
        if valor is None:  # El teléfono es opcional
            self.__telefono = None
            return
        valor = str(valor).replace(" ", "")  # Quitamos espacios: "300 123 4567" -> "3001234567"
        if not PATRON_TELEFONO.match(valor):  # 10 dígitos empezando por 3
            raise DatoInvalidoError("telefono", valor, "debe ser un celular de 10 dígitos que empiece por 3")
        self.__telefono = valor  # Guardamos el teléfono validado

    # ------------------------------------------------------------------
    # Métodos obligatorios de EntidadBase
    # ------------------------------------------------------------------

    def documento_oculto(self):
        """Muestra solo los últimos 4 dígitos del documento (protección de datos)."""
        return "*" * (len(self.__documento) - 4) + self.__documento[-4:]

    def describir(self):
        # Descripción pública: no mostramos el documento completo
        return f"Cliente {self.id}: {self.__nombre} | doc {self.documento_oculto()} | {self.__correo}"

    def validar(self):
        # Volvemos a pasar cada dato por su setter; si algo se dañó, se lanza la excepción
        self.nombre = self.__nombre
        self.documento = self.__documento
        self.correo = self.__correo
        self.telefono = self.__telefono
        return True  # Si llegó aquí, todo está correcto
