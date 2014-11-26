# -*- encoding: utf-8 -*-
"""
Tests issue #23
(https://github.com/securactive/gitchangelog/issues/23)

"""

from __future__ import unicode_literals

import difflib

from common import BaseGitReposTest, w


class TestCrossBranchTags(BaseGitReposTest):

    REFERENCE = """\
None
  None:
    * c [The Committer]
    * b [The Committer]
    * a [The Committer]

"""

    def setUp(self):
        super(TestCrossBranchTags, self).setUp()

        ## Target tree:
        ##
        ## (Pdb) print w("git log --all --pretty=tformat:%s\ %d --graph")
        ## * c  (HEAD, master)
        ## * b
        ## * a

        w("""

            git commit -m 'a' --allow-empty
            git commit -m 'b' --allow-empty
            git commit -m 'c' --allow-empty

        """)

    def test_matching_reference(self):
        """Test that all 3 commits are in the changelog"""

        changelog = self.simple_changelog()
        self.assertEqual(
            changelog, self.REFERENCE,
            msg="Should match our reference output... "
            "diff of reference vs current:\n%s"
            % '\n'.join(difflib.unified_diff(self.REFERENCE.split("\n"),
                                             changelog.split("\n"),
                                             lineterm="")))


