from setuptools import setup, find_packages

setup(
    name='DFSSYS',
    version='1.0.0',
    url='',
    license='UNKNOWN',
    author='Ankit',
    author_email='ankitvermajnp@gmail.com',
    description='Distributed discovery and data sharing system',
    packages=find_packages(),
    install_requires=['PyQt5'],
    entry_points={
        'console_scripts': [
            'dfssys=DFSSYS.user:main'
        ]
    }
)
