from setuptools import setup

setup(
    name='WSD-python',
    version='0.1',
    packages=['PyWSD'],
    install_requires=["argparse", "uuid", "lxml", "requests", "Pillow", "python-dateutil"],
    url='https://github.com/roncapat/WSD-python',
    license='GPL v3.0',
    author='Patrick Roncagliolo',
    author_email='ronca.pat@gmail.com',
    description='A library for Web Services for Devices support'
)
