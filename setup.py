from distribute_setup import use_setuptools
use_setuptools()
from setuptools import setup

setup(
    name='PyReddit',
    author='Thomas Neyland',
    version='0.1.1dev',
    packages=['pyreddit', ],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.txt').read(),
    install_requires=['mechanize'],
)
