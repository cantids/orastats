from setuptools import setup, find_packages
import re
import ast

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('orastats/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

install_requirements = [
            'cx-Oracle>=5.0.0'
            ]
description = 'oracle orastats'

setup(
    name='orastats',
    version='1.2',
    packages=find_packages(),
    url='https://github.com/travelliu/orastats.git',
    license='LICENSE.txt',
    author='Travel.Liu',
    author_email='travel.liu@outlook.com',
    description=description,
    long_description=open('README.md').read(),
	entry_points={'console_scripts':['orastats = orastats.main:run']}
)
