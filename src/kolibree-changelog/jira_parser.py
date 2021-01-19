from pathlib import Path
from urllib.parse import urljoin

from jira import JIRA

from changelog_writer import ChangelogItem, ChangeType


class JiraParser(object):
    username: str
    password: str
    server: str

    def __init__(self, username: str, password: str, server: str):
        self.username = username
        self.password = password
        self.server = server

    def generate_changelog_items(self, tickets: [str]) -> [ChangelogItem]:
        auth_jira = JIRA(
            server=self.server,
            basic_auth=(self.username, self.password),
        )

        changelog_items: [ChangelogItem] = []

        for ticket in tickets:
            issue = auth_jira.issue(ticket)
            ticket_url = urljoin(self.server, f"browse/{ticket}")

            change_type = ChangeType.build(issue.fields.issuetype.name)

            if change_type:
                item = ChangelogItem(
                    title=issue.fields.summary,
                    change_type=change_type,
                    url=ticket_url,
                    code=ticket,
                )
                changelog_items.append(item)
        return changelog_items
