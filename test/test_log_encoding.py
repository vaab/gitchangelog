# -*- encoding: utf-8 -*-
"""Testing unicode display"""

from __future__ import unicode_literals

import textwrap

from .common import BaseGitReposTest, cmd


class UnicodeCommitMessageTest(BaseGitReposTest):

    REFERENCE = textwrap.dedent("""\
        Changelog
        =========


        (unreleased)
        ------------
        - Hć. [The Committer]


        1.2 (2017-02-20)
        ----------------
        - B. [The Committer]


        """)

    def setUp(self):
        super(UnicodeCommitMessageTest, self).setUp()

        self.git.commit(message="b",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)
        self.git.tag("1.2")
        self.git.commit(message="Hć",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)

    def test_checking_log_output(self):
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            err, "",
            msg="There should be non error messages. "
            "Current stderr:\n%s" % err)
        self.assertEqual(errlvl, 0)
        self.assertNoDiff(self.REFERENCE, out)

