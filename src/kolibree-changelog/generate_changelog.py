import argparse
import getpass
from dataclasses import dataclass

from changelog_writer import Changelog, ChangelogWriter, VersionChanges
from commit_parser import CommitParser
from jira_parser import JiraParser


@dataclass
class Arguments:
    start_tag: str
    end_tag: str
    title: str
    filename: str
    github_access_token: str
    repository: str
    jira_project: str
    jira_username: str
    jira_access_token: str
    jira_server: str

    def __init__(self, arguments):
        self.start_tag = arguments.start_tag
        self.end_tag = arguments.end_tag
        self.title = arguments.title
        self.filename = arguments.filename
        self.github_access_token = arguments.github_access_token
        self.repository = arguments.repository
        self.jira_project = arguments.jira_project
        self.jira_server = arguments.jira_server
        self.jira_username = arguments.jira_username
        self.jira_access_token = arguments.jira_access_token


def _configure_argument_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--title",
        required=False,
        default="Changelog",
        help="Title of the changelog",
    )

    parser.add_argument(
        "--start-tag",
        required=True,
        help="Start tag",
    )
    parser.add_argument(
        "--end-tag",
        required=True,
        help="End tag for the changelog",
    )

    parser.add_argument(
        "--jira-project",
        required=True,
        help="JIRA project code that is appended to all the tickets, for ticket PROJ-1121 code is PROJ",
    )

    parser.add_argument(
        "--jira-username",
        required=True,
        help="Github access token. Make sure it has repo access",
    )

    parser.add_argument(
        "--jira-access-token",
        required=False,
        help="Jira access token. Make sure it has repo access",
    )

    parser.add_argument(
        "--jira-server",
        required=True,
        help="Jira server.",
    )

    parser.add_argument(
        "--github-access-token",
        required=False,
        help="Github access token. Make sure it has repo access",
    )

    parser.add_argument(
        "--repository",
        required=True,
        help="Repository name, eg: kolibree-git/iOS-monorepo",
    )

    parser.add_argument("--filename", help="Changelog filename", default="CHANGELOG.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Changelog argument parser")
    _configure_argument_parser(parser)
    arguments = Arguments(arguments=parser.parse_args())

    github_access_token = (
        arguments.github_access_token if arguments.github_access_token else getpass.getpass("Github access token:")
    )

    commits_parser = CommitParser(
        repository=arguments.repository,
        jira_project=arguments.jira_project,
        jira_server=arguments.jira_server,
        github_access_token=github_access_token,
    )

    jira_tickets = commits_parser.jira_tickets(start_tag=arguments.start_tag, end_tag=arguments.end_tag)

    jira_access_token = (
        arguments.jira_access_token if arguments.jira_access_token else getpass.getpass("Jira access token:")
    )

    jira_parser = JiraParser(
        username=arguments.jira_username,
        password=jira_access_token,
        server=arguments.jira_server,
    )

    changelog_items = jira_parser.generate_changelog_items(jira_tickets)
    changelog = Changelog(
        title=arguments.title,
        versions=[VersionChanges(version=arguments.end_tag, items=changelog_items)],
    )
    ChangelogWriter.write_changelog(changelog, arguments.filename)
