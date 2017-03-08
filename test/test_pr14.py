# -*- encoding: utf-8 -*-
"""
Tests pull request #14 Tags merged from other branches missing
(https://github.com/securactive/gitchangelog/pull/14)

Use cases intended to be covered by this test:
- Tags located in branches that are not "first-parents" get included.
    eg. A release tag in develop and a release tag in master should both be
    analyzed for the changelog.
- Changes committed to the repository before a tag on another branch should
    not be included in that tag, but the next descendant tag.

Run test with: python -m unittest discover -fv -s test

"""

from __future__ import unicode_literals

import textwrap

from .common import BaseGitReposTest


class TestCrossBranchTags(BaseGitReposTest):

    REFERENCE = textwrap.dedent("""\
        0.0.4
          None:
            * Merge branch 'master' into develop [The Committer]
            * new: some new commit [The Committer]
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
        super(TestCrossBranchTags, self).setUp()

        ## Target tree:
        ##
        ## (Pdb) print w("git log --all --pretty=tformat:%s\ %d --graph")
        ## *   Merge branch 'master' into develop  (HEAD, tag: 0.0.4, develop)
        ## |\
        ## | * new: some new commit  (master)
        ## | * fix: hotfix on master  (tag: 0.0.3)
        ## * | new: second commit on develop branch
        ## * | new: first commit on develop branch  (tag: 0.0.2)
        ## |/
        ## * first commit  (tag: 0.0.1)

        self.git.commit(message='first commit', allow_empty=True)
        self.git.tag("0.0.1")

        ## We are on master branch by default...
        ## commit, tag
        self.git.checkout(b="develop")
        self.git.commit(message='new: first commit on develop branch',
                        allow_empty=True)
        self.git.tag("0.0.2")

        self.git.commit(message='new: second commit on develop branch',
                        allow_empty=True)

        ## Back on master, commit tag
        self.git.checkout("master")
        self.git.commit(message='fix: hotfix on master', allow_empty=True)
        self.git.tag("0.0.3")

        self.git.commit(message='new: some new commit', allow_empty=True)

        ## Merge and tag
        self.git.checkout("develop")
        self.git.merge("master", no_ff=True)
        self.git.tag("0.0.4")

    def test_nothing_missed_or_duplicate(self):
        """Test that all tags in branch history make it into changelog"""

        changelog = self.simple_changelog()
        self.assertNoDiff(
            self.REFERENCE, changelog)


class TestLogLinearbility(BaseGitReposTest):
    """Test that commits are attributed to the proper release"""

    REFERENCE = textwrap.dedent("""\
        0.0.3
          None:
            * new: commit on develop branch [The Committer]

        0.0.2
          None:
            * fix: something [The Committer]

        0.0.1
          None:
            * first commit [The Committer]

        """)

    def setUp(self):
        super(TestLogLinearbility, self).setUp()

        ## Target tree:
        ##
        ## (Pdb) print w("git log --all --pretty=tformat:%s\ %d --graph")
        ## * new: commit on develop branch  (HEAD, tag: 0.0.3, develop)
        ## * fix: something  (tag: 0.0.2)
        ## * first commit  (tag: 0.0.1, master)

        self.git.commit(message='first commit', allow_empty=True)
        self.git.tag("0.0.1")

        ## Branch
        self.git.checkout(b="develop")

        self.git.commit(message='fix: something', allow_empty=True)
        self.git.tag("0.0.2")

        self.git.commit(message='new: commit on develop branch',
                        allow_empty=True)
        self.git.tag("0.0.3")

    def test_easy_release_attribution(self):
        """Test attribution when commits are already linear"""

        changelog = self.simple_changelog()
        self.assertNoDiff(
            self.REFERENCE, changelog)


class TestLogHardLinearbility(BaseGitReposTest):

    REFERENCE = textwrap.dedent("""\
        0.2
          None:
            * new: something [The Committer]
            * Merge tag '0.1.1' into develop [The Committer]
            * chg: continued development [The Committer]

        0.1.1
          None:
            * fix: out-of-band hotfix [The Committer]

        0.1
          None:
            * fix: something [The Committer]

        0.0.1
          None:
            * first commit [The Committer]

        """)

    def setUp(self):
        super(TestLogHardLinearbility, self).setUp()

        ##  Target tree:
        ##
        ## (Pdb) print w("git log --all --pretty=tformat:%s\ %d --graph")
        ## * new: something  (HEAD, tag: 0.2, develop)
        ## *   Merge tag '0.1.1' into develop
        ## |\
        ## | * fix: out-of-band hotfix  (tag: 0.1.1)
        ## * | chg: continued development
        ## |/
        ## * fix: something  (tag: 0.1)
        ## * first commit  (tag: 0.0.1, master)
        ##

        self.git.commit(message='first commit', allow_empty=True)
        self.git.tag("0.0.1")

        ## Branch
        self.git.checkout(b="develop")

        ## Build the tree
        self.git.commit(message='fix: something', allow_empty=True)
        self.git.tag("0.1")

        self.git.commit(message='chg: continued development', allow_empty=True)

        self.git.checkout("0.1")

        self.git.commit(message='fix: out-of-band hotfix', allow_empty=True)
        self.git.tag("0.1.1")

        self.git.checkout("develop")

        self.git.merge("0.1.1")

        self.git.commit(message='new: something', allow_empty=True)
        self.git.tag("0.2")

    def test_hard_release_attribution(self):
        """Test attribution for out-of-band releases"""

        changelog = self.simple_changelog()
        self.assertNoDiff(
            self.REFERENCE, changelog)
