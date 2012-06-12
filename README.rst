=============
git-changelog
=============

Translate commit message history to a changelog.

Feature
=======

  - fully driven by a small configuration file to match with your changelog
    policies. (see for example the `sample configuration file`_)

  - ignore commit message based on regexp matching

  - refactor commit message displayed on the fly with replace regexp

  - classify commit message into sections (ie: New, Fix, Changes...)

  - ignore non-changelog tags by regexps


Sample
======

The output is currently fixed to ReSTructured text, but it should be readable
is ASCII.

Here is a small sample of the ``git-changelog`` changelog at work.

Current ``git log`` output so you can get an idea of the log history::

  * 59f902a Valentin Lab new: dev: sections in changelog are now in the order given in ``git-changelog.rc`` in the ``section_regexps`` option.  (0.1.2)
  * c6f72cc Valentin Lab chg: dev: commented code to toggle doctest mode.
  * a9c38f3 Valentin Lab fix: dev: doctests were failing on this.
  * 59524e6 Valentin Lab new: usr: added ``body_split_regexp`` option to attempts to format correctly body of commit.
  * 5883f07 Valentin Lab new: usr: use a list of tuple instead of a dict for ``section_regexps`` to be able to manage order between section on find match.
  * 7c1d480 Valentin Lab new: dev: new ``unreleased_version_label`` option in ``git-changelog.rc`` to change label of not yet released code.
  * cf29c9c Valentin Lab fix: dev: bad sorting of tags (alphanumerical). Changed to commit date sort.
  * 61d8f80 Valentin Lab fix: dev: support of empty commit message.
  * eeca31b Valentin Lab new: dev: use ``git-changelog`` section in ``git config`` world appropriately.
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

  - New ``unreleased_version_label`` option in ``git-changelog.rc`` to
    change label of not yet released code. [Valentin Lab]

  - Use ``git-changelog`` section in ``git config`` world appropriately.
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

The `sample configuration file`_ is quite heavily commented and is quite
simple.  You should be able to use it as required.

.. _sample configuration file: http://github.com/vaab/gitchangelog/blob/master/gitchangelog.rc.sample

The changelog of gitchangelog is generated with himself and with the sample
configuration file. You'll see the output in the `changelog of the PyPI page`_.

.. _changelog of the PyPI page: http://pypi.python.org/pypi/gitchangelog



What is not (yet) configurable
==============================

The output is in ReSTructured text, and this is not configurable. This could be
easily implemented by using a template driven content generation.

