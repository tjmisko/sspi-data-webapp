from setuptools import setup, find_packages

setup(
    name='sspi',
    version='0.1',
    packages=find_packages(),
    install_requires=['click', 'flask', 'flask_login'],
    entry_points={
        'console_scripts': [
            'sspi = cli.cli:cli'
        ],
    }
)
