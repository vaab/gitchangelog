# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os
import textwrap

from .common import cmd, BaseGitReposTest, BaseTmpDirTest, gitchangelog


class GitReposInstantiationTest(BaseTmpDirTest):

    def test_instanciate_on_non_git_repos_dir(self):
        os.mkdir("repos")
        with self.assertRaises(EnvironmentError):
            gitchangelog.GitRepos("repos")

    def test_gitchangelog_on_non_git_repos_dir(self):
        os.mkdir("repos")
        os.chdir("repos")
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err.strip(),
            "Not in a git repository. (calling ``git remote`` failed.)")
        self.assertEqual(errlvl, 1)


class GitReposTest(BaseGitReposTest):

    def setUp(self):
        super(GitReposTest, self).setUp()

        self.git.commit(
            message='new: first commit',
            author='Bob <bob@example.com>',
            date='2000-01-01 10:00:00',
            allow_empty=True)
        self.git.tag("0.0.1")
        self.git.commit(
            message=textwrap.dedent("""
                add ``b`` with non-ascii chars éèàâ§µ and HTML chars ``&<``

                Change-Id: Ic8aaa0728a43936cd4c6e1ed590e01ba8f0fbf5b"""),
            author='Alice <alice@example.com>',
            date='2000-01-02 11:00:00',
            allow_empty=True)

    def test_get_commit(self):
        commit = self.repos.commit("0.0.1")
        self.assertEqual(commit.subject, 'new: first commit')
        commit = self.repos.commit("HEAD")
        self.assertEqual(
            commit.subject,
            'add ``b`` with non-ascii chars éèàâ§µ and HTML chars ``&<``')

    def test_exception_when_requesting_unexistent_commit(self):
        commit = self.repos.commit("XXX")  ## No exception yet.
        with self.assertRaises(ValueError):
            commit.subject

    def test_commit_less_or_equal(self):
        self.assertTrue(self.repos.commit("0.0.1") < self.repos.commit("HEAD"))
        self.assertTrue(self.repos.commit("0.0.1") < "HEAD")
        self.assertTrue(self.repos.commit("HEAD") == "HEAD")
        self.assertTrue(self.repos.commit("0.0.1") <= "HEAD")
        self.assertTrue(self.repos.commit("HEAD") <= "HEAD")
