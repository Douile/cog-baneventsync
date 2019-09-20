# BanEventSync
_By Douile_

Ban event sync will sync all bans and unbans between servers set to sync at the time of ban, this means you can use the discord ban button or any bot that issues a ban to ban users.

# Usage

To add a guild to sync list use `[p]synctoggle [guild id]` if you don't provide a guild id the guild in which the message was sent will be used.

**WARNING** When a guild is added to the sync list all its bans will be collected and synced unless the dont_collect option is set e.g. `[p]synctoggle 624371768664129556 true`

You can now carry on as normal, all bans should be synced between servers

To list servers in sync list use the command `[p]synclist`

To list all bans that have been synced use `[p]syncedbans`
