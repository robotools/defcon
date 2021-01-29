#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

needs_sphinx = {'build_sphinx', 'dist'}.intersection(sys.argv)
sphinx = ['sphinx'] if needs_sphinx else []
needs_pytest = {'pytest', 'test'}.intersection(sys.argv)
pytest_runner = ['pytest_runner'] if needs_pytest else []
needs_wheel = {'bdist_wheel'}.intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []

with open('README.rst', 'r') as f:
    long_description = f.read()

setup_params = dict(
    name="defcon",
    description="A set of flexible objects for representing UFO data.",
    long_description=long_description,
    author="Tal Leming",
    author_email="tal@typesupply.com",
    url="https://github.com/robotools/defcon",
    license="MIT",
    package_dir={"": "Lib"},
    packages=find_packages("Lib"),
    include_package_data=True,
    use_scm_version={
          "write_to": 'Lib/defcon/_version.py',
          "write_to_template": '__version__ = "{version}"',
     },
    setup_requires=pytest_runner + sphinx + wheel + ['setuptools_scm'],
    tests_require=[
        'pytest>=3.0.3',
    ],
    install_requires=[
        "fonttools[ufo,unicode] >= 4.10.0",
    ],
    extras_require={
        'pens': ["fontPens>=0.1.0"],
        'lxml': ["fonttools[lxml] >= 4.10.0"],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Graphics :: Editors :: Vector-Based',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.6',
    zip_safe=True,
)


if __name__ == "__main__":
    setup(**setup_params)
