from setuptools import setup

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pygrab',
    version='1.1.4',
    description='A secure python library for fetching data with async support',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Anish Kanthamneni',
    author_email='akneni@gmail.com',
    packages=['pygrab'],
    install_requires=[
        'requests',
        'pyppeteer',
    ],
)
