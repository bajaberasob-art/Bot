import unittest

from prime_level_controls import (
    controls_with_defaults,
    render_template,
    validate_controls,
)


class PrimeLevelControlTests(unittest.TestCase):
    def test_defaults_preserve_legacy_rank_channels_and_levelup_title(self):
        controls = controls_with_defaults(
            {},
            {
                "command_rank_channels": [123, "456"],
                "levelup_title": "Legacy title",
            },
        )
        self.assertTrue(controls["rank"]["imageOnly"])
        self.assertEqual(controls["rank"]["channels"], ["123", "456"])
        self.assertEqual(controls["levelup"]["embedTitle"], "Legacy title")
        self.assertFalse(controls["periodic"]["daily"]["enabled"])

    def test_unknown_message_variables_are_safe(self):
        self.assertEqual(
            render_template("Hi {user}: {future_variable}", {"user": "A"}),
            "Hi A: {future_variable}",
        )

    def test_validation_normalizes_ids_and_rejects_enabled_schedule_without_channel(self):
        controls = controls_with_defaults()
        controls["rank"]["channels"] = ["123"]
        controls["levelup"]["mentionRole"] = "45"
        controls["periodic"]["daily"].update({
            "enabled": True,
            "channel": "678",
            "timezone": "Asia/Aden",
            "time": "09:30",
        })
        checked = validate_controls(
            controls,
            {},
            validate_channel=lambda raw, messageable=False: int(raw),
            validate_role=lambda raw: int(raw),
            validate_assignable_role=lambda raw: int(raw),
        )
        self.assertEqual(checked["rank"]["channels"], ["123"])
        self.assertEqual(checked["levelup"]["mentionRole"], "45")
        self.assertEqual(checked["periodic"]["daily"]["channel"], "678")

        controls["periodic"]["daily"]["channel"] = ""
        with self.assertRaisesRegex(ValueError, "requires a channel"):
            validate_controls(
                controls,
                {},
                validate_channel=lambda raw, messageable=False: int(raw),
                validate_role=lambda raw: int(raw),
                validate_assignable_role=lambda raw: int(raw),
            )


if __name__ == "__main__":
    unittest.main()