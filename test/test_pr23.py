# -*- encoding: utf-8 -*-
"""
Tests issue #23
(https://github.com/securactive/gitchangelog/issues/23)

"""

from __future__ import unicode_literals

import textwrap

from .common import BaseGitReposTest


class TestCrossBranchTags(BaseGitReposTest):

    REFERENCE = textwrap.dedent("""\
        None
          None:
            * c [The Committer]
            * b [The Committer]
            * a [The Committer]

        """)

    def setUp(self):
        super(TestCrossBranchTags, self).setUp()

        ## Target tree:
        ##
        ## (Pdb) print w("git log --all --pretty=tformat:%s\ %d --graph")
        ## * c  (HEAD, master)
        ## * b
        ## * a

        self.git.commit(message='a', allow_empty=True)
        self.git.commit(message='b', allow_empty=True)
        self.git.commit(message='c', allow_empty=True)

    def test_matching_reference(self):
        """Test that all 3 commits are in the changelog"""

        changelog = self.simple_changelog()
        self.assertNoDiff(
            self.REFERENCE, changelog)


