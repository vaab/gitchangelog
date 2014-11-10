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


def simple_renderer(data, opts):
    """Provide a fixed template for tests.

    To use when checking what commits gets attributed to which
    versions/sections.

    Do not use if you want to check body contents as it is not printed.

    """
    s = ""
    for version in data["versions"]:
        s += "%s\n" % version["tag"]
        for section in version["sections"]:
            s += "  %s:\n" % section["label"]
            for commit in section["commits"]:
                s += "    * %(subject)s [%(author)s]\n" % commit
        s += "\n"
    return s


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


class ExtendedTest(unittest.TestCase):

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


class BaseTmpDirTest(ExtendedTest):

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

    def setUp(self):
        super(BaseGitReposTest, self).setUp()
        w(r"""

            ## Creating repository
            mkdir repos
            cd repos
            git init .

            git config user.email "committer@example.com"
            git config user.name "The Committer"

        """)
        os.chdir("repos")

        self.repos = gitchangelog.GitRepos(os.getcwd())

    @property
    def raw_changelog(self):
        ## Currifyed main function
        return lambda *a, **kw: gitchangelog.changelog(
            self.repos, *a, output_engine=raw_renderer, **kw)

    @property
    def simple_changelog(self):
        ## Currifyed main function
        return lambda *a, **kw: gitchangelog.changelog(
            self.repos, *a, output_engine=simple_renderer, **kw)
