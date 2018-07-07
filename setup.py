from setuptools import setup, find_packages


with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name='campbot',
    version="0.4.2",
    packages=find_packages(),
    author="Charles de Beauchesne",
    author_email="charles.de.beauchesne@gmail.com",
    description="Package for automatic edition of camptocamp.org",
    long_description=open('README.txt').read(),
    install_requires=install_requires,
    include_package_data=True,

    url='http://gitlab.com/cbeauchesne/CampBot',

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
