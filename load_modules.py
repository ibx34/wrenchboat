from pylint import epylint as lint

extensions = [
    "jishaku",
    "wrenchboat.moderation",
    "wrenchboat.help",
    "wrenchboat.admin",
    "wrenchboat.utility",
    "wrenchboat.settings",
    "wrenchboat.images",
    "wrenchboat.automod",
    "wrenchboat.error",
    "wrenchboat.tags",
    "wrenchboat.highlight",
    "wrenchboat.listeners",
    "wrenchboat.logging",
    "wrenchboat.backups",
    "wrenchboat.purge"
]

for ext in extensions:
    print(ext)
    errors = lint.py_run(f'{ext}.py', return_std=True)  
    print(errors)