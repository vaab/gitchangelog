# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os.path
import difflib

from common import GitChangelogTestCase, w, cmd


class TestEnvironmentCornerCases(GitChangelogTestCase):

    def test_config_file_is_not_a_file(self):
        w("""
            mkdir .gitchangelog.rc
        """)
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            errlvl, 1,
            msg="Should fail when bogus config file exists but is not a file")
        self.assertContains(
            err, "not a file",
            msg="There should be a error message stating that config file is not a file."
            "Current stderr:\n%r" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%s" % out)
