"""Provides base classes for all components of vimiv."""
from typing import TypeVar, Type

GenericType = TypeVar('GenericType')


class AppComponent:
    """Common base class of all components of vimiv.

    Components of vimiv that are referenced between each other or call each
    other's methods should extend this class. App components are registered in
    the main Vimiv class.
    """

    def __init__(self, app):
        self.app = app

    def get_component(self, component_type: Type[GenericType]) -> GenericType:
        return self.app.get_component(component_type)
