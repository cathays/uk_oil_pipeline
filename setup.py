from setuptools import setup, find_packages

setup(
    name="uk_oil_pipeline",
    packages=["uk_oil_pipeline"],
    requires=['pandas', 'bs4', 'lxml', 'openpyxl'],
    entry_points={
        "console_scripts": [
            "runetl = uk_oil_pipeline.__main__:main",
        ]
    }
)