from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, unique


@unique
class ChangeType(Enum):
    ENHANCEMENT = 1
    INTERNAL = 2
    BUG = 3

    @classmethod
    def build(cls, jira_issue_type: str):
        items = {
            "Story": cls.ENHANCEMENT,
            "Technical Debt": cls.INTERNAL,
            "Bug": cls.BUG,
            "Task": cls.ENHANCEMENT,
        }
        return items.get(jira_issue_type)

    @property
    def changelog_title(self):
        if self == ChangeType.ENHANCEMENT:
            return "Enhancements"
        elif self == ChangeType.INTERNAL:
            return "Internal"
        elif self == ChangeType.BUG:
            return "Fixed"
        else:
            return ""


@dataclass
class ChangelogItem:
    title: str
    change_type: ChangeType
    code: str
    url: str


@dataclass
class VersionChanges:
    version: str
    items: [ChangelogItem]

    @property
    def changes(self) -> {ChangeType: [ChangelogItem]}:
        all_changes = defaultdict(list)
        for item in self.items:
            all_changes[item.change_type].append(item)
        return all_changes


@dataclass
class Changelog:
    title: str
    versions: [VersionChanges]


class ChangelogWriter:
    @staticmethod
    def write_changelog(changelog: Changelog, filename: str):
        changelog_file = open(filename, "w")
        changelog_file.write("# " + changelog.title + "\n")

        for version_changes in changelog.versions:
            changelog_file.write("## " + version_changes.version + "\n")
            changes = version_changes.changes
            for key, items in changes.items():
                ChangelogWriter._write_items(changelog_file, key, items)

        changelog_file.write("\n")
        changelog_file.close()

    @staticmethod
    def _write_items(file, change_type, items):
        file.write("## " + change_type.changelog_title + "\n")

        for item in items:
            line = f"* [{item.code}]({item.url}) - {item.title.rstrip()}"
            file.write(line)
            file.write("\n")
