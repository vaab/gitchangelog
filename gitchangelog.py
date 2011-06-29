#!/usr/bin/env python

##
## TODO:
##
##  - use an external template to format changelog
##


import re
import os
import os.path
import sys
import textwrap
import datetime
import collections

from subprocess import Popen, PIPE

CONFIG_FILENAME = os.environ.get('GITCHANGELOG_CONFIG_FILENAME',
                                 '~/.git-changelog.rc')

help="""usage: %(exname)s

Run this command somewhere in a git repository to get a ReST changelog in
stdout.

%(exname)s uses a config file to remove some commit or do some regexp-replace
 in commit messages thanks to a config file.

Config file path can be set to be local to a git repository by using:

  $ git config git-changelog.rc-path <MY-LOCAL-PATH>

If this value is not set, %(CONFIG_FILENAME)r is used.

"""


class ShellError(Exception): pass

def die(msg=None):
    if msg: sys.stderr.write(msg + "\n")
    sys.exit(1)


## config file functions

def load_config_file(filename, fail_if_not_present=True):
    """Loads data from a config file."""

    config = {}

    if os.path.exists(filename):
        try:
            execfile(filename, config)
        except SyntaxError, e:
            die('Syntax error in config file: %s\n'
                'Line %i offset %i\n' % (filename, e.lineno, e.offset))
    else:
        if fail_if_not_present:
            die('%r config file is not found and is required.' % (filename, ))

    return config


## Text functions

def ucfirst(msg):
    return msg[0].upper() + msg[1:]


def final_dot(msg):
    if len(msg) == 0:
        return "No commit message."
    if msg[-1].isalnum():
        return msg + "."
    return msg


def indent(text, chars="  ", first=None):
    """Return text string indented with the given chars

    >>> string = 'This is first line.\\nThis is second line\\n'

    >>> print indent(string, chars="| ") # doctest: +NORMALIZE_WHITESPACE
    | This is first line.
    | This is second line
    |

    >>> print indent(string, first="- ") # doctest: +NORMALIZE_WHITESPACE
    - This is first line.
      This is second line


    """
    if first:
        first_line = text.split("\n")[0]
        rest = '\n'.join(text.split("\n")[1:])
        return '\n'.join([first + first_line,
                          indent(rest, chars=chars)])
    return '\n'.join([chars + line
                      for line in text.split('\n')])


def paragraph_wrap(text, regexp="\n\n"):
    r"""Wrap text by making sure that paragraph are separated correctly

    >>> string = 'This is first paragraph which is quite long don\'t you \
    ... think ? Well, I think so.\n\nThis is second paragraph\n'

    >>> print paragraph_wrap(string) # doctest: +NORMALIZE_WHITESPACE
    This is first paragraph which is quite long don't you think ? Well, I
    think so.
    This is second paragraph

    Notice that that each paragraph has been wrapped separately.

    """
    regexp = re.compile(regexp, re.MULTILINE)
    return "\n".join("\n".join(textwrap.wrap(paragraph.strip()))
                     for paragraph in regexp.split(text)).strip()

## System functions

def cmd(command):

    p = Popen(command, shell=True,
              stdin=PIPE, stdout=PIPE, stderr=PIPE,
              close_fds=True)
    stdout, stderr = p.communicate()
    return stdout, stderr, p.returncode


def wrap(command, quiet=True, exit_on_error=False, ignore_errlvls=[0]):
    """Wraps a shell command and casts an exception on unexpected errlvl

    >>> wrap('/tmp/lsdjflkjf') # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    ShellError: Wrapped command '/tmp/lsdjflkjf' exited with errorlevel 127.
      stderr:
      | /bin/sh: /tmp/lsdjflkjf: not found

    >>> wrap('echo hello') # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    'hello\\n'


    """

    out, err, errlvl = cmd(command)

    if errlvl not in ignore_errlvls:

        formatted = []
        if out:
            if out.endswith('\n'):
                out = out[:-1]
            formatted.append("stdout:\n%s" % indent(out, "| "))
        if err:
            if err.endswith('\n'):
                err = err[:-1]
            formatted.append("stderr:\n%s" % indent(err, "| "))
        formatted = '\n'.join(formatted)

        raise ShellError("Wrapped command %r exited with errorlevel %d.\n%s"
                        % (command, errlvl, indent(formatted, chars="  ")))
    return out

## git information access

class GitCommit(object):

    def __init__(self, identifier, repos):
        self.repos = repos
        self.identifier = identifier

        if identifier is "LAST":
            identifier = wrap("git log --format=%H | tail -n 1").strip()

        attrs = {'sha1': "%h",
                 'subject': "%s",
                 'author_name': "%an",
                 'author_date': "%ad",
                 'committer_name': "%cn",
                 'committer_date_timestamp': "%ct",
                 'raw_body': "%B",
                 'body': "%b",
                 }
        aformat = "%x00".join(attrs.values())
        try:
            ret = wrap("git show -s %r --pretty=format:%s" % (identifier, aformat))
        except ShellError:
            raise ValueError("Given commit identifier %r doesn't exists"
                             % identifier)
        attr_values = ret.split("\x00")
        for attr, value in zip(attrs.keys(), attr_values):
            setattr(self, attr, value.strip())

    @property
    def date(self):
        d = datetime.datetime.utcfromtimestamp(float(self.committer_date_timestamp))
        return d.strftime('%Y-%m-%d')

    def __eq__(self, value):
        if not isinstance(value, GitCommit):
            return False
        return self.sha1 == value.sha1

    def __hash__(self):
        return hash(self.sha1)

    def __sub__(self, value):
        if not isinstance(value, GitCommit):
            raise TypeError("Invalid type for %r in operation" % value)
        if self.sha1 == value.sha1:
            return []
        commits = wrap('git rev-list %s..%s'
                       % (value.sha1, self.sha1)).strip()
        if not commits:
            raise ValueError('Seems that %r is earlier than %r'
                             % (self.identifier, value.identifier))
        return [GitCommit(commit, self.repos)
                for commit in reversed(commits.split('\n'))]

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.identifier)


