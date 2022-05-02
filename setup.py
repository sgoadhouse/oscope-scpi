# -*- coding: utf-8 -*-

#from distutils.core import setup
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(name="oscope_scpi", 
                 version='0.1.13',
                 description='Control of Oscilloscopes with SCPI command sets like Keysight MSO-X/DSO-X 3000A/3000T, UXR, MXR and EXR Series through python via PyVisa',
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 url='https://github.com/sgoadhouse/oscope-scpi',
                 author='Stephen Goadhouse', 
                 author_email="sgoadhouse@virginia.edu",
                 maintainer='Stephen Goadhouse',
                 maintainer_email="sgoadhouse@virginia.edu",
                 license='MIT',
                 keywords=['HP', 'Agilent', 'Keysight', 'MSO3000', 'MSOX3000', 'DSO3000', 'DSOX3000',
                           'MXR', 'MXR058A', 'EXR', 'UXR', 'UXR0334A', 'PyVISA', 'VISA', 'SCPI', 'INSTRUMENT'],
                 classifiers=[
                     'Development Status :: 4 - Beta',
                     'Intended Audience :: Developers',
                     'Intended Audience :: Education',
                     'Intended Audience :: Science/Research',
                     'License :: OSI Approved :: MIT License',
                     'Programming Language :: Python',
                     'Topic :: Scientific/Engineering',
                     'Topic :: Scientific/Engineering :: Physics',
                     'Topic :: Software Development',
                     'Topic :: Software Development :: Libraries',
                     'Topic :: Software Development :: Libraries :: Python Modules'], 
                 install_requires=[
                     'pyvisa>=1.11.3',
                     'pyvisa-py>=0.5.2',
                     'argparse',
                     'QuantiPhy>=2.3.0',
                     'numpy>=1.19.5; python_version>="3.8"',
                     'numpy==1.19.5; python_version<"3.8"'
                 ],
                 python_requires='>=3.6',
                 packages=setuptools.find_packages(),
                 include_package_data=True,
                 zip_safe=False
)
