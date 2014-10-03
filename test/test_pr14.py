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

from common import GitChangelogTestCase, w


class TestCrossBranchTags(GitChangelogTestCase):

    def test_tags(self):
        """ Test that all tags in branch history make it into changelog """

        w("""

#            Target tree:
#
#            * bd474af (HEAD, tag: 0.0.7)
#            *   e4e3d60 Merge branch 'master' into test_tags
#            |\
#            | * ae1baa0 (tag: 0.0.6, master) fix: hotfix on master
#            |/
#            * 42e63da commit on develop branch
#            * 42e65da (tag: 0.0.5) commit on develop branch

            ## Branch
            git checkout master
            git tag 0.0.4
            git checkout -b test_tags

            ## Build the tree
            git commit -m 'commit on develop branch' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-07 11:00:00' \
                --allow-empty

            git tag 0.0.5

            git commit -m 'commit on develop branch' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-08 11:00:00' \
                --allow-empty

           git checkout master

            git commit -m 'fix: hotfix on master' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-11 11:00:00' \
                --allow-empty

            git tag 0.0.6

            git checkout test_tags
            git merge master
            git tag 0.0.7

        """)
        changelog = w('$tprog')
        self.assertContains(
            changelog, "0.0.6",
            msg="Missing a tag (0.0.6) that is located in a branch that was merged into HEAD... "
            "content of changelog:\n%s" % changelog)


class TestLogLinearbility(GitChangelogTestCase):
    """ Test that commits are attributed to the proper release """

    def test_easy_release_attribution(self):
        """ Test attribution when commits are already linear """

        REFERENCE_CHANGELOG = r"""Changelog
=========

0.0.5 (2000-01-11)
------------------

New
~~~

- Something. [Alice]

- Commit on develop branch. [Alice]

Changes
~~~~~~~

- Continued development. [Alice]

Fix
~~~

- More work on develop branch. [Alice]

0.0.4 (2000-01-07)
------------------

Changes
~~~~~~~

- Modified ``b`` XXX. [Alice]

Fix
~~~

- Something. [Alice]

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

        w("""

#            Target tree:
#
#            * 6c0fd62 (tag: 0.0.5, develop) new: something
#            * 7d6286f fix: more work on develop branch
#            * 8c1e3d6 chg: continued development
#            * fa3d4bd new: commit on develop branch
#            * ec1a19c (tag: 0.0.4) fix: something


            ## Branch
            git checkout master
            git checkout -b test_easy_release_attribution

            ## Build the tree
            git commit -m 'fix: something' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-07 11:00:00' \
                --allow-empty

            git tag 0.0.4

            git commit -m 'new: commit on develop branch' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-08 11:00:00' \
                --allow-empty

            git commit -m 'chg: continued development' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-09 11:00:00' \
                --allow-empty

            git commit -m 'fix: more work on develop branch' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-10 11:00:00' \
                --allow-empty

            git commit -m 'new: something' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-11 11:00:00' \
                --allow-empty

            git tag 0.0.5

        """)
        changelog = w('$tprog')
        self.assertEqual(
            changelog, REFERENCE_CHANGELOG,
            msg="Should match our reference output... "
            "diff from what it should be:\n%s"
            % '\n'.join(difflib.unified_diff(REFERENCE_CHANGELOG.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))

    def test_hard_release_attribution(self):
        """ Test attribution for out-of-band releases, where chronologically older commits are not in the next tag """

        REFERENCE_CHANGELOG = r"""Changelog
=========

0.2 (2000-01-12)
----------------

New
~~~

- Something. [Alice]

- Commit on develop branch. [Alice]

Changes
~~~~~~~

- Continued development. [Alice]

Fix
~~~

- More work on develop branch. [Alice]

Other
~~~~~

- Merge tag '0.1.1' into test_hard_release_attribution. [The Committer]

0.1.1 (2000-01-11)
------------------

Fix
~~~

- Out-of-band hotfix. [Alice]

0.1 (2000-01-07)
----------------

Changes
~~~~~~~

- Modified ``b`` XXX. [Alice]

Fix
~~~

- Something. [Mary]

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

        w("""

#            Target tree:
#
#            * 85b9161 (HEAD, tag: 0.2, test_hard_release_attribution) new: something
#            *   9979e78 Merge tag '0.1.1' into test_hard_release_attribution.
#            |\
#            | * 23fbe34 (tag: 0.1.1, master) fix: out-of-band hotfix
#            * | c47e172 fix: more work on develop branch
#            * | 02dd137 chg: continued development
#            * | 8491971 new: commit on develop branch
#            * | 8713012 (tag: 0.1) fix: something
#            |/   <--- From here down is base setup
#            * fc4d378 chg: modified ``b`` XXX
#            * a45944e (tag: 0.0.3) chg: modified ``b`` !minor
#            * d6a8ac7 new: add file ``e``, modified ``b``
#            * 1e6109b new: add file ``c``
#            * d7573c1 (tag: 0.0.2) new: add ``b`` with non-ascii chars éèàâ§µ
#            * b8fb18b (tag: 0.0.1) new: first commit
#

            ## Branch
            git checkout master
            git checkout -b test_hard_release_attribution

            ## Build the tree
            git commit -m 'fix: something' \
                --author 'Mary <mary@example.com>' \
                --date '2000-01-07 11:00:00' \
                --allow-empty

            git tag 0.1

            git commit -m 'new: commit on develop branch' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-08 11:00:00' \
                --allow-empty

            git commit -m 'chg: continued development' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-09 11:00:00' \
                --allow-empty

            git commit -m 'fix: more work on develop branch' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-10 11:00:00' \
                --allow-empty

           git checkout 0.1

            git commit -m 'fix: out-of-band hotfix' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-11 11:00:00' \
                --allow-empty

            git tag 0.1.1

            git checkout test_hard_release_attribution
            git merge 0.1.1

            git commit -m 'new: something' \
                --author 'Alice <alice@example.com>' \
                --date '2000-01-12 11:00:00' \
                --allow-empty

            git tag 0.2

        """)
        ## Good debugging tool
        # print w("""
        #     gitk --all
        # """)
        changelog = w('$tprog')
        self.assertEqual(
            changelog, REFERENCE_CHANGELOG,
            msg="Should match our reference output... "
            "diff from what it should be:\n%s"
            % '\n'.join(difflib.unified_diff(REFERENCE_CHANGELOG.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="",
                                             n=100)))
