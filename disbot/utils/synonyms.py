from __future__ import annotations

# Maps canonical command name → synonyms that should resolve to it.
# Only add entries where genuine synonyms exist; skip commands with no
# natural alternatives.
COMMAND_SYNONYMS: dict[str, list[str]] = {
    "help": ["hilfe", "commands", "cmds", "cmd", "befehle"],
    "rank": [
        "level",
        "lvl",
        "xp",
        "stats",
        "score",
        "myscore",
        "mrank",
        "myrank",
        "progres",
        "progress",
    ],
    "leaderboard": [
        "top",
        "rankings",
        "scores",
        "highscore",
        "highscores",
        "scoreboard",
    ],
    "blackjack": ["bj", "21", "cards", "cardgame"],
    "rps": ["rockpaperscissors", "rock", "schere", "stein", "papier"],
    "serverstats": ["serverstat", "serv"],
    "serverinfo": ["sinfo"],
    "userinfo": ["uinfo", "whois", "user"],
    "clear": ["purge", "clean", "delete", "löschen"],
    "warn": ["warning", "verwarnen"],
    "ban": ["bannieren", "banish", "sperren"],
    "kick": ["rauswerfen", "boot", "entfernen"],
    "timeout": ["mute", "stumm", "stumschalten"],
    "unban": ["entbannen"],
    "poll": ["vote", "abstimmung", "umfrage"],
    "assignroles": ["updateroles", "roleupdate"],
    "rolesettings": ["roleconfig", "rolethresholds"],
    "createrole": ["newrole", "addrole", "makerole"],
    "deleterole": ["removerole", "rmrole"],
    "givexp": ["addxp", "grantxp"],
    "resetxp": ["clearxp"],
    "xpconfig": ["xpsettings"],
    "restart": ["reboot", "restar"],
    "loglevel": ["loglvl", "setloglevel"],
    "remind": ["reminder", "remindme", "erinnerung"],
    "roles": ["rolelist", "listroles"],
    "invite": ["einladen"],
    "avatar": ["pfp", "bild"],
    "cleanuphistory": ["cleanhistory", "bereinigen"],
    "word": ["addword", "removeword", "prohibit", "blockword", "wordlist"],
}


def find_command(query: str) -> str | None:
    """Return the canonical command name if *query* matches a known synonym.

    Returns None if no synonym matches (so the caller can fall through to
    normal 'command not found' handling).
    """
    q = query.lower().strip()
    # Direct synonym lookup
    for cmd, aliases in COMMAND_SYNONYMS.items():
        if q in aliases:
            return cmd
    return None
