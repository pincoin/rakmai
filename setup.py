from setuptools import (
    setup, find_packages
)

from rakmai import (
    PROJECT, VERSION, AUTHOR
)

setup(
    name=PROJECT,
    version=VERSION,
    description='rakmai',
    url='http://github.com/pincoin/rakmai',
    author=AUTHOR,
    maintainer='rakmai maintainers',
    license='MIT',
    zip_safe=False,

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    packages=find_packages(exclude=['docs', 'tests']),

    install_requires=[
        'Django',
    ],
    setup_requires=[
    ],
    scripts=[
    ],

    tests_require=[
    ],
    test_suite='runtests.runtests',
),
