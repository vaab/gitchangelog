import os
import re
from pathlib import Path
from urllib.parse import urlparse

from github import Github


class CommitParser(object):
    github_access_token: str
    repository: str
    jira_project: str
    jira_server: str

    def __init__(self, repository, jira_project, jira_server, github_access_token):
        self.repository = repository
        self.jira_project = jira_project
        self.jira_server = jira_server
        self.github_access_token = github_access_token

    @property
    def jira_regex_format(self) -> str:
        return f"({self.jira_project}-[0-9]*)"

    def jira_tickets(self, start_tag, end_tag) -> [str]:
        commits = self._get_commits(start_tag, end_tag)

        jira_tickets, github_prs = self._process_commits(
            commits, self.jira_regex_format
        )

        jira_tickets += self._get_jira_tickets_from_github(
            github_prs, self.jira_regex_format
        )

        return jira_tickets

    def _get_commits(self, start, end) -> [str]:
        return os.popen("git log --pretty=%s " + start + "..." + end)

    def _process_commits(self, commits: [str], regex_format: str) -> ([str], [str]):
        jira_ticket_regex = re.compile(regex_format)
        # Github adds pull request number (#XXXX) at the end of its title.
        github_pr_regex = re.compile("(\\(#[0-9]*\\))")
        jira_tickets: [str] = []
        github_prs: [str] = []
        for commit in commits:
            jira_search = jira_ticket_regex.search(commit)
            if jira_search is not None:
                jira_tickets.append(jira_search.group())
            elif github_pr_regex.findall(commit):
                pr_number_text = github_pr_regex.findall(commit)[-1]
                # Keep only the PR number and remove (#).
                pr_number = pr_number_text.translate({ord(i): None for i in "()#"})
                github_prs.append(pr_number)

        return (jira_tickets, github_prs)

    def _get_jira_tickets_from_github(self, github_prs: [str], regex_format: str):
        github = Github(self.github_access_token)
        repo = github.get_repo(self.repository)
        # Include the serve in the url.
        server_netloc = urlparse(self.jira_server).netloc
        url_regex = re.compile(
            f"https?:\\/\\/{server_netloc}\\b([-a-zA-Z0-9@:%_\\+.~#?&//=]*{regex_format})"
        )
        jira_ticket_regex = re.compile(regex_format)

        jira_tickets = []
        for pr_number in github_prs:
            pr = repo.get_pull(int(pr_number))
            url_match = url_regex.search(pr.body)
            if url_match is None:
                # If no url is found the PR will be skipped.
                continue
            jira_ticket_match = jira_ticket_regex.search(url_match.group())
            url_path = Path(urlparse(url_match.group()).path)
            # In case the ticket ends with 1XXXX, the regex match will not contain the XXXX.
            # The match will be PROJECT-1, which is wrong.
            # This check is to exclude this results.
            if (
                jira_ticket_match is not None
                and jira_ticket_match.group() == url_path.name
            ):
                jira_tickets.append(jira_ticket_match.group())
        return jira_tickets
