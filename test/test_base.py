from common import GitChangelogTestCase, w, cmd


class TestBase(GitChangelogTestCase):

    def test_simple_run(self):
        out, err, errlvl = cmd('$tprog')
        self.assertNotEqual(
            errlvl, 0,
            msg="Should fail because not finding configuration file")
        self.assertContains(
            err, "--help",
            msg="Error message should mention --help option. "
            "Current stderr:\n%s" % err)
        self.assertEqual(
            out, "",
            msg="There should be no standard output. "
            "Current stdout:\n%r" % out)
