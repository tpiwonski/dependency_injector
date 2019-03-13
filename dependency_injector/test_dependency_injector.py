import pytest
import abc
import uuid

from .dependency_injector import Container, Scope, inject, scoped, transient, singleton


class Repository(abc.ABC):
    
    @abc.abstractmethod
    def get_next_id(self):
        """get_next_id"""


class TestRepository(Repository):
    
    def __init__(self):
        self._id = 0

    def get_next_id(self):
        self._id += 1
        return self._id


class Service(abc.ABC):
    
    @abc.abstractmethod
    def create_message(self):
        """create_object"""


class TestService(Service):
    
    def __init__(self, repository : Repository):
        self.repository = repository

    def create_message(self):
        return (self.repository.get_next_id(), "lorem ipsum")


def test_scoped():
    container = Container()
    scoped(container=container)(TestRepository)
    scoped(container=container)(TestService)

    @inject(container=container)
    def test_scope(repository: Repository, service: Service):
        return repository, service

    repository, service = test_scope()

    assert isinstance(repository, TestRepository)
    assert isinstance(service, TestService)
    assert isinstance(service.repository, TestRepository)
    assert repository == service.repository


def test_transient():
    container = Container()
    transient(container=container)(TestRepository)
    scoped(container=container)(TestService)

    @inject(container=container)
    def test_scope(repository: Repository, service: Service):
        return repository, service

    repository, service = test_scope()

    assert isinstance(repository, TestRepository)
    assert isinstance(service, TestService)
    assert isinstance(service.repository, TestRepository)
    assert repository != service.repository


def test_singleton():
    container = Container()
    singleton(container=container)(TestRepository)
    singleton(container=container)(TestService)

    @inject(container=container)
    def test_scope1(repository: Repository, service: Service):
        return repository, service

    @inject(container=container)
    def test_scope2(repository: Repository, service: Service):
        return repository, service

    repository1, service1 = test_scope1()
    repository2, service2 = test_scope2()

    assert isinstance(repository1, TestRepository)
    assert isinstance(repository2, TestRepository)
    assert isinstance(service1, TestService)
    assert isinstance(service2, TestService)
    assert isinstance(service1.repository, TestRepository)
    assert isinstance(service2.repository, TestRepository)
    assert repository1 == service1.repository
    assert repository2 == service2.repository
    assert repository1 == repository2

# def test_singleton():
#     container = Container()
#     container.add_singleton_class(Repository, MemoryRepository)

#     scope = Scope()
#     repository1 = container.create_instance_of_interface(Repository, scope)
#     repository2 = container.create_instance_of_interface(Repository, scope)

#     assert isinstance(repository1, MemoryRepository)
#     assert isinstance(repository2, MemoryRepository)
#     assert repository1 == repository2

# def test_boo():
#     container = Container()
#     container.add_singleton_class(Repository, MemoryRepository)
#     container.add_singleton_class(MessageService, TextMessageService)

#     scope = Scope()
#     service = container.create_instance_of_interface(MessageService, scope)

#     assert isinstance(service, TextMessageService)
#     assert isinstance(service._repository, MemoryRepository)

# def test_transient_xxx():
#     container = Container()
#     container.add_transient_class(Repository, MemoryRepository)
#     container.add_transient_class(MessageService, TextMessageService)

#     scope = Scope()
#     service1 = container.create_instance_of_interface(MessageService, scope)
#     service2 = container.create_instance_of_interface(MessageService, scope)

#     message1 = service1.create_message()
#     message2 = service2.create_message()

#     assert service1 != service2
#     assert service1._repository != service2._repository
#     assert message1 == message2
