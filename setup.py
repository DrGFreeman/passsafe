from pathlib import Path
from setuptools import setup

NAME = 'passsafe'
VERSION = '0.1.0'

install_requires = [
    'cryptography',
    'flask',
    'pyotp',
    'requests',
    'waitress'
]

data = list(Path.cwd().joinpath(NAME).glob('*.txt'))

setup(
    name=NAME,
    version=VERSION,
    description="A client-server app to safely handle a password in "
                "applications.",
    author='Julien de la Bruère-Terreault',
    author_email='drgfreeman@tuta.io',
    url='https://github.com/DrGFreeman/passsafe',
    license='MIT',
    python_requires='>=3.6',
    install_requires=install_requires,
    packages=['passsafe'],
    entry_points={
        'console_scripts': ['passsafe=passsafe.server:run']
    },
    package_data={NAME: data},
)
