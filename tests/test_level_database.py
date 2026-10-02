import os
import unittest

import database


class LevelDatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        database.DB_NAME = f"/tmp/lona_level_phase1_{os.getpid()}.db"
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)
        await database.init_db()

    async def test_level_tables_indexes_and_defaults(self):
        async with database.connect() as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ) as cur:
                tables = {row[0] for row in await cur.fetchall()}
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ) as cur:
                indexes = {row[0] for row in await cur.fetchall()}
        self.assertTrue(
            {
                "level_settings",
                "user_levels",
                "level_role_rewards",
                "level_multipliers",
                "level_blacklist",
            }.issubset(tables)
        )
        self.assertTrue(
            {
                "idx_user_levels_text",
                "idx_user_levels_voice",
                "idx_level_role_rewards_guild",
                "idx_level_multipliers_guild",
                "idx_level_blacklist_guild",
            }.issubset(indexes)
        )

        self.assertIsNone(await database.get_level_settings(700))
        settings = await database.create_default_level_settings(700)
        self.assertEqual(settings["guild_id"], 700)
        self.assertEqual(settings["is_enabled"], 1)
        self.assertEqual(settings["command_rank_channels"], [])
        self.assertEqual(
            settings["command_rank_aliases"],
            ["rank", "level", "لفل", "رانك"],
        )
        self.assertEqual(
            settings["command_top_aliases"],
            ["top", "توب", "متصدرين"],
        )
        self.assertEqual(settings["weekly_reset_day"], "Friday")
        self.assertEqual(await database.get_level_settings(700), settings)

    async def test_level_settings_update_is_partial_and_validated(self):
        settings = await database.update_level_settings(
            701,
            {
                "xp_multiplier": 2.25,
                "command_rank_channels": ["1001", "1002"],
                "command_rank_aliases": ["rank", "رتبة"],
                "web_leaderboard_enabled": 0,
            },
        )
        self.assertEqual(settings["xp_multiplier"], 2.25)
        self.assertEqual(settings["command_rank_channels"], ["1001", "1002"])
        self.assertEqual(settings["command_rank_aliases"], ["rank", "رتبة"])
        self.assertEqual(settings["web_leaderboard_enabled"], 0)
        self.assertEqual(settings["weekly_reset_day"], "Friday")
        with self.assertRaises(ValueError):
            await database.update_level_settings(701, {"guild_id": 999})
        with self.assertRaises(ValueError):
            await database.update_level_settings(
                701, {"command_top_channels": "not-json"}
            )

    async def test_user_level_crud_and_text_voice_leaderboards(self):
        self.assertIsNone(await database.get_user_level(702, 1))
        first = await database.create_user_level(702, 1)
        self.assertEqual(first["text_xp"], 0)
        self.assertEqual(first["voice_level"], 0)
        await database.create_user_level(702, 2)
        await database.create_user_level(702, 3)
        await database.update_user_level(
            702,
            1,
            {
                "text_xp": 150,
                "text_level": 4,
                "voice_xp": 60,
                "voice_level": 2,
                "total_messages": 15,
            },
        )
        await database.update_user_level(
            702, 2, {"text_xp": 300, "voice_xp": 20, "total_voice_seconds": 90}
        )
        await database.update_user_level(702, 3, {"text_xp": 80, "voice_xp": 95})

        text = await database.get_text_leaderboard(702, 2)
        voice = await database.get_voice_leaderboard(702, 2)
        self.assertEqual([row["user_id"] for row in text], [2, 1])
        self.assertEqual([row["text_xp"] for row in text], [300, 150])
        self.assertEqual([row["user_id"] for row in voice], [3, 1])
        self.assertEqual([row["voice_xp"] for row in voice], [95, 60])
        self.assertEqual((await database.get_user_level(702, 1))["total_messages"], 15)
        with self.assertRaises(ValueError):
            await database.update_user_level(702, 1, {"guild_id": 999})

    async def test_rewards_multipliers_blacklist_and_unrelated_economy(self):
        text_reward = await database.add_level_reward(703, "text", 5, 9001)
        voice_reward = await database.add_level_reward(703, "voice", 3, 9002)
        self.assertEqual(
            [(row["reward_type"], row["role_id"]) for row in await database.get_level_rewards(703)],
            [("text", 9001), ("voice", 9002)],
        )
        with self.assertRaises(ValueError):
            await database.add_level_reward(703, "xp", 5, 9003)
        self.assertTrue(await database.delete_level_reward(703, text_reward["id"]))
        self.assertFalse(await database.delete_level_reward(703, text_reward["id"]))
        self.assertEqual(len(await database.get_level_rewards(703)), 1)

        multiplier = await database.add_level_multiplier(
            703, "role", 9100, 2.0
        )
        await database.add_level_multiplier(703, "channel", 9101)
        self.assertEqual(len(await database.get_level_multipliers(703)), 2)
        self.assertEqual(
            next(
                row["multiplier"]
                for row in await database.get_level_multipliers(703)
                if row["id"] == multiplier["id"]
            ),
            2.0,
        )
        with self.assertRaises(ValueError):
            await database.add_level_multiplier(703, "member", 9102)
        self.assertTrue(
            await database.delete_level_multiplier(703, multiplier["id"])
        )
        self.assertEqual(len(await database.get_level_multipliers(703)), 1)

        blacklist = await database.add_level_blacklist(703, "channel", 9200)
        await database.add_level_blacklist(703, "role", 9201)
        self.assertEqual(len(await database.get_level_blacklist(703)), 2)
        with self.assertRaises(ValueError):
            await database.add_level_blacklist(703, "user", 9202)
        self.assertTrue(
            await database.delete_level_blacklist(703, blacklist["id"])
        )
        self.assertEqual(len(await database.get_level_blacklist(703)), 1)

        wallet = await database.get_or_create_user(42, 703)
        self.assertEqual(wallet["balance"], 100)
        self.assertEqual(await database.update_balance(42, 703, 25), 125)
        async with database.connect() as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name IN ('tickets', 'warnings', 'guild_settings')"
            ) as cur:
                unrelated_tables = {row[0] for row in await cur.fetchall()}
        self.assertEqual(unrelated_tables, {"tickets", "warnings", "guild_settings"})


if __name__ == "__main__":
    unittest.main()