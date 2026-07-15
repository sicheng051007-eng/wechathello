import json
import tempfile
import unittest
from pathlib import Path

from love_push.config import ConfigurationError, load_recipients


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "recipients.json"
        self.path.write_text(
            json.dumps(
                {
                    "recipients": [
                        {
                            "id": "her",
                            "name": "小朋友",
                            "openid_env": "OPENID_HER",
                            "location": {
                                "name": "清华园",
                                "latitude": 40,
                                "longitude": 116.3,
                            },
                            "signoff": "想你",
                        },
                        {
                            "id": "him",
                            "name": "同学",
                            "openid_env": "OPENID_HIM",
                            "location": {
                                "name": "紫金港",
                                "latitude": 30.3,
                                "longitude": 120.1,
                            },
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_only_loads_configured_openids(self) -> None:
        recipients, skipped = load_recipients(self.path, {"OPENID_HER": "abc"})
        self.assertEqual([item.id for item in recipients], ["her"])
        self.assertEqual(recipients[0].openid, "abc")
        self.assertEqual(skipped, ["him"])

    def test_preview_includes_unconfigured(self) -> None:
        recipients, skipped = load_recipients(
            self.path, {}, include_unconfigured=True
        )
        self.assertEqual(len(recipients), 2)
        self.assertEqual(recipients[0].openid, "preview:her")
        self.assertEqual(skipped, [])

    def test_rejects_invalid_coordinates(self) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data["recipients"][0]["location"]["latitude"] = 100
        self.path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ConfigurationError):
            load_recipients(self.path, {"OPENID_HER": "abc"})


if __name__ == "__main__":
    unittest.main()

