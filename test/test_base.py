from common import GitChangelogTestCase, w, cmd


class TestConfiguration(GitChangelogTestCase):

    def test_simple_run(self):
        out, err, errlvl = cmd('$tprog')
        self.assertEqual(
            errlvl, 0,
            msg="Should not fail on simple repo and without config file")
        self.assertEqual(
            err, "",
            msg="There should be no standard error outputed. "
            "Current stderr:\n%r" % err)
        self.assertContains(
            out, "0.0.2",
            msg="At leat one of the tags should be displayed in stdout... "
            "Current stdout:\n%s" % out)

    def test_overriding_options(self):
        """We must be able to define a small gitchangelog.rc that adjust only
        one variable of all the builtin defaults."""

        w("""

            cat <<EOF > .gitchangelog.rc

tag_filter_regexp = r'^v[0-9]+\.[0.9]$'

EOF
            git tag 'v7.0' HEAD^
            git tag 'v8.0' HEAD

        """)
        changelog = w('$tprog')
        self.assertContains(
            changelog, "v8.0",
            msg="At leat one of the tags should be displayed in changelog... "
            "content of changelog:\n%s" % changelog)

    def test_reuse_options(self):
        """We must be able to define a small gitchangelog.rc that adjust only
        one variable of all the builtin defaults."""

        w("""cat <<EOF > .gitchangelog.rc

ignore_regexps += [r'XXX', ]

EOF
        """)
        changelog = w('$tprog')
        self.assertNotContains(
            changelog, "XXX",
            msg="Should not contain commit with XXX in it... "
            "content of changelog:\n%s" % changelog)
        self.assertContains(
            changelog, "dd file ``e``",
            msg="Should contain at least a message of other commits... "
            "content of changelog:\n%s" % changelog)
        self.assertNotContains(
            changelog, "!minor",
            msg="Shouldn't contain !minor tagged commit neither... "
            "content of changelog:\n%s" % changelog)
