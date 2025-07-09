#!/bin/bash

echo "generating pot files"
pygettext.py -d commands -o ./helpers/locales/commands.pot --keyword=commands_texts helpers/commands.py &&
pygettext.py -d org_admin -o ./helpers/locales/org_admin.pot --keyword=org_admin_texts helpers/org_admin.py &&
pygettext.py -d client_functions -o ./helpers/locales/client_functions.pot --keyword=client_functions_texts helpers/client_functions.py &&  
pygettext.py -d bot_functions -o ./helpers/locales/bot_functions.pot --keyword=bot_functions_texts helpers/bot_functions.py &&

echo "generating mo files for EN"
msgfmt helpers/locales/en/LC_MESSAGES/commands.po -o helpers/locales/en/LC_MESSAGES/commands.mo && 
msgfmt helpers/locales/en/LC_MESSAGES/org_admin.po -o helpers/locales/en/LC_MESSAGES/org_admin.mo && 
msgfmt helpers/locales/en/LC_MESSAGES/client_functions.po -o helpers/locales/en/LC_MESSAGES/client_functions.mo && 
msgfmt helpers/locales/en/LC_MESSAGES/bot_functions.po -o helpers/locales/en/LC_MESSAGES/bot_functions.mo &&
# msgfmt helpers/locales/en/LC_MESSAGES/general.po -o helpers/locales/en/LC_MESSAGES/general.mo

echo "generating mo files for FA"
msgfmt helpers/locales/fa/LC_MESSAGES/commands.po -o helpers/locales/fa/LC_MESSAGES/commands.mo &&
msgfmt helpers/locales/fa/LC_MESSAGES/org_admin.po -o helpers/locales/fa/LC_MESSAGES/org_admin.mo &&
msgfmt helpers/locales/fa/LC_MESSAGES/client_functions.po -o helpers/locales/fa/LC_MESSAGES/client_functions.mo &&
msgfmt helpers/locales/fa/LC_MESSAGES/bot_functions.po -o helpers/locales/fa/LC_MESSAGES/bot_functions.mo
# msgfmt helpers/locales/fa/LC_MESSAGES/general.po -o helpers/locales/fa/LC_MESSAGES/general.mo