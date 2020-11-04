#!/bin/bash

set -e
set -x

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    PYENV_ROOT="$HOME/.pyenv-gitchangelog"
    PATH="$PYENV_ROOT/bin:$PATH"
    hash -r
    eval "$(pyenv init -)"
fi

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    python3 -m nose -sx .
    python3 setup.py bdist_wheel
fi

if [[ $BUILD_WHEEL == 'true' ]]; then
    cibuildwheel --output-dir dist
fi

if [[ $BUILD_SDIST == 'true' ]]; then
    python3 setup.py sdist
fi
