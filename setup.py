from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pygrab',
    version='3.0.1',
    description='A secure python library for fetching data with async, JS, and Tor support',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Anish Kanthamneni',
    author_email='akneni@gmail.com',
    packages=find_packages(),
    install_requires=[
        'requests',
        'pyppeteer',
        'nest_asyncio',
        'PySocks',
    ],
    package_data={
        'pygrab': ['rust_dependencies/*'],
    },
)
