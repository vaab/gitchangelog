============
gitchangelog
============

.. image:: https://pypip.in/v/gitchangelog/badge.png
    :target: https://pypi.python.org/pypi/gitchangelog

.. image:: https://secure.travis-ci.org/vaab/gitchangelog.png?branch=master
    :target: http://travis-ci.org/vaab/gitchangelog


Translate commit message history to a changelog.


Feature
=======

  - fully driven by a small configuration file to match with your changelog
    policies. (see for example the `sample configuration file`_)

  - ignore commit message based on regexp matching

  - refactor commit message displayed on the fly with replace regexp

  - classify commit message into sections (ie: New, Fix, Changes...)

  - ignore non-changelog tags by regexps

  - templating system for easy tailoring your output (markdown, ReST, etc)


Requirements
============

Each commit are tested regularly on Python 2.7 and Python 3.2.

It should work on Linux/BSD/MacOSX and it should work under cygwin on Windows.

Please submit an issue if you encounter incompatibilies.


Sample
======

The default output is ReSTructured text, so it should be readable in ASCII.

Here is a small sample of the ``gitchangelog`` changelog at work.

Current ``git log`` output so you can get an idea of the log history::

  * 59f902a Valentin Lab new: dev: sections in changelog are now in the order given in ``gitchangelog.rc`` in the ``section_regexps`` option.  (0.1.2)
  * c6f72cc Valentin Lab chg: dev: commented code to toggle doctest mode.
  * a9c38f3 Valentin Lab fix: dev: doctests were failing on this.
  * 59524e6 Valentin Lab new: usr: added ``body_split_regexp`` option to attempts to format correctly body of commit.
  * 5883f07 Valentin Lab new: usr: use a list of tuple instead of a dict for ``section_regexps`` to be able to manage order between section on find match.
  * 7c1d480 Valentin Lab new: dev: new ``unreleased_version_label`` option in ``gitchangelog.rc`` to change label of not yet released code.
  * cf29c9c Valentin Lab fix: dev: bad sorting of tags (alphanumerical). Changed to commit date sort.
  * 61d8f80 Valentin Lab fix: dev: support of empty commit message.
  * eeca31b Valentin Lab new: dev: use ``gitchangelog`` section in ``git config`` world appropriately.
  * 6142b71 Valentin Lab chg: dev: cosmetic removal of trailing whitespaces
  * 3c3edd5 Valentin Lab fix: usr: ``git`` in later versions seems to fail on ``git config <key>`` with errlvl 255, that was not supported.
  * 3f9617d Valentin Lab fix: usr: removed Traceback when there were no tags at all in the current git repository.
  * e0db9ae Valentin Lab new: usr: added section classifiers (ie: New, Change, Bugs) and updated the sample rc file.  (0.1.1)
  * 0c66d59 Valentin Lab fix: dev: Fixed case where exception was thrown if two tags are on the same commit.
  * d2fae0d Valentin Lab new: usr: added a succint ``--help`` support.

And here is the ``gitchangelog`` output::

  0.1.2 (2011-05-17)
  ------------------

  New
  ~~~

  - Sections in changelog are now in the order given in ``git-
    changelog.rc`` in the ``section_regexps`` option. [Valentin Lab]

  - Added ``body_split_regexp`` option to attempts to format correctly
    body of commit. [Valentin Lab]

  - Use a list of tuple instead of a dict for ``section_regexps`` to be
    able to manage order between section on find match. [Valentin Lab]

  - New ``unreleased_version_label`` option in ``gitchangelog.rc`` to
    change label of not yet released code. [Valentin Lab]

  - Use ``gitchangelog`` section in ``git config`` world appropriately.
    [Valentin Lab]

  Changes
  ~~~~~~~

  - Commented code to toggle doctest mode. [Valentin Lab]

  - Cosmetic removal of trailing whitespaces. [Valentin Lab]

  Fix
  ~~~

  - Doctests were failing on this. [Valentin Lab]

  - Bad sorting of tags (alphanumerical). Changed to commit date sort.
    [Valentin Lab]

  - Support of empty commit message. [Valentin Lab]

  - ``git`` in later versions seems to fail on ``git config <key>`` with
    errlvl 255, that was not supported. [Valentin Lab]

  - Removed Traceback when there were no tags at all in the current git
    repository. [Valentin Lab]

  0.1.1 (2011-04-07)
  ------------------

  New
  ~~~

  - Added section classifiers (ie: New, Change, Bugs) and updated the
    sample rc file. [Valentin Lab]

  - Added a succint ``--help`` support. [Valentin Lab]

  Fix
  ~~~

  - Fixed case where exception was thrown if two tags are on the same
    commit. [Valentin Lab]

