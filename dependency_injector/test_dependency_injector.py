import abc
from dataclasses import dataclass

from .dependency_injector import (
    Container,
    inject,
    provide,
    scoped,
    singleton,
    transient,
)


class RepositoryInterface(abc.ABC):
    @abc.abstractmethod
    def get_next_id(self):
        """get_next_id"""


class RepositoryImplementation(RepositoryInterface):
    def __init__(self):
        self._id = 0

    def get_next_id(self):
        self._id += 1
        return self._id


class ServiceInterface(abc.ABC):
    @abc.abstractmethod
    def create_message(self):
        """create_object"""


@dataclass
class ServiceImplementation(ServiceInterface):
    repository: RepositoryInterface

    def create_message(self):
        return self.repository.get_next_id(), "lorem ipsum"


@dataclass
class ServiceImplementationWithoutInterface:
    other_service: ServiceInterface


def test_scoped():
    container = Container()
    scoped(container=container)(RepositoryImplementation)
    scoped(container=container)(ServiceImplementation)

    @inject([RepositoryInterface, ServiceInterface], container=container)
    def test_scope(repository: RepositoryInterface, service: ServiceInterface):
        return repository, service

    repository, service = test_scope()

    assert isinstance(repository, RepositoryImplementation)
    assert isinstance(service, ServiceImplementation)
    assert isinstance(service.repository, RepositoryImplementation)
    assert repository is service.repository


def test_transient():
    container = Container()
    transient(container=container)(RepositoryImplementation)
    scoped(container=container)(ServiceImplementation)

    @inject([RepositoryInterface, ServiceInterface], container=container)
    def test_scope(repository: RepositoryInterface, service: ServiceInterface):
        return repository, service

    repository, service = test_scope()

    assert isinstance(repository, RepositoryImplementation)
    assert isinstance(service, ServiceImplementation)
    assert isinstance(service.repository, RepositoryImplementation)
    assert repository is not service.repository


def test_singleton():
    container = Container()
    singleton(container=container)(RepositoryImplementation)
    singleton(container=container)(ServiceImplementation)

    @inject([RepositoryInterface, ServiceInterface], container=container)
    def test_scope1(repository: RepositoryInterface, service: ServiceInterface):
        return repository, service

    @inject([RepositoryInterface, ServiceInterface], container=container)
    def test_scope2(repository: RepositoryInterface, service: ServiceInterface):
        return repository, service

    repository1, service1 = test_scope1()
    repository2, service2 = test_scope2()

    assert isinstance(repository1, RepositoryImplementation)
    assert isinstance(repository2, RepositoryImplementation)
    assert isinstance(service1, ServiceImplementation)
    assert isinstance(service2, ServiceImplementation)
    assert isinstance(service1.repository, RepositoryImplementation)
    assert isinstance(service2.repository, RepositoryImplementation)
    assert repository1 is service1.repository
    assert repository2 is service2.repository
    assert repository1 is repository2


def test_scoped_without_interface():
    container = Container()
    scoped(container=container)(RepositoryImplementation)
    scoped(container=container)(ServiceImplementation)
    scoped(container=container)(ServiceImplementationWithoutInterface)

    @inject([ServiceImplementationWithoutInterface], container=container)
    def test_scope(other_service: ServiceImplementationWithoutInterface):
        return other_service

    service = test_scope()

    assert isinstance(service, ServiceImplementationWithoutInterface)
    assert isinstance(service.other_service, ServiceImplementation)
    assert isinstance(service.other_service.repository, RepositoryImplementation)


def test_provide_instances():
    container = Container()
    scoped(container=container)(RepositoryImplementation)
    scoped(container=container)(ServiceImplementation)
    scoped(container=container)(ServiceImplementationWithoutInterface)

    services = provide([ServiceImplementationWithoutInterface], container=container)
    service = services[ServiceImplementationWithoutInterface]

    assert isinstance(service, ServiceImplementationWithoutInterface)
    assert isinstance(service.other_service, ServiceImplementation)
    assert isinstance(service.other_service.repository, RepositoryImplementation)
