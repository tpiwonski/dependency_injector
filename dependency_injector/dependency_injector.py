from __future__ import annotations

import abc
import functools
from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from inspect import signature
from typing import Any, Callable, Dict, List, Optional

Implementation = Any
Interface = Any
Instance = Any


class DependencyInjectionError(Exception):
    pass


@dataclass
class Container:
    scoped_classes: Dict[Interface, Implementation] = field(default_factory=dict)
    transient_classes: Dict[Interface, Implementation] = field(default_factory=dict)
    singleton_instances: Dict[Interface, Implementation] = field(default_factory=dict)
    singleton_classes: Dict[Interface, Implementation] = field(default_factory=dict)

    def register_singleton_class(
        self, interface: Interface, clazz: Implementation
    ) -> None:
        assert issubclass(clazz, interface)
        self.singleton_classes[interface] = clazz

    def register_scoped_class(
        self, interface: Interface, clazz: Implementation
    ) -> None:
        assert issubclass(clazz, interface)
        self.scoped_classes[interface] = clazz

    def register_transient_class(
        self, interface: Interface, clazz: Implementation
    ) -> None:
        assert issubclass(clazz, interface)
        self.transient_classes[interface] = clazz

    def create_instance_of_interface(
        self, interface: Interface, scope: Scope
    ) -> Instance:
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

        raise DependencyInjectionError(f"Interface or class {interface} not registered")

    def create_instance_of_class(self, clazz: Implementation, scope: Scope) -> Instance:
        if is_dataclass(clazz):
            params = {}
            for class_field in fields(clazz):
                if (class_field.default is not MISSING) or (
                    class_field.default_factory is not MISSING  # type: ignore
                ):
                    continue

                params[class_field.name] = self.create_instance_of_interface(
                    class_field.type, scope
                )

            return clazz(**params)
        else:
            return clazz()

    def create_parameters(
        self, func: Any, interfaces: List[Interface], scope: Scope
    ) -> Dict[str, Instance]:
        params = {}
        sig = signature(func)
        for name, parameter in sig.parameters.items():

            if parameter.annotation not in interfaces:
                continue

            if parameter.annotation is parameter.empty:
                raise DependencyInjectionError(
                    f"Type of parameter {parameter} not specified"
                )

            params[name] = self.create_instance_of_interface(
                parameter.annotation, scope
            )

        return params

    def create_instances(
        self, interfaces: List[Interface], scope: Scope
    ) -> Dict[Interface, Instance]:
        return {
            interface: self.create_instance_of_interface(interface, scope)
            for interface in interfaces
        }


@dataclass
class Scope:
    scoped_instances: Dict[Interface, Instance] = field(default_factory=dict)

    def add_instance(self, interface: Interface, instance: Instance) -> None:
        self.scoped_instances[interface] = instance

    def get_instance(self, interface: Interface) -> Instance:
        return self.scoped_instances.get(interface)


_container = Container()


def scoped(
    interfaces: Optional[List[Interface]] = None,
    *,
    container: Optional[Container] = None,
) -> Any:
    return class_decorator(
        interfaces,
        container,
        lambda cont, iface, cls: cont.register_scoped_class(iface, cls),
    )


def transient(
    interfaces: Optional[List[Interface]] = None,
    *,
    container: Optional[Container] = None,
) -> Any:
    return class_decorator(
        interfaces,
        container,
        lambda cont, iface, cls: cont.register_transient_class(iface, cls),
    )


def singleton(interfaces: Optional[List[Interface]] = None, *, container=None) -> Any:
    return class_decorator(
        interfaces,
        container,
        lambda cont, iface, cls: cont.register_singleton_class(iface, cls),
    )


def class_decorator(interfaces, container, register) -> Any:
    return functools.partial(class_wrapper, interfaces, container, register)


def class_wrapper(
    interfaces: List[Interface], container: Container, register: Any, cls: Any
) -> Any:
    c = container or _container
    if interfaces:
        for i in interfaces:
            register(c, i, cls)
    else:
        interfaces = [
            interface for interface in cls.__bases__ if issubclass(interface, abc.ABC)
        ]
        if not interfaces:
            if not is_dataclass(cls):
                raise DependencyInjectionError(
                    "Only classes annotated with @dataclass can provide implicit interface"
                )

            interfaces = [cls]

        for interface in interfaces:
            register(c, interface, cls)

    return cls


def inject(
    interfaces: List[Interface],
    *,
    scope: Optional[Scope] = None,
    container: Optional[Container] = None,
) -> Callable[[Any], Any]:
    def provide_decorator(func):
        def provide_wrapper(*args, **kwargs):
            params = (container or _container).create_parameters(
                func, interfaces, scope or Scope()
            )
            params.update(kwargs)
            return func(*args, **params)

        return provide_wrapper

    return provide_decorator


def provide(
    interfaces: List[Interface],
    *,
    scope: Optional[Scope] = None,
    container: Optional[Container] = None,
) -> Dict[Interface, Instance]:
    return (container or _container).create_instances(interfaces, scope or Scope())


def provide_single(
    interface: Interface,
    *,
    scope: Optional[Scope] = None,
    container: Optional[Container] = None,
) -> Instance:
    return (container or _container).create_instances([interface], scope or Scope())[
        interface
    ]


def provide_many(
    interfaces: List[Interface],
    *,
    scope: Optional[Scope] = None,
    container: Optional[Container] = None,
) -> List[Instance]:
    instances = (container or _container).create_instances(interfaces, scope or Scope())
    return [instances[interface] for interface in interfaces]
