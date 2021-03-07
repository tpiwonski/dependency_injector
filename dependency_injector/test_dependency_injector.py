import abc
from dataclasses import dataclass

from .dependency_injector import Container, provide, scoped, singleton, transient


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
class ServiceWithoutInterface:
    test_service: ServiceInterface
    foo: int = 1


def test_scoped():
    container = Container()
    scoped(container=container)(RepositoryImplementation)
    scoped(container=container)(ServiceImplementation)

    @provide([RepositoryInterface, ServiceInterface], container=container)
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

    @provide([RepositoryInterface, ServiceInterface], container=container)
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

    @provide([RepositoryInterface, ServiceInterface], container=container)
    def test_scope1(repository: RepositoryInterface, service: ServiceInterface):
        return repository, service

    @provide([RepositoryInterface, ServiceInterface], container=container)
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


def test_scoped2():
    container = Container()
    scoped(container=container)(RepositoryImplementation)
    scoped(container=container)(ServiceImplementation)
    scoped(container=container)(ServiceWithoutInterface)

    @provide([ServiceWithoutInterface], container=container)
    def test_scope(other_service: ServiceWithoutInterface):
        return other_service

    other_service = test_scope()

    assert isinstance(other_service, ServiceWithoutInterface)
    assert isinstance(other_service.test_service, ServiceImplementation)
    assert isinstance(other_service.test_service.repository, RepositoryImplementation)
