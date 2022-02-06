from setuptools import setup, find_packages

setup(
    name="diarium-cli",
    version="0.1.1",
    description="CLI tool for journaling app Diarium",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Yelov",
    packages=find_packages(),
    include_package_date=True,
    install_requires=open("requirements.txt").read().splitlines(),
    license="Apache License 2.0",
    entry_points="""
        [console_scripts]
        diarium-cli=src.main:cli
    """,
)
