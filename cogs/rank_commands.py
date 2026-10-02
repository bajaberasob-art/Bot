"""Phase 6 PRIME rank commands. No XP writes, dashboard, or public leaderboard."""
import asyncio
import logging
import math
from collections import OrderedDict
from time import monotonic

import discord
from discord import app_commands
from discord.ext import commands

import database
from cogs.card_generator import generate_rank_card
from cogs.utilities import ShortcutInteraction
from interaction_runtime import send_interaction_message
from level_progression import xp_required

logger = logging.getLogger("PrimeRankCommands")
RANK_ALIASES = ("level", "lvl", "لفل", "رانك")


class RankUnavailable(Exception):
    """A safe user-facing denial, not a bot failure."""


class CommandInteraction:
    """Apply the existing /top policy to component clicks without mutating itx."""
    def __init__(self, interaction, command):
        self.original, self.command = interaction, command

    def __getattr__(self, name):
        return getattr(self.original, name)


class LeaderboardView(discord.ui.View):
    def __init__(self, cog, owner_id, guild_id, mode):
        super().__init__(timeout=120)
        self.cog, self.owner_id, self.guild_id = cog, owner_id, guild_id
        self.message = None
        self.busy = False
        self.set_mode(mode)

    def set_mode(self, mode):
        for child in self.children:
            child.style = (discord.ButtonStyle.primary
                           if child.label.casefold() == mode else discord.ButtonStyle.secondary)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await send_interaction_message(
                interaction, "هذا التحكم لصاحب الأمر فقط؛ استخدم /top لفتح قائمتك.", ephemeral=True)
            return False
        return True

    async def switch(self, interaction, mode):
        try:
            guild = self.cog.guild_for(interaction)
            if guild.id != self.guild_id:
                raise RankUnavailable("هذه القائمة لم تعد متاحة في هذا السيرفر.")
            if self.busy:
                raise RankUnavailable("يرجى انتظار تحميل القائمة الحالية.")
            retry = self.cog.take_cooldown(guild.id, interaction.user.id, "navigation", 2)
            if retry:
                raise RankUnavailable(f"يرجى الانتظار {retry} ثانية قبل تغيير القائمة.")
            self.busy = True
            try:
                await self.cog.defer(interaction, thinking=False)
                utilities = self.cog.bot.get_cog("Utilities")
                command = self.cog.bot.tree.get_command("top")
                if utilities and command:
                    if not await utilities.app_command_interceptor(CommandInteraction(interaction, command)):
                        return
                settings = await self.cog.settings_for(interaction, "top")
                embed = await self.cog.leaderboard_embed(guild, mode, settings)
                self.set_mode(mode)
                await interaction.message.edit(embed=embed, view=self)
            finally:
                self.busy = False
        except RankUnavailable as error:
            await send_interaction_message(interaction, str(error), ephemeral=True)
        except Exception:
            logger.exception("Leaderboard navigation failed guild=%s", self.guild_id)
            await send_interaction_message(
                interaction, "تعذر تحديث المتصدرين الآن؛ حاول مجدداً لاحقاً.", ephemeral=True)

    @discord.ui.button(label="TEXT", style=discord.ButtonStyle.primary)
    async def text_button(self, interaction, button):
        await self.switch(interaction, "text")

    @discord.ui.button(label="VOICE", style=discord.ButtonStyle.secondary)
    async def voice_button(self, interaction, button):
        await self.switch(interaction, "voice")

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class RankCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cooldowns = OrderedDict()
        self._member_locks = [asyncio.Lock() for _ in range(32)]

    def guild_for(self, interaction):
        guild = getattr(interaction, "guild", None)
        if (guild is None or getattr(guild, "unavailable", False)
                or self.bot.get_guild(guild.id) is None):
            raise RankUnavailable("هذا الأمر متاح داخل سيرفر متصل بالبوت فقط.")
        return guild

    def take_cooldown(self, guild_id, user_id, family, seconds):
        key = (guild_id, user_id, family)
        now = monotonic()
        retry = self._cooldowns.get(key, 0) - now
        if retry > 0:
            return math.ceil(retry)
        self._cooldowns[key] = now + seconds
        self._cooldowns.move_to_end(key)
        # Bounded process-local cooldowns; no database writes.
        while len(self._cooldowns) > 20000:
            self._cooldowns.popitem(last=False)
        return 0

    @staticmethod
    async def defer(interaction, thinking=True):
        if not interaction.response.is_done():
            await interaction.response.defer(thinking=thinking)

    async def settings_for(self, interaction, family):
        settings = await database.get_level_settings(interaction.guild.id) or {}
        if not settings.get("is_enabled", True) or not settings.get(f"command_{family}_enabled", True):
            raise RankUnavailable("هذا الأمر معطل في إعدادات المستويات لهذا السيرفر.")
        allowed = {int(value) for value in settings.get(f"command_{family}_channels", [])}
        channel = interaction.channel
        channels = {channel.id, getattr(channel, "parent_id", None)}
        if allowed and not allowed.intersection(channels):
            raise RankUnavailable("هذا الأمر متاح في قنوات المستويات المحددة فقط.")
        return settings

    async def human_members(self, guild):
        # Exclude bots/deleted members before SQL LIMIT, not after the top ten.
        # A partial gateway cache must not silently produce incorrect rankings.
        if not getattr(guild, "chunked", False):
            async with self._member_locks[guild.id % len(self._member_locks)]:
                if not getattr(guild, "chunked", False):
                    try:
                        await asyncio.wait_for(guild.chunk(cache=True), timeout=15)
                    except (discord.HTTPException, asyncio.TimeoutError):
                        raise RankUnavailable("قائمة أعضاء السيرفر غير جاهزة؛ حاول مجدداً بعد قليل.")
        if not getattr(guild, "chunked", False):
            raise RankUnavailable("قائمة أعضاء السيرفر غير مكتملة؛ حاول مجدداً بعد قليل.")
        return {member.id: member for member in guild.members if not member.bot}

    async def target_member(self, guild, user):
        member = guild.get_member(user.id)
        if member is None:
            try:
                member = await asyncio.wait_for(guild.fetch_member(user.id), timeout=5)
            except (discord.HTTPException, asyncio.TimeoutError):
                raise RankUnavailable("لم أجد هذا العضو في السيرفر؛ ربما غادر أو حُذف حسابه.")
        if member.bot:
            raise RankUnavailable("بطاقات وترتيب المستويات مخصصة للأعضاء وليس للبوتات.")
        return member

    async def show_rank(self, interaction, member=None):
        try:
            guild = self.guild_for(interaction)
            retry = self.take_cooldown(guild.id, interaction.user.id, "rank", 8)
            if retry:
                raise RankUnavailable(f"يرجى الانتظار {retry} ثانية قبل إعادة استخدام أمر الرانك.")
            await self.defer(interaction)
            settings = await self.settings_for(interaction, "rank")
            target = await self.target_member(guild, member or interaction.user)
            humans = await self.human_members(guild)
            if target.id not in humans:
                raise RankUnavailable("هذا العضو لم يعد موجوداً في قائمة أعضاء السيرفر.")
            row = await database.get_command_rank_snapshot(guild.id, target.id, list(humans))
            card_settings = dict(settings)
            for key in ("total_messages", "total_voice_seconds", "current_streak"):
                card_settings[key] = row.get(key, 0)
            image = await generate_rank_card(
                target, row["text_level"], row["text_xp"], xp_required(row["text_level"]),
                row["rank"], row["total_members"], card_settings)
            embed = discord.Embed(title="PRIME • بطاقة المستوى", color=0x6366F1)
            embed.set_image(url="attachment://prime-rank.png")
            seconds = int(row.get("total_voice_seconds", 0) or 0)
            embed.add_field(name="الرسائل", value=f"{int(row.get('total_messages', 0) or 0):,}")
            embed.add_field(name="وقت الصوت", value=f"{seconds // 3600}h {(seconds % 3600) // 60}m")
            embed.add_field(name="السلسلة اليومية", value=f"{int(row.get('current_streak', 0) or 0):,} days")
            attachment = discord.File(image, filename="prime-rank.png")
            try:
                await send_interaction_message(
                    interaction, file=attachment, embed=embed,
                    allowed_mentions=discord.AllowedMentions.none())
            finally:
                attachment.close()
                image.close()
        except RankUnavailable as error:
            await send_interaction_message(interaction, str(error), ephemeral=True)
        except Exception:
            logger.exception("Rank card command failed guild=%s", getattr(interaction.guild, "id", None))
            await send_interaction_message(
                interaction, "تعذر إنشاء بطاقة PRIME الآن؛ حاول مجدداً لاحقاً.", ephemeral=True)

    async def leaderboard_embed(self, guild, mode, settings):
        if mode not in {"text", "voice"}:
            raise RankUnavailable("اختر TEXT أو VOICE.")
        humans = await self.human_members(guild)
        rows = await database.get_command_level_leaderboard(guild.id, list(humans), mode)
        try:
            color = discord.Color.from_str(settings.get("bot_embed_color", "#6366F1"))
        except (ValueError, TypeError):
            color = discord.Color(0x6366F1)
        embed = discord.Embed(title=f"PRIME • {mode.upper()} TOP 10", color=color)
        lines = []
        for position, row in enumerate(rows, 1):
            member = guild.get_member(row["user_id"])
            if member is None or member.bot:
                # A member can leave while the query is running.
                continue
            name = discord.utils.escape_mentions(
                discord.utils.escape_markdown(member.display_name[:50])).replace("\n", " ")
            lines.append(f"**#{position}** · {name} — **Lv {row['level']:,}** · **{row['xp']:,} XP**")
        embed.description = "\n".join(lines) or "لا يوجد أعضاء لديهم XP في هذه القائمة بعد."
        embed.set_footer(text="أعلى 10 أعضاء • البوتات والأعضاء المغادرون مستبعدون • ترتيب التعادل حسب ID")
        return embed

    async def show_top(self, interaction, mode="text"):
        view = None
        try:
            guild = self.guild_for(interaction)
            retry = self.take_cooldown(guild.id, interaction.user.id, "top", 5)
            if retry:
                raise RankUnavailable(f"يرجى الانتظار {retry} ثانية قبل إعادة استخدام /top.")
            await self.defer(interaction)
            settings = await self.settings_for(interaction, "top")
            embed = await self.leaderboard_embed(guild, mode, settings)
            view = LeaderboardView(self, interaction.user.id, guild.id, mode)
            view.message = await send_interaction_message(
                interaction, embed=embed, view=view, allowed_mentions=discord.AllowedMentions.none())
            if view.message is None:
                view.stop()
        except RankUnavailable as error:
            await send_interaction_message(interaction, str(error), ephemeral=True)
        except Exception:
            if view is not None:
                view.stop()
            logger.exception("Leaderboard command failed guild=%s", getattr(interaction.guild, "id", None))
            await send_interaction_message(
                interaction, "تعذر تحميل المتصدرين الآن؛ حاول مجدداً لاحقاً.", ephemeral=True)

    @app_commands.command(name="rank", description="عرض بطاقة PRIME ومستوى العضو")
    @app_commands.guild_only()
    @app_commands.describe(member="العضو المطلوب، أو اتركه فارغاً لعرض بطاقتك")
    async def rank_slash(self, interaction: discord.Interaction, member: discord.Member | None = None):
        await self.show_rank(interaction, member)

    @commands.command(name="rank", aliases=list(RANK_ALIASES), ignore_extra=False)
    @commands.guild_only()
    async def rank_prefix(self, ctx: commands.Context, member: str = None):
        # Optional[Member] converters can silently fall back to "self" for an
        # invalid argument. Explicit conversion keeps missing targets explicit.
        if member is not None:
            member = await commands.MemberConverter().convert(ctx, member)
        await self.show_rank(ShortcutInteraction(ctx.message, self.rank_slash), member)

    @app_commands.command(name="top", description="أعلى 10 أعضاء في مستويات PRIME النصية أو الصوتية")
    @app_commands.guild_only()
    @app_commands.choices(mode=[app_commands.Choice(name="TEXT", value="text"),
                               app_commands.Choice(name="VOICE", value="voice")])
    async def top_slash(self, interaction: discord.Interaction, mode: str = "text"):
        await self.show_top(interaction, mode)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            message = "لم أجد هذا العضو؛ استخدم منشن أو ID لعضو موجود في السيرفر."
        elif isinstance(error, commands.NoPrivateMessage):
            message = "هذا الأمر متاح داخل السيرفرات فقط."
        else:
            message = "تعذر تنفيذ أمر الرانك الآن."
        try:
            await ctx.send(message, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException:
            logger.warning("Cannot send prefix rank error")


async def setup(bot):
    await bot.add_cog(RankCommands(bot))


async def publish_rank_commands(bot, guild=None):
    """Upsert only Phase 6 commands, never bulk-replace unrelated registrations.

    Called after all cogs load when broad sync is disabled. Compare signatures
    first so normal restarts do not rewrite unchanged Discord registrations.
    """
    fields = ("name", "description", "type", "options", "default_member_permissions", "dm_permission")
    def signature(payload):
        return {key: payload.get(key) for key in fields}
    try:
        remote = await bot.tree.fetch_commands(guild=guild)
        existing = {command.name: command for command in remote}
        changed = 0
        for name in ("rank", "top"):
            command = bot.tree.get_command(name)
            if command is None:
                raise RuntimeError(f"local /{name} command is missing")
            payload = command.to_dict(bot.tree)
            previous = existing.get(name)
            if previous and signature(previous.to_dict()) == signature(payload):
                continue
            if guild is None:
                await bot.http.upsert_global_command(bot.application_id, payload)
            else:
                await bot.http.upsert_guild_command(bot.application_id, guild.id, payload)
            changed += 1
        logger.info("PRIME /rank and /top registrations ready (%s updated)", changed)
        return True
    except Exception:
        logger.exception("Cannot register PRIME /rank and /top; existing Discord commands are untouched")
        return False