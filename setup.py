from setuptools import setup, find_packages


with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

exec(open("campbot/version.py").read())


setup(
    name="campbot",
    version=__version__,
    packages=find_packages(),
    author="Charles de Beauchesne",
    author_email="charles.de.beauchesne@gmail.com",
    description="Package for automatic edition of camptocamp.org",
    long_description=open('README.txt').read(),
    install_requires=install_requires,
    python_requires=">=3.11",
    include_package_data=True,

    url="http://github.com/c2corg/CampBot",

    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Communications",
    ],

    entry_points={
        'console_scripts': [
            'campbot = campbot.__main__:main_entry_point',
        ],
    },

    license="WTFPL",

)
