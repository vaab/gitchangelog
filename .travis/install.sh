#!/bin/bash

set -e
set -x

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    if [ ! -e "$HOME/.pyenv-gitchangelog/.git" ]; then
      if [ -e "$HOME/.pyenv-gitchangelog" ]; then
        rm -rf ~/.pyenv-gitchangelog
      fi
      git clone https://github.com/pyenv/pyenv.git ~/.pyenv-gitchangelog
    else
      (cd ~/.pyenv-gitchangelog; git pull)
    fi
    PYENV_ROOT="$HOME/.pyenv-gitchangelog"
    PATH="$PYENV_ROOT/bin:$PATH"
    hash -r
    eval "$(pyenv init -)"
    hash -r
    pyenv install --list
    pyenv install -s $PYENV_VERSION
    pip3 install wheel
    pip3 install --user .[test,ci]
fi

if [[ $BUILD_WHEEL == 'true' ]]; then
    pip install wheel cibuildwheel==1.5.2
fi
