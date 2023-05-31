from setuptools import setup

setup(
    name='pygrab',
    version='0.1.0',
    description='A secure python library for fetching data with async support',
    author='Anish Kanthamneni',
    author_email='akneni@gmail.com',
    packages=['pygrab'],
    install_requires=[
        'requests',
        'pyppeteer',
    ],
)
