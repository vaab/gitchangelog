from unittest import TestCase

from src.gitchangelog.gitchangelog import fix_incorrect_ticket


class IncorrectTicketTests(TestCase):
    def test_jira_format_fix_too_many_dashes(self):
        ticket = "KLTB002-12234-ABCD-EFGH"
        ticket_fixed = fix_incorrect_ticket(ticket=ticket)
        self.assertEqual(ticket_fixed, "KLTB002-12234")

    def test_jira_format_fix_one_dash(self):
        ticket = "KLTB002-12234"
        ticket_fixed = fix_incorrect_ticket(ticket=ticket)
        self.assertEqual(ticket, ticket_fixed)
