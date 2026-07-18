import unittest
from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parent.parent
    / ".github"
    / "workflows"
    / "daily-push.yml"
)
PERIOD_CARE_WORKFLOW = WORKFLOW.with_name("period-care.yml")


class DailyPushWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_prepares_before_target_time_and_has_retry_windows(self) -> None:
        for cron in (
            'cron: "55 7 * * *"',
            'cron: "12,27,42,57 8 * * *"',
            'cron: "55 17 * * *"',
            'cron: "12,27,42,57 18 * * *"',
        ):
            self.assertIn(cron, self.workflow)
        self.assertIn("等待到目标整点", self.workflow)
        self.assertIn('sleep "$wait_seconds"', self.workflow)

    def test_each_recipient_has_an_independent_send_marker(self) -> None:
        self.assertIn("actions/cache/restore@v6", self.workflow)
        self.assertIn("actions/cache/save@v6", self.workflow)
        self.assertIn("period }}-girlfriend", self.workflow)
        self.assertIn("period }}-boyfriend", self.workflow)
        self.assertIn("steps.send-girlfriend.outcome == 'success'", self.workflow)
        self.assertIn("steps.send-boyfriend.outcome == 'success'", self.workflow)

    def test_daily_deployment_preserves_period_care_page(self) -> None:
        self.assertIn("保留爱心关怀详情页", self.workflow)
        self.assertIn("--message-kind period-care", self.workflow)


class PeriodCareWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = PERIOD_CARE_WORKFLOW.read_text(encoding="utf-8")

    def test_is_manual_only_and_offers_three_care_styles(self) -> None:
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("schedule:", self.workflow)
        for style in ("温柔关心", "有些不舒服", "很难受想休息"):
            self.assertIn(f"- {style}", self.workflow)

    def test_only_sends_to_girlfriend(self) -> None:
        self.assertIn("--recipient-id girlfriend", self.workflow)
        self.assertIn('WECHAT_OPENID_BOYFRIEND: ""', self.workflow)
        self.assertNotIn("给自己发送", self.workflow)
        self.assertIn("--message-kind period-care", self.workflow)


if __name__ == "__main__":
    unittest.main()
