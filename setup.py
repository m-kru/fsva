from setuptools import setup

from fsva import version


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='fsva',
    version=version.version,
    description="fsva (FuseSoc Verification Automation)",
    long_description=readme(),
    classifiers=[
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Utilities",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
    ],
    keywords = [
        'verification',
        'simulation',
        'testbench',
        'FuseSoc',
        'VHDL',
        'SystemVerilog',
        'UVVM',
        'OSVVM',
        'GHDL',
        'Questa',
        'HDL',
        'RTL',
        'FPGA',
    ],
    url="https://github.com/m-kru/fsva",
    author="Michał Kruszewski",
    author_email="mkru@protonmail.com",
    license="MIT",
    install_requires=[
        'fusesoc>=1.9.1'
    ],
    entry_points={
        'console_scripts' : [
            'fsva = fsva.main:main'
        ]
    }
)
