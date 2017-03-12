# -*- encoding: utf-8 -*-
"""Reference file is not required to be found

Tests issue #54
(https://github.com/vaab/gitchangelog/issues/54)

"""

from __future__ import unicode_literals

from .common import BaseGitReposTest, cmd, gitchangelog


class TestConfigComplains(BaseGitReposTest):

    def test_missing_option(self):
        super(TestConfigComplains, self).setUp()

        gitchangelog.file_put_contents(
            ".gitchangelog.rc",
            "del section_regexps"
        )

        out, err, errlvl = cmd('$tprog --debug')
        self.assertContains(
            err.lower(), "missing value",
            msg="There should be an error message containing 'missing value'. "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err.lower(), "config file",
            msg="There should be an error message containing 'config file'. "
            "Current stderr:\n%s" % err)
        self.assertContains(
            err.lower(), "section_regexps",
            msg="There should be an error msg containing 'section_regexps'. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            errlvl, 1,
            msg="Should faild.")
        self.assertEqual(
            out, "",
            msg="No output is expected.")
