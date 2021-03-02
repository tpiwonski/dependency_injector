from __future__ import annotations

import functools
from abc import ABC
from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from inspect import isclass, signature
from typing import Any, Callable, Dict, List, Optional

C = Any
I = Any
O = Any


@dataclass
class Container:
    scoped_classes: Dict[I, C] = field(default_factory=dict)
    transient_classes: Dict[I, C] = field(default_factory=dict)
    singleton_instances: Dict[I, C] = field(default_factory=dict)
    singleton_classes: Dict[I, C] = field(default_factory=dict)

    def add_singleton_class(self, interface: I, clazz: C) -> None:
        assert issubclass(clazz, interface)
        self.singleton_classes[interface] = clazz

    def add_singleton_instance(self, interface: I, instance: O) -> None:
        assert isinstance(instance, interface)
        self.singleton_instances[interface] = instance

    def add_scoped_class(self, interface: I, clazz: C) -> None:
        assert issubclass(clazz, interface)
        self.scoped_classes[interface] = clazz

    def add_transient_class(self, interface: I, clazz: C) -> None:
        assert issubclass(clazz, interface)
        self.transient_classes[interface] = clazz

    def create_instance_of_interface(self, interface: I, scope: Scope) -> O:
        instance = self.singleton_instances.get(interface)
        if instance:
            return instance

        clazz = self.singleton_classes.get(interface)
        if clazz:
            instance = self.create_instance_of_class(clazz, scope)
            self.singleton_instances[interface] = instance
            return instance

        instance = scope.get_instance(interface)
        if instance:
            return instance

        clazz = self.scoped_classes.get(interface)
        if clazz:
            instance = self.create_instance_of_class(clazz, scope)
            scope.add_instance(interface, instance)
            return instance

        clazz = self.transient_classes.get(interface)
        if clazz:
            instance = self.create_instance_of_class(clazz, scope)
            return instance

        raise Exception("Interface {0} not found".format(interface))

    def create_instance_of_class(self, clazz: C, scope: Scope) -> O:
        if is_dataclass(clazz):
            params = {}
            for class_field in fields(clazz):
                if (class_field.default is not MISSING) or (
                    class_field.default_factory is not MISSING  # type: ignore
                ):
                    continue

                try:
                    if not issubclass(class_field.type, ABC):
                        continue
                except TypeError:
                    continue

                instance = self.create_instance_of_interface(class_field.type, scope)
                params[class_field.name] = instance

            return clazz(**params)
        else:
            return clazz()

    def create_parameters(
        self, func: Any, scope: Scope, interfaces: List[I]
    ) -> Dict[str, O]:
        params = {}
        sig = signature(func)
        for name, parameter in sig.parameters.items():

            if parameter.annotation not in interfaces:
                continue

            if parameter.annotation is parameter.empty:
                raise ValueError("Type of parameter {} not specified".format(name))

            if issubclass(parameter.annotation, ABC):
                instance = self.create_instance_of_interface(
                    parameter.annotation, scope
                )
            elif isclass(parameter.annotation):
                instance = self.create_instance_of_class(parameter.annotation, scope)
            else:
                raise ValueError(
                    "Type of parameter {} is not an interface or class".format(name)
                )

            params[name] = instance

        return params


@dataclass
class Scope:
    scoped_instances: Dict[I, O] = field(default_factory=dict)

    def add_instance(self, interface: I, instance: O) -> None:
        self.scoped_instances[interface] = instance

    def get_instance(self, interface: I) -> O:
        return self.scoped_instances.get(interface)


_container = Container()


def scoped(
    interfaces: Optional[List[I]] = None, container: Optional[Container] = None
) -> Any:
    return class_decorator(
        interfaces,
        container,
        lambda cont, iface, cls: cont.add_scoped_class(iface, cls),
    )


def transient(
    interfaces: Optional[List[I]] = None, container: Optional[Container] = None
) -> Any:
    return class_decorator(
        interfaces,
        container,
        lambda cont, iface, cls: cont.add_transient_class(iface, cls),
    )


def singleton(interfaces=None, container=None) -> Any:
    return class_decorator(
        interfaces,
        container,
        lambda cont, iface, cls: cont.add_singleton_class(iface, cls),
    )


def class_decorator(interfaces, container, register) -> Any:
    return functools.partial(class_wrapper, interfaces, container, register)


def class_wrapper(
    interfaces: List[I], container: Container, register: Any, cls: Any
) -> Any:
    c = container or _container
    if interfaces:
        for i in interfaces:
            register(c, i, cls)
    else:
        interface = cls.__bases__[0]  # TODO register all ABC bases?
        register(c, interface, cls)

    return cls


def provide(
    interfaces: List[I],
    *,
    scope: Optional[Scope] = None,
    container: Optional[Container] = None
) -> Callable[[Any], Any]:
    def provide_decorator(func):
        def provide_wrapper(*args, **kwargs):
            s = scope or Scope()
            c = container or _container
            params = c.create_parameters(func, s, interfaces)
            params.update(kwargs)
            return func(*args, **params)

        return provide_wrapper

    return provide_decorator
