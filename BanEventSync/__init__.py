from .BanEventSync import BanEventSync

def setup(bot):
    bot.add_cog(BanEventSync(bot))
