#!/bin/bash

set -e

DOMAINS=("commands" "org_admin" "client_functions" "bot_functions")
LANGS=("en" "fa")

echo "Generating pot files"
for domain in "${DOMAINS[@]}"; do
    pygettext.py -d $domain -o ./helpers/locales/$domain.pot --keyword=${domain}_texts helpers/$domain.py
done

echo "Merging pot into po files"
for domain in "${DOMAINS[@]}"; do
    for lang in "${LANGS[@]}"; do
        if [ -f helpers/locales/$lang/LC_MESSAGES/$domain.po ]; then
            msgmerge --update helpers/locales/$lang/LC_MESSAGES/$domain.po helpers/locales/$domain.pot
        else
            msginit --no-translator --input=helpers/locales/$domain.pot --locale=$lang --output-file=helpers/locales/$lang/LC_MESSAGES/$domain.po
        fi
    done
done

echo "Compiling mo files"
for domain in "${DOMAINS[@]}"; do
    for lang in "${LANGS[@]}"; do
        msgfmt helpers/locales/$lang/LC_MESSAGES/$domain.po -o helpers/locales/$lang/LC_MESSAGES/$domain.mo
    done
done

echo "Localization update complete."