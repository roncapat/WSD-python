from setuptools import setup, find_packages
import os

setup(
    name='PyWSD',
    version='0.21',
    package_dir={'': "src"},
    packages=['PyWSD'],
    python_requires='>=3.6',
    install_requires=["argparse", "uuid", "lxml", "requests", "Pillow", "python-dateutil", "sphinx_rtd_theme", "urllib3"],
    url='https://github.com/roncapat/WSD-python',
    license='GPL v3.0',
    author='Patrick Roncagliolo',
    author_email='ronca.pat@gmail.com',
    description='A library for Web Services for Devices support',
    package_data={'PyWSD': ["templates/*.xml"]},
    scripts=['src/bin/wsdtool']
)