class GitRepos(object):

    def __init__(self, path):

        self.path = path

    @property
    def tags(self):
        tags = wrap('git tag -l').strip().split("\n")
	while '' in tags:
            tags.remove('')
        return sorted([GitCommit(tag, self) for tag in tags],
                      key=lambda x: int(x.committer_date_timestamp))

    def changelog(self, ignore_regexps=[],
                  replace_regexps={},
                  section_regexps={},
                  unreleased_version_label="unreleased",
                  tag_filter_regexp=r"\d+\.\d+(\.\d+)?",
                  body_split_regexp="\n\n",
                  ):

        def make_section_string(title, section, section_label_order):
            s = ""
            if len(sections) != 0:
                title = title.strip()
                s += title + "\n"
                s += "-" * len(title) + "\n\n"

                nb_sections = len(sections)
                for section in section_label_order:
                    if section not in sections:
                        continue

                    section_label = section if section else "Other"

                    if not (section_label == "Other" and nb_sections == 1):
                        s += section_label + "\n"
                        s += "~" * len(section_label) + "\n\n"

                    for entry in sections[section]:
                        s += entry
            return s


        s =  "Changelog\n"
        s += "=========\n\n"


        tags = [tag
                for tag in reversed(self.tags)
                if re.match(tag_filter_regexp, tag.identifier)]

        section_order = [k for k, v in section_regexps]


        title = unreleased_version_label + "\n"
        sections = collections.defaultdict(list)

        for commit in reversed(self[:]):

            tags_of_commit = [tag for tag in tags
                             if tag == commit]
            if len(tags_of_commit) > 0:
                tag = tags_of_commit[0]
                ## End of sections, let's flush current one.
                s += make_section_string(title, sections, section_order)

                title = "%s (%s)\n" % (tag.identifier, commit.date)
                sections = collections.defaultdict(list)

            ## Ignore some commit subject

            if any([re.match(pattern, commit.subject) is not None
                    for pattern in ignore_regexps]):
                continue

            ## Put message in sections if possible

            def first_matching(replace_regexps, string):
                for section, regexps in section_regexps:
                    if regexps is None:
                        return section
                    for regexp in regexps:
                        if re.match(regexp, commit.subject) is not None:
                            return section

            matched_section = first_matching(replace_regexps, commit.subject)

            ## Replace content in commit subject

            subject = commit.subject
            for regexp, replacement in replace_regexps.iteritems():
                subject = re.sub(regexp, replacement, subject)

            ## Finaly print out the commit

            subject = final_dot(subject)
            subject += " [%s]" % (commit.author_name, )
            entry = indent('\n'.join(textwrap.wrap(ucfirst(subject))),
                           first="- ").strip() + "\n\n"

            if commit.body:
                entry += indent(paragraph_wrap(commit.body,
                                               regexp=body_split_regexp)) + "\n\n"

            sections[matched_section].append(entry)


        s += make_section_string(title, sections, section_order)
        return s

    def __getitem__(self, key):

        if isinstance(key, basestring):
            return GitCommit(key, self)

        if isinstance(key, slice):
            start, stop = key.start, key.stop

            if start is None:
                start = GitCommit('LAST', self)

            if stop is None:
                stop = GitCommit('HEAD', self)

            return stop - start
        raise NotImplemented("Unsupported getitem %r object." % key)


def main():

    basename = os.path.basename(sys.argv[0])

    if len(sys.argv) == 1:
        repos = "."
    elif len(sys.argv) == 2:
        if sys.argv[1] == "--help":
            print help % {'exname': basename,
                          'CONFIG_FILENAME': CONFIG_FILENAME}
            sys.exit(0)
        repos = sys.argv[1]
    else:
        die('usage: %s [REPOS]\n' % basename)

    ## warning: not safe (repos is given by the user)
    changelogrc = wrap("cd %r; git config git-changelog.rc-path" % repos,
                       ignore_errlvls=[0,1,255])

    if not changelogrc:
        changelogrc = CONFIG_FILENAME

    config = load_config_file(os.path.expanduser(changelogrc))

    print GitRepos(repos).changelog(
        ignore_regexps=config['ignore_regexps'],
        replace_regexps=config['replace_regexps'],
        section_regexps=config['section_regexps'],
        unreleased_version_label=config['unreleased_version_label'],
        tag_filter_regexp=config['tag_filter_regexp'],
        body_split_regexp=config['body_split_regexp'],
    )


## MAIN CODE
if __name__ == "__main__":

    # import doctest
    # doctest.testmod()
    # sys.exit(1)

    main()