And the rendered full result is directly used to generate the HTML webpage of
the `changelog of the PyPI page`_.


Usage
=====

You need to place a ``gitchangelog.rc`` file somewhere, these are the location
checked in the given order (first match will prevail):

  - in the path given thanks to the environment variable
    ``GITCHANGELOG_CONFIG_FILENAME``

  - in the path stored in git config's entry "gitchangelog.rc-path" (which
    could be stored in system location or per repository)

  - in the root of the current git repository with the name ``.gitchangelog.rc``

Then, you'll be able to call ``gitchangelog`` in a GIT repository and it'll
print changelog as its standard output.


Configuration file format
-------------------------

The `sample configuration file`_ is quite heavily commented and is quite
simple.  You should be able to use it as required.

.. _sample configuration file: http://github.com/vaab/gitchangelog/blob/master/gitchangelog.rc.reference

The changelog of gitchangelog is generated with himself and with the sample
configuration file. You'll see the output in the `changelog of the PyPI page`_.

.. _changelog of the PyPI page: http://pypi.python.org/pypi/gitchangelog


Output Engines
--------------

At the end of the configuration file, you'll notice a variable called
``output_engine``. By default, it's set to ``rest_py``, which is the
legacy python engine to produce the `ReSTructured Text` output format
that is shown in above samples. If this engine fits your needs, you
won't need to fiddle with this option.

To render the template, ``gitchangelog`` will generate a data structure that
will then be rendered thanks to the output engine. This should help you get
the exact output that you need.

As people might have different needs and knowledge, a templating
system using ``mustache`` is available. ``mustache`` templates are
provided to render both `ReSTructured Text` or `markdown` formats. If
you know ``mustache`` templating, then you could easily add or modify
these existing templates.

A ``mako`` templating engine is also provided. You'll find also a ``mako``
template producing the same `ReSTructured Text` output than the legacy one.
It's provided for reference and/or further tweak if you would rather use `mako`_
templates.


Mustache
~~~~~~~~

The ``mustache``  output engine uses `mustache templates`_.

The `mustache`_ templates for ``gitchangelog`` are located in
``templates/mustache`` and are powered via `pystache`_ the python
implementation of the `mustache`_ specifications. So `mustache`_ output engine
will only be available if you have `pystache`_ module available in your python
environment.

.. _mustache: http://mustache.github.io
.. _pystache: https://pypi.python.org/pypi/pystache
.. _mustache templates: http://mustache.github.io/mustache.5.html


Mako
~~~~

The ``makotemplate`` output engine templates for ``gitchangelog`` are located in
``templates/mako`` and are powered via `mako`_ python templating system. So
`mako`_ output engine will only be available if you have `mako`_ module
available in your python environment.

.. _mako: http://www.makotemplates.org


Changelog data tree
~~~~~~~~~~~~~~~~~~~

This is a sample of the current data structure sent to output engines::

  {'title': 'Changelog',
   'versions': [{'label': '%%version%% (unreleased)',
                 'date': None,
                 'tag': None
                 'sections': [{'label': 'Changes',
                               'commits': [{'author': 'John doe',
                                            'body': '',
                                            'subject': 'Adding some extra values.'},
                                           {'author': 'John Doe',
                                            'body': '',
                                            'subject': 'Some more changes'}]},
                              {'label': 'Other',
                               'commits': [{'author': 'Jim Foo',
                                            'body': '',
                                            'subject': 'classic modification'},
                                           {'author': 'Jane Done',
                                            'body': '',
                                            'subject': 'Adding some stuff to do.'}]}]},
                {'label': 'v0.2.5 (2013-08-06)',
                 'date': '2013-08-06',
                 'tag': 'v0.2.5'
                 'sections': [{'commits': [{'author': 'John Doe',
                                            'body': '',
                                            'subject': 'Updating Changelog installation.'}],
                               'label': 'Changes'}]}]}
