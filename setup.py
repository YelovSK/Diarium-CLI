from setuptools import setup, find_packages


def read_requirements():
    with open("requirements.txt") as req:
        return req.read().split("\n")


setup(
    name="diarium-cli",
    version="0.1",
    author="Yelov",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_date=True,
    install_requires=read_requirements(),
    entry_points="""
        [console_scripts]
        diarium-cli=main:cli
    """,
)
