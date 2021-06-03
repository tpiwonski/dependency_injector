from setuptools import find_packages, setup


def read_description():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()


setup(
    name="dependency-injector",
    version="0.2",
    url="https://github.com/tpiwonski/dependency_injector",
    author="Tomasz Piwoński",
    # author_email='@gmail.com',
    description="Python dependency injection library",
    long_description=read_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={"dependency_injector": ["py.typed"]},
    zip_safe=False,
    include_package_data=True,
    install_requires=[],
)
