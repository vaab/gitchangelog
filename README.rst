git-changelog
=============

Translate commit message history to a changelog.

Feature
-------

    -  fully driven by a small configuration file to match with your
       changelog policies. (see for example the `sample configuration
       file <http://github.com/vaab/gitchangelog/blob/master/gitchangelog.rc.sample>`__)

    -  ignore commit message based on regexp matching

    -  refactor commit message displayed on the fly with replace regexp

    -  classify commit message into sections (ie: New, Fix, Changes...)

    -  ignore non-changelog tags by regexps

    -  templates for different types of output (markdown, ReST, etc)

Sample
------

The output is currently fixed to ReSTructured text, but it should be readable is ASCII.

Here is a small sample of the ``git-changelog`` changelog at work.

Current ``git log`` output so you can get an idea of the log history:

::

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

And here is the ``gitchangelog`` output (in ReST format):

::

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

And the rendered full result is directly used to generate the HTML webpage of the `changelog of the PyPI page <http://pypi.python.org/pypi/gitchangelog>`__.

Usage
-----

The `sample configuration
file <http://github.com/vaab/gitchangelog/blob/master/gitchangelog.rc.sample>`__ is quite heavily commented and is quite simple. You should be able to use it as required.

The changelog of gitchangelog is generated with himself and with the sample configuration file. You'll see the output in the `changelog of the PyPI page <http://pypi.python.org/pypi/gitchangelog>`__.

Templating system
-----------------

The output can be provided in different format. For the moment Markdown and ReSTructured text are supported.

The templates are located in ``share/templates`` are implemented thanks to ```pystache`` <https://pypi.python.org/pypi/pystache>`__ the python implementation of the `mustache <http://mustache.github.io/>`__ specifications.

gitchangelog is constructing a data tree holding the elements that will be used to render the changelog using the provided templates.

If you want more information about mustache & pystache:

-  mustache web site: http://mustache.github.io/
-  mustache(5) man page: http://mustache.github.io/mustache.5.html
-  pystache web site: https://pypi.python.org/pypi/pystache

Changelog data tree
~~~~~~~~~~~~~~~~~~~

To render the template, gitchangelog is generating a data tree that will then be used with the template to create the changelog.

Here is the structure of the changelog data tree:

::

    {
        "title": "Changelog",
        "title_under": [
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-"
        ],
        "versions": [
            {
                "params": {
                    "date": "(unreleased)",
                    "tag": "%%version%%"
                },
                "sections": [
                    {
                        "commits": [
                            {
                                "author": "John doe",
                                "body": "",
                                "content": "Adding some extra values.",
                                "has_body": false
                            },
                            {
                                "author": "John Doe",
                                "body": "",
                                "content": "Some more changes",
                                "has_body": false
                            }
                        ],
                        "section_title": "Changes :",
                        "section_under": [
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-"
                        ],
                        "type": "Changes"
                    },
                    {
                        "commits": [
                            {
                                "author": "Jim Foo",
                                "body": "",
                                "content": "classic modification",
                                "has_body": false
                            },
                            {
                                "author": "Jane Done",
                                "body": "",
                                "content": "Adding some stuff to do.",
                                "has_body": false
                            }
                        ],
                        "section_title": "Other :",
                        "section_under": [
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-"
                        ],
                        "type": "Other"
                    }
                ],
                "version_title": "%%version%% (unreleased)",
                "version_under": [
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-"
                ]
            },
            {
                "params": {
                    "date": "2013-08-06",
                    "tag": "v0.2.5"
                },
                "sections": [
                    {
                        "commits": [
                            {
                                "author": "John Doe",
                                "body": "",
                                "content": "Updating Changelog installation.",
                                "has_body": false
                            }
                        ],
                        "section_title": "Changes :",
                        "section_under": [
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-",
                            "-"
                        ],
                        "type": "Changes"
                    }
                ],
                "version_title": "v0.2.5 (2013-08-06)",
                "version_under": [
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-"
                ]
            }
        ]
    }

Using the ReSTructured text template, the generate template will be :

::

    Changelog
    ---------

    ### %%version%% (unreleased)

    #### Changes :

    -   Adding some extra values. [John doe]

    -   Some more changes [John Doe]

    #### Other :

    -   classic modification [Jim Foo]

    -   Adding some stuff to do. [Jane Done]

    ### v0.2.5 (2013-08-06)

    #### Changes :

    -   Updating Changelog installation. [John Doe]

