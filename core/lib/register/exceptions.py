"""
Excepciones personalizadas para el sistema de auto-registro de rutas.

Este módulo define las excepciones y warnings que se lanzan durante
el proceso de descubrimiento y registro automático de rutas HTTP,
tanto para templates como para controllers de API.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Excepciones compartidas (templates y API)
# ---------------------------------------------------------------------------


class DuplicateRouteHandlerError(Exception):
    """Se lanza cuando se detectan dos handlers con el mismo nombre y método HTTP.

    Esto ocurre cuando dos métodos decorados con el mismo decorador HTTP
    (e.g. @Get) comparten el mismo nombre de función dentro del mismo
    contexto de registro.

    Attributes:
        handler_name: Nombre del método handler duplicado.
        http_method: Método HTTP donde se encontró la colisión (GET, POST, etc.).
        existing_module: Módulo donde se registró originalmente el handler.
        conflicting_module: Módulo donde se detectó el duplicado.
    """

    def __init__(
        self,
        handler_name: str,
        http_method: str,
        existing_module: Optional[str] = None,
        conflicting_module: Optional[str] = None,
    ) -> None:
        self.handler_name: str = handler_name
        self.http_method: str = http_method
        self.existing_module: Optional[str] = existing_module
        self.conflicting_module: Optional[str] = conflicting_module

        message: str = (
            f"Duplicate route handler detected: "
            f"handler '{handler_name}' with HTTP method '{http_method}' "
            f"is already registered."
        )

        if existing_module is not None:
            message += f" Originally registered in module '{existing_module}'."

        if conflicting_module is not None:
            message += f" Conflicting registration in module '{conflicting_module}'."

        super().__init__(message)


# ---------------------------------------------------------------------------
# Excepciones para Templates
# ---------------------------------------------------------------------------


class TemplateControllerMissingError(Exception):
    """Se lanza cuando un archivo template.py no contiene una clase que herede de Template.

    Esto indica que el archivo template.py existe en el directorio de templates,
    pero no define ninguna clase controladora válida que herede de la clase base
    ``Template``.

    Attributes:
        template_file_path: Ruta absoluta del archivo template.py problemático.
        module_path: Ruta del módulo Python importado.
    """

    def __init__(
        self,
        template_file_path: str,
        module_path: Optional[str] = None,
    ) -> None:
        self.template_file_path: str = template_file_path
        self.module_path: Optional[str] = module_path

        message: str = (
            f"Template controller missing: "
            f"the file '{template_file_path}' exists but does not contain "
            f"any class that inherits from 'Template'."
        )

        if module_path is not None:
            message += f" Module path: '{module_path}'."

        super().__init__(message)


class TemplateFileNotFoundWarning(UserWarning):
    """Warning emitido cuando un directorio dentro del árbol de templates no contiene template.py.

    Este warning no interrumpe la ejecución. Se emite con ``warnings.warn()``
    para informar al desarrollador de que un directorio fue ignorado durante
    el escaneo recursivo porque no contiene el archivo ``template.py`` requerido.

    Attributes:
        directory_path: Ruta del directorio que no contiene template.py.
    """

    def __init__(
        self,
        directory_path: str,
    ) -> None:
        self.directory_path: str = directory_path

        message: str = (
            f"Template file not found: "
            f"the directory '{directory_path}' does not contain a 'template.py' file. "
            f"This directory will be skipped during route auto-registration."
        )

        super().__init__(message)


# ---------------------------------------------------------------------------
# Excepciones para API Controllers
# ---------------------------------------------------------------------------


class ApiControllerMissingError(Exception):
    """Se lanza cuando un archivo controller.py no contiene una clase que herede de Controller.

    Esto indica que el archivo controller.py existe en el directorio de la API,
    pero no define ninguna clase controladora válida que herede de la clase base
    ``Controller``.

    Attributes:
        controller_file_path: Ruta absoluta del archivo controller.py problemático.
        module_path: Ruta del módulo Python importado.
    """

    def __init__(
        self,
        controller_file_path: str,
        module_path: Optional[str] = None,
    ) -> None:
        self.controller_file_path: str = controller_file_path
        self.module_path: Optional[str] = module_path

        message: str = (
            f"API controller missing: "
            f"the file '{controller_file_path}' exists but does not contain "
            f"any class that inherits from 'Controller'."
        )

        if module_path is not None:
            message += f" Module path: '{module_path}'."

        super().__init__(message)


class ControllerFileNotFoundWarning(UserWarning):
    """Warning emitido cuando un directorio dentro del árbol API no contiene controller.py.

    Este warning no interrumpe la ejecución. Se emite con ``warnings.warn()``
    para informar al desarrollador de que un directorio fue ignorado durante
    el escaneo recursivo porque no contiene el archivo ``controller.py`` requerido.

    Attributes:
        directory_path: Ruta del directorio que no contiene controller.py.
    """

    def __init__(
        self,
        directory_path: str,
    ) -> None:
        self.directory_path: str = directory_path

        message: str = (
            f"Controller file not found: "
            f"the directory '{directory_path}' does not contain a 'controller.py' file. "
            f"This directory will be skipped during API route auto-registration."
        )

        super().__init__(message)
