# -*- encoding: utf-8 -*-
"""
Tests issue #52
(https://github.com/vaab/gitchangelog/issues/52)

"""

from __future__ import unicode_literals

import difflib

from common import BaseGitReposTest, w


class TestNoTagWarn(BaseGitReposTest):

    def setUp(self):
        super(TestNoTagWarn, self).setUp()

        ## Target tree:
        ##
        ## (Pdb) print w("git log --all --pretty=tformat:%s\ %d --graph")
        ## * a  (HEAD, master)

        w("""

            git commit -m 'a' --allow-empty

        """)

    def test_no_tag_no_revlist(self):
        """if no tags are detected it should throw a warning"""

        warnings = []

        def warn(msg):
            if "no tag" in msg.lower():
                warnings.append(msg)

        self.simple_changelog(warn=warn)
        self.assertTrue(
            len(warnings) != 0,
            msg="Should have outputed at least one warning about 'no tag'")

    def test_no_tag_revlist(self):
        """if no tags are detected and revlist is provided, check warning"""

        warnings = []

        def warn(msg):
            if "no tag" in msg.lower() and "revlist" in msg.lower():
                warnings.append(msg)

        self.simple_changelog(revlist=["HEAD", ], warn=warn)
        self.assertTrue(
            len(warnings) != 0,
            msg="Should have outputed at least one warning about 'no tag'"
            "and 'revlist'")


class TestEmptyChangelogWarn(BaseGitReposTest):

    def setUp(self):
        super(TestEmptyChangelogWarn, self).setUp()

        ## Target tree:
        ##
        ## (Pdb) print w("git log --all --pretty=tformat:%s\ %d --graph")
        ## * chg: dev: ignore !minor (HEAD, master)

        w("""

            git commit -m 'chg: dev: ignore !minor' --allow-empty

        """)

    def test_no_commit(self):
        """check warning about empty changelog"""

        warnings = []

        def warn(msg):
            if "empty changelog" in msg.lower():
                warnings.append(msg)

        self.simple_changelog(warn=warn, ignore_regexps=['!minor'])
        self.assertTrue(
            len(warnings) != 0,
            msg="Should have outputed at least one warning about 'empty changelog'")

