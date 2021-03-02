import functools
from abc import ABC
from dataclasses import MISSING, fields, is_dataclass
from inspect import isclass, signature


class Container(object):
    def __init__(self):
        self.scoped_classes = {}
        self.transient_classes = {}
        self.singleton_classes = {}
        self.singleton_instances = {}

    def add_singleton_class(self, interface, clazz):
        assert issubclass(clazz, interface)
        self.singleton_classes[interface] = clazz

    def add_singleton_instance(self, interface, instance):
        assert isinstance(instance, interface)
        self.singleton_instances[interface] = instance

    def add_scoped_class(self, interface, clazz):
        assert issubclass(clazz, interface)
        self.scoped_classes[interface] = clazz

    def add_transient_class(self, interface, clazz):
        assert issubclass(clazz, interface)
        self.transient_classes[interface] = clazz

    def create_instance_of_interface(self, interface, scope):
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

    def create_instance_of_class(self, clazz, scope):
        if is_dataclass(clazz):
            params = {}
            for field in fields(clazz):
                if field.default is not MISSING or field.default_factory is not MISSING:
                    continue

                try:
                    if not issubclass(field.type, ABC):
                        continue
                except TypeError:
                    continue

                instance = self.create_instance_of_interface(field.type, scope)
                params[field.name] = instance

            return clazz(**params)
        else:
            return clazz()

    def create_parameters(self, func, scope, interfaces):
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


class Scope(object):
    def __init__(self):
        self.scoped_instances = {}

    def add_instance(self, interface, instance):
        self.scoped_instances[interface] = instance

    def get_instance(self, interface):
        return self.scoped_instances.get(interface)


_container = Container()


def scoped(interfaces=None, container=None):
    return class_decorator(
        interfaces,
        container,
        lambda cont, iface, cls: cont.add_scoped_class(iface, cls),
    )


def transient(interfaces=None, container=None):
    return class_decorator(
        interfaces,
        container,
        lambda cont, iface, cls: cont.add_transient_class(iface, cls),
    )


def singleton(interfaces=None, container=None):
    return class_decorator(
        interfaces,
        container,
        lambda cont, iface, cls: cont.add_singleton_class(iface, cls),
    )


def class_decorator(interfaces, container, register):
    return functools.partial(class_wrapper, interfaces, container, register)


def class_wrapper(interfaces, container, register, cls):
    c = container or _container
    if interfaces:
        for i in interfaces:
            register(c, i, cls)
    else:
        interface = cls.__bases__[0]  # TODO register all ABC bases?
        register(c, interface, cls)

    return cls


def provide(interfaces, *, scope=None, container=None):
    def provide_decorator(func):
        def provide_wrapper(*args, **kwargs):
            s = scope or Scope()
            c = container or _container
            params = c.create_parameters(func, s, interfaces)
            params.update(kwargs)
            return func(*args, **params)

        return provide_wrapper

    return provide_decorator
