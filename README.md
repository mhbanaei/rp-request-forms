# rp-request-forms
A set of modular Discord bot commands designed for RP servers to handle requests such as weapon permits, driver's licenses, and recruitment.

---

# 🔧 Basic Configuration
```
TOKEN = "YourDiscordToken"
GUILD_ID = YourDiscordToken
LOG_CHANNEL_ID = YourDiscordToken
ALLOWED_ROLE_ID = YourDiscordToken
ACCEPT_CHANNEL_ID = YourDiscordToken
DENY_CHANNEL_ID = YourDiscordToken
```

* These variables are for your bot's setup.

`TOKEN:` The bot's access token.

`GUILD_ID:` The server ID.

`LOG_CHANNEL_ID:` The channel for logging activity.

`ALLOWED_ROLE_ID:` Role ID allowed to approve/deny requests.

`ACCEPT_CHANNEL_ID` / DENY_CHANNEL_ID: Channels where accepted or denied requests are sent.

# ExplanationModal Class

* This is a modal (pop-up form) shown when someone clicks Accept or Deny.

* Constructor (__init__):

Takes the applicant, original embed (form), reviewer (the one who clicks), action type (accept or deny), and the original message.

Adds a text input field for optional explanation.

* on_submit():

`Generates a timestamp and case number.`

`Extracts user info from the embed.`

`Creates a new embed with results (accepted or denied).`

`Sends it to the appropriate channel.`

`Sends a DM to the applicant.`

`Removes buttons from the original message.`

`Confirms action to the reviewer privately.`

# ApprovalView Class

* Contains the Accept and Deny buttons.

Contains the Accept and Deny buttons.

`accept_button()` / `deny_button():`

* Check if the clicking user has permission (correct role).

* Extract the user ID from the embed's footer.

* Create and show the ExplanationModal with appropriate action.

# on_ready() Event

* When the event is ready :

Add the persistent view so Accept/Deny buttons stay active after restarts.
Syncs slash commands with Discord.

