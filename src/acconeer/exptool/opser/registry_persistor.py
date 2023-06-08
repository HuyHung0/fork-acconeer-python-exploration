# Copyright (c) Acconeer AB, 2023
# All rights reserved
from __future__ import annotations

import typing as t

from . import core


class RegistryPersistor(core.Persistor):
    """
    Persistor implementation that can have other persistors registered to it.

    Its 'save' and 'load' implementations exclusively call registered persistor's
    'save' and 'load'.

    This persistor is the hub for recursion and allows circumventing
    the combinatorial explosion of the problem.
    """

    _REGISTRY: t.ClassVar[t.Dict[str, t.Type[core.Persistor]]] = {}

    @classmethod
    def register_persistor(cls, __persistor: t.Type[core.Persistor]) -> t.Type[core.Persistor]:
        """
        Registers a persistor that can extend the handled types.

        This can be called many times with the same persistor without repercussions.
        """
        cls._REGISTRY[__persistor.__name__] = __persistor
        return __persistor

    @classmethod
    def _get_applicable_persistors(cls, __type: type) -> t.List[t.Type[core.Persistor]]:
        """Retrieves the persistors that can handle the specified type"""
        return [
            persistor for persistor in cls._REGISTRY.values() if persistor.is_applicable(__type)
        ]

    @classmethod
    def registry_size(cls) -> int:
        return len(cls._REGISTRY)

    @classmethod
    def is_applicable(cls, __type: core.TypeLike) -> bool:
        return len(cls._get_applicable_persistors(__type)) > 0

    def save(self, instance: t.Any) -> None:
        persistor_classes = self._get_applicable_persistors(self.type_tree.data)

        if not persistor_classes:
            raise core.SaveError(f"No applicable persistors for instance {instance!r:.100}")

        errors = []
        for persistor_class in persistor_classes:
            try:
                persistor_class(self.parent_group, self.name, self.type_tree).save(instance)
            except core.SaveError as save_error:
                errors += [save_error]
                continue
            else:
                return

        raise core.SaveErrorGroup(
            f"Could not save instance of type '{type(instance)}' (with expected type {self.type_tree.data}) using any of the persistors {persistor_classes}.",
            errors,
        )

    def load(self) -> t.Any:
        persistor_classes = self._get_applicable_persistors(self.type_tree.data)

        if not persistor_classes:
            raise core.LoadError(
                f"No applicable persistors for expected type {self.type_tree.data}"
            )

        errors = []
        for persistor_class in persistor_classes:
            try:
                res = persistor_class(self.parent_group, self.name, self.type_tree).load()
            except core.LoadError as load_error:
                errors += [load_error]
                continue
            else:
                return res

        raise core.LoadErrorGroup(
            f"Could not load an instance of type {self.type_tree.data} with any of the persistors {persistor_classes}.",
            errors,
        )
