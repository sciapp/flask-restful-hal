# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import os
import subprocess
from setuptools import setup, find_packages
from flask_restful_hal._version import __version__


def get_install_requires_from_requirements(requirements_filename='requirements.txt'):
    try:
        with codecs.open(requirements_filename, 'r', 'utf-8') as requirements_file:
            requirements = requirements_file.readlines()
    except OSError:
        import logging
        logging.warning('Could not read the requirements file.')
    return requirements


def get_long_description_from_readme(readme_filename='README.md'):
    rst_filename = '{}.rst'.format(os.path.splitext(os.path.basename(readme_filename))[0])
    created_tmp_rst = False
    if not os.path.isfile(rst_filename):
        try:
            subprocess.check_call(['pandoc', readme_filename, '-t', 'rst', '-o', rst_filename])
            created_tmp_rst = True
        except (OSError, subprocess.CalledProcessError):
            import logging
            logging.warning('Could not convert the readme file to rst.')
    long_description = None
    if os.path.isfile(rst_filename):
        with codecs.open(rst_filename, 'r', 'utf-8') as readme_file:
            long_description = readme_file.read()
    if created_tmp_rst:
        os.remove(rst_filename)
    return long_description


long_description = get_long_description_from_readme()
install_requires = get_install_requires_from_requirements()

setup(
    name='flask-restful-hal',
    version=__version__,
    packages=find_packages(),
    package_data={
        str(''): ['requirements.txt']  # setuptools needs byte strings as keys when running Python 2.x
    },
    install_requires=install_requires,
    author='Ingo Heimbach',
    author_email='i.heimbach@fz-juelich.de',
    description='HAL extension for Flask-RESTful',
    long_description=long_description,
    license='MIT',
    url='https://github.com/sciapp/flask-restful-hal',
    keywords=['Flask', 'RESTful', 'HAL'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
