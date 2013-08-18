from setuptools import setup, find_packages

import glob

print glob.glob("share/templates/*")

long_description = '\n\n'.join([open('README.rst').read(),
                                open('CHANGELOG.rst').read(),
                                open('TODO.rst').read()])


setup(
    name='gitchangelog',
    version='%%version%%',
    description='gitchangelog generates a changelog thanks to git log.',
    long_description=long_description,
    data_files=[
          ('share/templates', glob.glob("share/templates/*")),
          ],
    # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Programming Language :: Python",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development",
        "Topic :: Software Development :: Version Control",
        "Programming Language :: Python :: 2.5",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='sact git changelog',
    author='SecurActive SA',
    author_email='opensource@securactive.net',
    url='www.securactive.net',
    license='BSD License',
    py_modules=['gitchangelog'],
    namespace_packages=[],
    zip_safe=False,
    install_requires=[
        'setuptools',
        'pystache'
        # -*- Extra requirements: -*-
    ],
    entry_points="""
    [console_scripts]
    gitchangelog = gitchangelog:main
    """,
)
