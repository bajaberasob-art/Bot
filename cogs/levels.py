"""Phase 2: text XP only. No commands, voice listeners or announcement UI."""
import asyncio
import logging
import math
import random
from time import monotonic
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import discord
from discord.ext import commands

import database
from level_progression import text_progress

logger = logging.getLogger("LonaLevels")
MAX_MULTIPLIER = 100.0
MAX_COOLDOWN = 86400


@dataclass(frozen=True)
class TextLevelUp:
    guild: Any
    member: Any
    old_level: int
    new_level: int
    current_xp: int
    xp_required_for_next_level: int
    next_level_total_xp: int


@dataclass(frozen=True)
class TextMilestone:
    guild: Any
    member: Any
    current_level: int
    current_xp: int
    next_level: int
    next_level_required_xp: int
    percentage: float
    next_level_total_xp: int


def bounded_multiplier(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return 1.0
    if not math.isfinite(value) or value < 0:
        return 1.0
    return min(value, MAX_MULTIPLIER)


def boost_is_active(expires_at: Any, now: datetime) -> bool:
    if not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry > now
    except (TypeError, ValueError):
        return False


def resolve_multiplier(settings: dict, multipliers: list, role_ids: set,
                       channel_ids: set, now: datetime) -> float:
    factors = [bounded_multiplier(settings.get("xp_multiplier", 1))]
    # Sorted IDs make multiplication deterministic even for duplicate targets.
    for item in sorted(multipliers, key=lambda row: row["id"]):
        if (
            item["target_type"] == "role" and item["target_id"] in role_ids
            or item["target_type"] == "channel" and item["target_id"] in channel_ids
        ):
            factors.append(bounded_multiplier(item["multiplier"]))
    if boost_is_active(settings.get("boost_expires_at"), now):
        factors.append(bounded_multiplier(settings.get("boost_multiplier", 1)))
    # Clamp only the final product so fractional factors remain meaningful.
    if any(factor == 0 for factor in factors):
        return 0.0
    return min(math.prod(factors), MAX_MULTIPLIER)


class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Bounded LRU: eviction never bypasses the persisted cooldown guard.
        self._cooldowns: OrderedDict[tuple[int, int], float] = OrderedDict()
        self._cooldown_capacity = 50000
        # Fixed stripes avoid a growing lock object per member.
        self._locks = [asyncio.Lock() for _ in range(256)]

    @staticmethod
    def cooldown_seconds(settings: dict) -> int:
        try:
            return max(0, min(MAX_COOLDOWN, int(settings.get("message_cooldown_seconds", 60))))
        except (TypeError, ValueError, OverflowError):
            return 60

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        key = (message.guild.id, message.author.id)
        try:
            async with self._locks[hash(key) % len(self._locks)]:
                await self._process_message(message, key)
        except Exception:
            # Only this listener fails; commands, tickets and automod continue.
            logger.exception("Text XP failed for guild=%s member=%s", *key)

    async def _process_message(self, message: discord.Message, key: tuple):
        now_tick = monotonic()
        cached = self._cooldowns.get(key)
        if cached is not None and now_tick < cached:
            return
        self._cooldowns.pop(key, None)
        settings = await database.get_level_settings(key[0])
        if settings is None:
            settings = await database.create_default_level_settings(key[0])
        if not settings["is_enabled"]:
            return
        role_ids = {role.id for role in message.author.roles}
        channel_ids = {message.channel.id}
        # Parent-channel configuration applies to its threads too.
        parent_id = getattr(message.channel, "parent_id", None)
        if parent_id:
            channel_ids.add(parent_id)
        blacklist = await database.get_level_blacklist(key[0])
        if any(
            row["target_type"] == "role" and row["target_id"] in role_ids
            or row["target_type"] == "channel" and row["target_id"] in channel_ids
            for row in blacklist
        ):
            return
        now = datetime.now(timezone.utc)
        multipliers = await database.get_level_multipliers(key[0])
        factor = resolve_multiplier(settings, multipliers, role_ids, channel_ids, now)
        xp = int(random.randint(15, 25) * factor)
        if xp <= 0:
            return
        cooldown = self.cooldown_seconds(settings)
        award = await database.award_text_xp(*key, xp, now, cooldown)
        if award is None:
            # Restart/LRU miss: recover the actual remaining cooldown once.
            row = await database.get_user_level(*key)
            last = datetime.fromisoformat(str(row["last_message_at"]).replace("Z", "+00:00"))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            remaining = max(0, cooldown - (now - last).total_seconds())
            self._remember_cooldown(key, monotonic() + remaining)
            return
        self._remember_cooldown(key, monotonic() + cooldown)
        progress = text_progress(award["text_xp"])
        if award["text_level"] > award["old_level"]:
            await self.apply_text_rewards(message.author, award["text_level"], settings)
            self.emit_level_up(TextLevelUp(
                message.guild, message.author, award["old_level"], award["text_level"],
                award["text_xp"], progress["xp_required"], progress["next_level_total_xp"],
            ))
        elif progress["percentage"] >= 90:
            # One notification on crossing 90%, not every following message.
            previous = text_progress(award["old_xp"])
            if previous["level"] == progress["level"] and previous["percentage"] < 90:
                self.emit_milestone(TextMilestone(
                    message.guild, message.author, award["text_level"], award["text_xp"],
                    award["text_level"] + 1, progress["xp_required"],
                    progress["percentage"], progress["next_level_total_xp"],
                ))

    def _remember_cooldown(self, key: tuple, deadline: float):
        # Lazily purge old entries; the map is hard bounded even when idle.
        self._cooldowns[key] = deadline
        self._cooldowns.move_to_end(key)
        while len(self._cooldowns) > self._cooldown_capacity:
            self._cooldowns.popitem(last=False)

    def emit_level_up(self, event: TextLevelUp):
        """One range event represents every crossed level, including jumps."""
        self.bot.dispatch("lona_text_level_up", event)

    def emit_milestone(self, event: TextMilestone):
        self.bot.dispatch("lona_text_milestone", event)

    async def apply_text_rewards(self, member: discord.Member, level: int, settings: dict):
        try:
            await self._apply_text_rewards(member, level, settings)
        except Exception:
            logger.exception("Text reward failure guild=%s member=%s", member.guild.id, member.id)

    async def _apply_text_rewards(self, member: discord.Member, level: int, settings: dict):
        rewards = [
            row for row in await database.get_level_rewards(member.guild.id)
            if row["reward_type"] == "text" and row["level_required"] <= level
        ]
        if not rewards:
            return
        rewards.sort(key=lambda row: (row["level_required"], row["id"]))
        single = bool(settings["rewards_single_highest"])
        selected = rewards[-1:] if single else rewards
        held = {role.id for role in member.roles}
        highest_granted = False
        for reward in selected:
            role = member.guild.get_role(reward["role_id"])
            if role is None:
                logger.warning("Deleted text reward role %s in guild %s", reward["role_id"], member.guild.id)
                continue
            if role.id in held:
                highest_granted = True
                continue
            if not self._manageable(member.guild, role):
                logger.warning("Cannot manage text reward role %s in guild %s", role.id, member.guild.id)
                continue
            try:
                await member.add_roles(role, reason="Lona text level reward")
                held.add(role.id)
                highest_granted = True
            except discord.HTTPException:
                logger.warning("Cannot grant text reward role %s", role.id, exc_info=True)
        # Never strip old rewards if granting the replacement failed.
        if single and highest_granted:
            selected_id = selected[0]["role_id"]
            lower_ids = {
                row["role_id"] for row in rewards
                if row["level_required"] < selected[0]["level_required"]
                and row["role_id"] != selected_id
            }
            # Preserve any role also configured as a voice reward.
            voice_ids = {
                row["role_id"] for row in await database.get_level_rewards(member.guild.id)
                if row["reward_type"] == "voice"
            }
            for role_id in sorted(lower_ids - voice_ids):
                role = member.guild.get_role(role_id)
                if role and role_id in held and self._manageable(member.guild, role):
                    try:
                        await member.remove_roles(role, reason="Lona highest text reward")
                    except discord.HTTPException:
                        logger.warning("Cannot remove text reward role %s", role_id, exc_info=True)

    @staticmethod
    def _manageable(guild: discord.Guild, role: discord.Role) -> bool:
        me = guild.me
        return bool(
            me and me.guild_permissions.manage_roles and not role.managed
            and not role.is_default() and role < me.top_role
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))