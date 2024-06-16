import gettext

gettext.bindtextdomain('app', 'locales')
gettext.textdomain('app')
_ = gettext.gettext


