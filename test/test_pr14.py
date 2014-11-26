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

import difflib

from common import BaseGitReposTest, w


class TestCrossBranchTags(BaseGitReposTest):

    REFERENCE = """\
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

"""

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

        w("""

            git commit -m 'first commit' --allow-empty
            git tag 0.0.1

            ## We are on master branch by default...
            ## commit, tag
            git checkout -b develop
            git commit -m 'new: first commit on develop branch' --allow-empty
            git tag 0.0.2

            git commit -m 'new: second commit on develop branch' --allow-empty

            ## Back on master, commit tag
            git checkout master
            git commit -m 'fix: hotfix on master' --allow-empty
            git tag 0.0.3

            git commit -m 'new: some new commit' --allow-empty

            ## Merge and tag
            git checkout develop
            git merge master --no-ff
            git tag 0.0.4

        """)

    def test_nothing_missed_or_duplicate(self):
        """Test that all tags in branch history make it into changelog"""

        changelog = self.simple_changelog()
        self.assertEqual(
            changelog, self.REFERENCE,
            msg="Should match our reference output... "
            "diff of reference vs current:\n%s"
            % '\n'.join(difflib.unified_diff(self.REFERENCE.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))


class TestLogLinearbility(BaseGitReposTest):
    """Test that commits are attributed to the proper release"""

    REFERENCE = """\
0.0.3
  None:
    * new: commit on develop branch [The Committer]

0.0.2
  None:
    * fix: something [The Committer]

0.0.1
  None:
    * first commit [The Committer]

"""

    def setUp(self):
        super(TestLogLinearbility, self).setUp()

        ## Target tree:
        ##
        ## (Pdb) print w("git log --all --pretty=tformat:%s\ %d --graph")
        ## * new: commit on develop branch  (HEAD, tag: 0.0.3, develop)
        ## * fix: something  (tag: 0.0.2)
        ## * first commit  (tag: 0.0.1, master)

        w("""

            git commit -m 'first commit' --allow-empty
            git tag 0.0.1

            ## Branch
            git checkout -b develop

            git commit -m 'fix: something' --allow-empty
            git tag 0.0.2

            git commit -m 'new: commit on develop branch' --allow-empty
            git tag 0.0.3

        """)


    def test_easy_release_attribution(self):
        """Test attribution when commits are already linear"""

        changelog = self.simple_changelog()
        self.assertEqual(
            changelog, self.REFERENCE,
            msg="Should match our reference output... "
            "diff of reference vs current:\n%s"
            % '\n'.join(difflib.unified_diff(self.REFERENCE.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))


class TestLogHardLinearbility(BaseGitReposTest):

    REFERENCE = """\
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

"""

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

        w("""

            git commit -m 'first commit' --allow-empty
            git tag 0.0.1

            ## Branch
            git checkout -b develop

            ## Build the tree
            git commit -m 'fix: something' --allow-empty
            git tag 0.1

            git commit -m 'chg: continued development' --allow-empty

            git checkout 0.1

            git commit -m 'fix: out-of-band hotfix' --allow-empty
            git tag 0.1.1

            git checkout develop

            git merge 0.1.1

            git commit -m 'new: something' --allow-empty
            git tag 0.2

        """)

    def test_hard_release_attribution(self):
        """Test attribution for out-of-band releases

        """
        changelog = self.simple_changelog()
        self.assertEqual(
            changelog, self.REFERENCE,
            msg="Should match our reference output... "
            "diff of reference vs current:\n%s"
            % '\n'.join(difflib.unified_diff(self.REFERENCE.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))
