from setuptools import setup, find_packages

setup(
    name="diarium-cli",
    version="0.1",
    description="CLI tool for journaling app Diarium",
    author="Yelov",
    packages=find_packages(),
    include_package_date=True,
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points="""
        [console_scripts]
        diarium-cli=src.main:cli
    """,
)
