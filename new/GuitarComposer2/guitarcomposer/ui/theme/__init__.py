from .default import theme as default_theme

def getTheme():
    # TODO, this would select from a preferences setting
    # which theme to use but right now just return the
    # defualt theme
    return default_theme()
