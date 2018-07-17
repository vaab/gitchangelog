# -*- encoding: utf-8 -*-
"""Testing tag data

Currently only testing tag subject but to be extended when more tag data is 
included

"""

from __future__ import unicode_literals

import textwrap

from .common import BaseGitReposTest



def simple_renderer(data, opts):
    s = ""
    for version in data["versions"]:
        s += "%s: %s (%s)\n" % (version["tag"], 
                            version["subject"], 
                            version["tagger_date"])
        for section in version["sections"]:
            s += "  %s:\n" % section["label"]
            for commit in section["commits"]:
                s += "    * %(subject)s [%(author)s]\n" % commit
        s += "\n"
    return s

class TagSubjectTest(BaseGitReposTest):

    REFERENCE = textwrap.dedent("""\
        1.2: tag message (2017-03-17)
          None:
            * b [The Committer]

        """)

    def setUp(self):
        super(TagSubjectTest, self).setUp()

        self.git.commit(message="b",
                        date="2017-02-20 11:00:00",
                        allow_empty=True)
        self.git.tag(['-a', "1.2", '--message=tag message'],
                     env={'GIT_COMMITTER_DATE': "2017-03-17 11:00:00"})

    def test_checking_tag_subject(self):
        out = self.changelog(output_engine=simple_renderer)
        self.assertNoDiff(self.REFERENCE, out)