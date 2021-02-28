import abc

from .dependency_injector import Container, inject, scoped, singleton, transient


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
    def __init__(self, repository: Repository):
        self.repository = repository

    def create_message(self):
        return (self.repository.get_next_id(), "lorem ipsum")


def test_scoped():
    container = Container()
    scoped(container=container)(TestRepository)
    scoped(container=container)(TestService)

    @inject([Repository, Service], container=container)
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

    @inject([Repository, Service], container=container)
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

    @inject([Repository, Service], container=container)
    def test_scope1(repository: Repository, service: Service):
        return repository, service

    @inject([Repository, Service], container=container)
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
