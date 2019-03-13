from inspect import signature, getattr_static, isclass
from abc import ABC
import threading
import functools


class Container(object):
 
    def __init__(self):
        self.scoped_classes = {}
        self.transient_classes = {}
        self.singleton_classes = {}
        self.singleton_instances = {}

    def add_singleton_class(self, interface, clazz):
        self.singleton_classes[interface] = clazz

    def add_singleton_instance(self, interface, instance):
        self.singleton_instances[interface] = instance

    def add_scoped_class(self, interface, clazz):
        self.scoped_classes[interface] = clazz

    def add_transient_class(self, interface, clazz):
        self.transient_classes[interface] = clazz

    def create_instance_of_interface(self, interface, scope):
        print("IOC: create instance of interface {0}".format(interface))
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
        print("IOC: create instance of class {0}".format(clazz))
        constructor = getattr_static(clazz, '__init__')
        args = {}
        if constructor is not None:
            # args = self.initialize_parameters(constructor)

            sig = signature(constructor)
            for i, x in enumerate(sig.parameters.items()):
                n, p = x
                if (i == 0 or
                    p.kind == p.VAR_POSITIONAL or
                    p.kind == p.VAR_KEYWORD
                ):
                    continue

                if p.annotation is p.empty:
                    raise ValueError("Type of parameter {} not specified".format(n))

                if not issubclass(p.annotation, ABC):
                    raise ValueError("Type of parameter {} is not an interface".format(n))

                instance = self.create_instance_of_interface(p.annotation, scope)
                args[n] = instance

        return clazz(**args)

    def create_parameters(self, func, scope):
        params = {}
        sig = signature(func)
        for i, x in enumerate(sig.parameters.items()):
            n, p = x
            if (#i == 0 or
                p.kind == p.VAR_POSITIONAL or
                p.kind == p.VAR_KEYWORD
            ):
                continue

            if p.annotation is p.empty:
                raise ValueError("Type of parameter {} not specified".format(n))

            if issubclass(p.annotation, ABC):
                instance = self.create_instance_of_interface(p.annotation, scope)
            elif isclass(p.annotation):
                instance = self.create_instance_of_class(p.annotation, scope)
            else:
                raise ValueError("Type of parameter {} is not an interface or class".format(n))

            params[n] = instance

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
    return class_decorator(interfaces, container, lambda cont, iface, cls: cont.add_scoped_class(iface, cls))


def transient(interfaces=None, container=None):
    return class_decorator(interfaces, container, lambda cont, iface, cls: cont.add_transient_class(iface, cls))


def singleton(interfaces=None, container=None):
    return class_decorator(interfaces, container, lambda cont, iface, cls: cont.add_singleton_class(iface, cls))


def class_decorator(interfaces, container, register):
    return functools.partial(class_wrapper, interfaces, container, register)


def class_wrapper(interfaces, container, register, cls):
    c = container or _container
    if interfaces:
        for i in interfaces:
            register(c, i, cls)
    else:
        interface = cls.__bases__[0]
        register(c, interface, cls)
    
    return cls


def inject(scope=None, container=None):

    def decorator(func):

        def wrapper(*args, **kwargs):
            s = scope or Scope()
            c = container or _container
            params = c.create_parameters(func, s)
            params.update(kwargs)
            return func(*args, **params)

        return wrapper

    return decorator
