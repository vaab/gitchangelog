from setuptools import setup, find_packages

import glob

import sys, os.path
## Ensure that ``./autogen.sh`` is run prior to using ``setup.py``
if "%%short-version%%".startswith("%%"):
    import os, subprocess
    if not os.path.exists('./autogen.sh'):
        sys.stderr.write(
            "This source repository was not configured.\n"
            "Please ensure ``./autogen.sh`` exists and that you are running "
            "``setup.py`` from the project root directory.\n")
        sys.exit(1)
    if os.path.exists('.autogen.sh.output'):
        sys.stderr.write(
            "It seems that ``./autogen.sh`` couldn't do its job as expected.\n"
            "Please try to launch ``./autogen.sh`` manualy, and send the results to "
            "the\nmaintainer of this package.\n"
            "Package will not be installed !\n")
        sys.exit(1)
    sys.stderr.write("Missing version information: running './autogen.sh'...\n")
    os.system('./autogen.sh > .autogen.sh.output')
    cmdline = sys.argv[:]
    if cmdline[1] == "install":
        ## XXXvlab: for some reason, this is needed when launched from pip
        if cmdline[0] == "-c":
            cmdline[0] = "setup.py"
        errlvl = subprocess.call(["python", ] + cmdline)
        os.unlink(".autogen.sh.output")
        sys.exit(errlvl)

description_files = [
    'README.rst',
    'CHANGELOG.rst',
    'TODO.rst',
]

long_description = '\n\n'.join(open(f).read()
                               for f in description_files
                               if os.path.exists(f))

## XXXvlab: Hacking distutils, not very elegant, but the only way I found
## to get data files to get copied next to the colour.py file...
## Any suggestions are welcome.
from distutils.command.install import INSTALL_SCHEMES
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

setup(
    name='gitchangelog',
    version='%%version%%',
    description='gitchangelog generates a changelog thanks to git log.',
    data_files=[
      ('', ['gitchangelog.rc.reference', ]),
      ('templates/mustache', glob.glob("templates/mustache/*.tpl")),
      ('templates/mako', glob.glob("templates/mako/*.tpl")),
    ],
    long_description=long_description,
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
    ],
    extras_require={
        'Mustache': ["pystache", ],
        'Mako': ["mako", ],
        'test': [
            "nose",
            "minimock",
            "mako",
            "pystache",
        ],
    },
    entry_points="""
    [console_scripts]
    gitchangelog = gitchangelog:main
    """,
)
