# -*- encoding: utf-8 -*-
"""

Each tests should start in an empty directory that will be destroyed at the end.



"""

from __future__ import unicode_literals

import unittest
import tempfile
import os
import os.path
import shutil
import re

import gitchangelog


def raw_renderer(data, opts):
    return data


def set_env(key, value):

    def decorator(f):

        def _wrapped(*args, **kwargs):
            kwargs["env"] = dict(kwargs.get("env") or os.environ)
            kwargs["env"][key] = value
            return f(*args, **kwargs)
        return _wrapped
    return decorator

tprog = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..", "gitchangelog.py")

w = set_env("tprog", tprog)(gitchangelog.wrap)
cmd = set_env("tprog", tprog)(gitchangelog.cmd)


class ExtendedTestCase(unittest.TestCase):

    def assertContains(self, haystack, needle, msg=None):
        if not msg:
            msg = "%r should contain %r." % (haystack, needle)
        self.assertTrue(needle in haystack, msg)

    def assertNotContains(self, haystack, needle, msg=None):
        if not msg:
            msg = "%r should not contain %r." % (haystack, needle)
        self.assertTrue(needle not in haystack, msg)

    def assertRegex(self, text, regex, msg=None):
        if not msg:
            msg = "%r should match regex %r." % (text, regex)
        self.assertTrue(re.search(regex, text, re.MULTILINE) is not None, msg)


class BaseTmpDirTest(ExtendedTestCase):

    def setUp(self):
        ## put an empty tmp directory up
        self.old_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        ## put an empty tmp directory up
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)


class BaseGitReposTest(BaseTmpDirTest):
    """Base for all tests needing to start in a new git small repository"""

    REFERENCE = r"""Changelog
=========

%%version%% (unreleased)
------------------------

Changes
~~~~~~~

- Modified ``b`` XXX. [Alice]

0.0.3 (2000-01-05)
------------------

New
~~~

- Add file ``e``, modified ``b`` [Bob]

- Add file ``c`` [Charly]

0.0.2 (2000-01-02)
------------------

New
~~~

- Add ``b`` with non-ascii chars éèàâ§µ. [Alice]


"""

    def setUp(self):
        super(BaseGitReposTest, self).setUp()
        ## offer $tprog ENVIRON variable to call the test program

        w(r"""

            ## Creating repository
            mkdir repos
            cd repos
            git init .

            git config user.email "committer@example.com"
            git config user.name "The Committer"

            ## Adding first file
            echo 'Hello' > a
            git add a
            git commit -m 'new: first commit' \
                --author 'Bob <bob@example.com>' \
                --date '2000-01-01 10:00:00'
            git tag 0.0.1

            ## Adding second file
            echo 'Second file with strange non-ascii char: éèàâ§µ' > b
            git add b
            git commit -m 'new: add ``b`` with non-ascii chars éèàâ§µ' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-02 11:00:00'
            git tag 0.0.2

            ## Adding more files
            echo 'Third file' > c
            git add c
            git commit -m 'new: add file ``c``' \
                --author 'Charly <charly@example.com>' \
                --date '2000-01-03 12:00:00'
            echo 'Fourth file' > d
            echo 'With a modification' >> b
            git add d b
            git commit -m 'new: add file ``e``, modified ``b``' \
                --author 'Bob <bob@example.com>' \
                --date '2000-01-04 13:00:00'

            echo 'minor addition 1' >> b
            git commit -am 'chg: modified ``b`` !minor' \
                --author 'Bob <bob@example.com>' \
                --date '2000-01-05 13:00:00'
            git tag 0.0.3

            ## Add untagged commits
            echo 'addition' >> b
            git commit -am 'chg: modified ``b`` XXX' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-06 11:00:00'

            """)
        os.chdir("repos")

        self.repos = gitchangelog.GitRepos(os.getcwd())

    @property
    def raw_changelog(self):
        ## Currifyed main function
        return lambda *a, **kw: gitchangelog.changelog(
            self.repos, *a, output_engine=raw_renderer, **kw)


class GitChangelogTestCase(BaseGitReposTest, ExtendedTestCase):
    pass
