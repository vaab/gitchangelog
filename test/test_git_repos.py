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

    def test_commit_less_or_equal_unrelated(self):
        self.repos.git.checkout("unrelated_commit", orphan=True)
        self.git.commit(
            message="unrelated",
            date='2000-01-02 11:00:00',
            allow_empty=True)
        with self.assertRaisesRegexp(ValueError, "Unrelated commits"):
            self.repos.commit("0.0.1") < self.repos.commit("HEAD")
        with self.assertRaisesRegexp(ValueError, "Unrelated commits"):
            self.repos.commit("0.0.1") > self.repos.commit("HEAD")
        with self.assertRaisesRegexp(ValueError, "Unrelated commits"):
            self.repos.commit("0.0.1") <= self.repos.commit("HEAD")
        with self.assertRaisesRegexp(ValueError, "Unrelated commits"):
            self.repos.commit("0.0.1") >= self.repos.commit("HEAD")


class TestCrossBranchReleasesOrder(BaseGitReposTest):

    REFERENCE = textwrap.dedent("""\
        0.0.5
          None:
            * Merge branch 'master' into develop [The Committer]
            * new: some new commit [The Committer]

        0.0.4
          None:
            * new: another release on this branch [The Committer]
            * new: second commit on develop branch [The Committer]

        0.0.3
          None:
            * fix: hotfix on master [The Committer]

        0.0.2
          None:
            * new: first commit on develop branch [The Committer]

        0.0.1
          None:
            * first commit [The Committer]

        """)

    def setUp(self):
        super(TestCrossBranchReleasesOrder, self).setUp()

        ## Target tree:
        ##
        ## (Pdb) print self.git.log(['--all', '--pretty=tformat:%s %d', '--graph', '--author-date-order'])
        ## *   Merge branch 'master' into develop  (HEAD -> develop, tag: 0.0.5)
        ## |\
        ## * | new: another release on this branch  (tag: 0.0.4)
        ## | * new: some new commit  (master)
        ## | * fix: hotfix on master  (tag: 0.0.3)
        ## * | new: second commit on develop branch
        ## * | new: first commit on develop branch  (tag: 0.0.2)
        ## |/
        ## * first commit  (tag: 0.0.1)
        ##

        self.git.commit(message='first commit',
                        allow_empty=True,
                        date='2000-01-02 11:00:00')
        self.git.tag("0.0.1")

        ## We are on master branch by default...
        ## commit, tag
        self.git.checkout(b="develop")
        self.git.commit(message='new: first commit on develop branch',
                        allow_empty=True,
                        date='2000-01-02 11:00:03')
        self.git.tag("0.0.2")

        self.git.commit(message='new: second commit on develop branch',
                        allow_empty=True,
                        date='2000-01-02 11:00:05')

        ## Back on master, commit tag
        self.git.checkout("master")
        self.git.commit(message='fix: hotfix on master', allow_empty=True,
                        date='2000-01-02 11:00:010')
        self.git.tag("0.0.3")

        self.git.commit(message='new: some new commit', allow_empty=True,
                        date='2000-01-02 11:00:15')

        ## Merge and tag
        self.git.checkout("develop")
        self.git.commit(message='new: another release on this branch',
                        allow_empty=True,
                        date='2000-01-02 11:00:20')

        self.git.tag("0.0.4")

        self.git.merge("master", no_ff=True)
        self.git.tag("0.0.5")

    def test_order_of_releases(self):
        """Test that releases are displayed in correct order"""

        changelog = self.simple_changelog()
        self.assertNoDiff(
            self.REFERENCE, changelog)
