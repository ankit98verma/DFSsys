from setuptools import setup

setup(
    name='DDS',
    version='1.0.4',
    packages=['DDS'],
    url='https://github.com/ankit98verma/DFSsys',
    license='Caltech',
    author='Ankit',
    author_email='ankitvermajnp@gmail.com',
    description='Distributed discovery and data sharing system',
    install_requires=['PyQt5'],
    entry_points={
            'console_scripts': [
                'dds=DDS.user:main'
            ]
        }
)
