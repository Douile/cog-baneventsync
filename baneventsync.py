import discord

from redbot.core import commands, checks, Config, utils

listener = getattr(commands.Cog, "listener", None)  # red 3.0 backwards compatibility support

if listener is None:  # thanks Sinbad
    def listener(name=None):
        return lambda x: x

class BanEventSync(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.config = Config.get_conf(self, 2348123)
    self.config.register_global(sync_list=[],ban_list=[])

  async def in_sync_list(self, guild):
      sync_list = await self.config.sync_list()
      return guild.id in sync_list

  async def synced_guilds(self):
      sync_list = await self.config.sync_list()
      for id in sync_list:
          guild = self.bot.get_guild(id)
          if guild is not None:
              yield guild

  async def in_ban_list(self, user):
      ban_list = await self.config.ban_list()
      for ban in ban_list:
          if ban['user'] == user.id:
              return True
      return False

  async def sync_ban(self, guild, ban):
      if ban is None or guild is None or ban.user is None or await self.in_ban_list(ban.user):
          return

      print("Syncing ban {0} - {1}".format(ban.user.name, ban.reason))
      await self.save_ban(ban)

      async for g in self.synced_guilds():
        if g == guild:
          continue
        try:
          t_ban = await g.fetch_ban(ban.user)
          continue
        except discord.errors.NotFound: # User is not banned on server g
          pass
        except Exception as e:
          print(e)
          continue # Add proper error handling
        await g.ban(ban.user, reason=ban.reason)

  async def collect_guild_bans(self, guild):
      if guild is None:
          return
      bans = await guild.bans()
      for ban in bans:
          await self.sync_ban(guild, ban)

  async def enact_bans(self, guild):
      ban_list = await self.config.ban_list()
      for ban in ban_list:
          await guild.ban(discord.Object(ban['user']),reason=ban['reason'])

  @listener()
  async def on_member_ban(self, guild, user):
    if not await self.in_sync_list(guild) or await self.in_ban_list(user):
      return

    try:
      ban = await guild.fetch_ban(user)
    except Exception as e:
      print(e)
      return e

    await self.sync_ban(guild, ban)



  @listener()
  async def on_member_unban(self, guild, user):
    if not await self.in_sync_list(guild) or not await self.in_ban_list(user):
      return

    print("Syncing unban {0}".format(user.name))
    await self.save_unban(user)

    async for g in self.synced_guilds():
      if g == guild:
        continue
      try:
        ban = await g.fetch_ban(user)
      except discord.NotFound:
        continue
      except Exception as e:
        print(e)
        continue # Add proper error handling

      try:
        await g.unban(user)
      except Exception as e:
        print(e)
        pass

  @commands.command(name="synctoggle", help="Toggle whether or not a server is synced given its ID")
  @checks.admin()
  async def syncserver(self, ctx, guild_id: int = None, *, dont_collect: bool = False):
      if guild_id is not None:
          guild = self.bot.get_guild(guild_id)
      else:
          guild = ctx.guild
      if guild is not None:
          id = guild.id
      else:
          return await ctx.send("Unknown id {0}".format(guild_id))

      sync_list = await self.config.sync_list()
      in_list = id in sync_list
      if in_list:
          sync_list.remove(id)
          message = "Removed `{0}` from the sync list".format(guild.name)
      else:
          sync_list.append(id)
          message = "Added `{0}` to the sync list".format(guild.name)
          await self.enact_bans(guild)
          if not dont_collect:
              await self.collect_guild_bans(guild)

      await self.config.sync_list.set(sync_list)
      await ctx.send(message)

  @commands.command(name="synclist", help="Print list of server set to be synced")
  @checks.admin()
  async def synclist(self, ctx):
      sync_list = await self.config.sync_list()
      message = "Synced servers: "
      for id in sync_list:
          guild = self.bot.get_guild(id)
          message += "**{0}** [{1}], ".format(guild.name, id)
      await ctx.send(message[:-2])

  @commands.command(name="syncedbans", help="Print a list of bans and reasons that have been synced")
  @checks.admin()
  async def syncedbans(self, ctx):
      ban_list = await self.config.ban_list()
      message = "Synced bans:\n"
      for ban in ban_list:
          message += "- <@{0}> `{1}`\n".format(ban['user'],ban['reason'])
      for content in utils.chat_formatting.pagify(message):
          await ctx.send(content)

  async def save_ban(self, ban):
      ban_list = await self.config.ban_list()
      ban_list.append({'user': ban.user.id, 'reason': ban.reason})
      await self.config.ban_list.set(ban_list)

  async def save_unban(self, user):
      ban_list = await self.config.ban_list()
      for ban in ban_list:
          if ban['user'] == user.id:
              ban_list.remove(ban)
      await self.config.ban_list.set(ban_list)

  # @commands.command()
  # @checks.admin()
  # async def testban(self, ctx, id: int = None, reason: str = None):
  #     await ctx.guild.ban(discord.Object(id),reason=reason)

  # @commands.Command()
  # async def globalban(self, ctx, *, member: discord.Member = None, id: str = None, reason: str = None, delete_days: int = 1):
  #   if member is not None:
  #     user = member
  #   elif id is not None:
  #     user = discord.Object(id)
  #   else:
  #     return Error("You must mention a member or provide a snowflake")
  #
  #   for guild in self.synced_guilds():
  #     if guild == ctx.guild:
  #         continue
  #     try:
  #         await guild.ban(user, reason=reason, delete_message_days=delete_days)
  #     except Exception as e:
  #         continue
  #   # store id in database using user.id

def setup(bot):
    bot.add_cog(BanEventSync(bot))
