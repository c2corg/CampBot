from setuptools import setup, find_packages

import campbot

setup(
    name='campbot',
    version=campbot.__version__,
    packages=find_packages(),
    author="Charles de Beauchesne",
    author_email="charles.de.beauchesne@gmail.com",
    description="Package for automatic edition of camptocamp.org",
    long_description=open('README.md').read(),

    install_requires=[
        "docopt==0.6.2",
        "requests==2.18.4",
        "python-dateutil==2.6.1",
        "pytz==2017.2",
        "pytest",
        "pytest-cov",
    ],

    include_package_data=True,

    url='http://github.com/cbeauchesne/CampBot',

    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 1 - Planning",
        "License :: OSI Approved",
        "Natural Language :: French",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Topic :: Communications",
    ],

    entry_points={
        'console_scripts': [
            'campbot = campbot.__main__:main_entry_point',
        ],
    },

    license="WTFPL",

)
