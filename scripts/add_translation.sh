#!/bin/bash

# Interactive script to add a translation key to all languages for a selected domain
# Usage: ./add_translation.sh

set -e

# List available domains
DOMAINS=( $(ls ../helpers/locales/*.pot | xargs -n1 basename | sed 's/\.pot$//') )
echo "Available domains:"
for i in "${!DOMAINS[@]}"; do
    echo "$((i+1)). ${DOMAINS[$i]}"
done

# Prompt user to select a domain
while true; do
    read -p "Enter the number of the domain you want to use: " domain_idx
    if [[ "$domain_idx" =~ ^[0-9]+$ ]] && (( domain_idx >= 1 && domain_idx <= ${#DOMAINS[@]} )); then
        domain="${DOMAINS[$((domain_idx-1))]}"
        break
    else
        echo "Invalid selection. Please enter a valid number."
    fi
done

echo "Selected domain: $domain"

# Prompt for key and values
read -p "Enter the translation key: " key
read -p "Enter the English value: " en_value
read -p "Enter the Farsi value: " fa_value

PO_EN="../helpers/locales/en/LC_MESSAGES/$domain.po"
PO_FA="../helpers/locales/fa/LC_MESSAGES/$domain.po"

# Add to English .po
if ! grep -q "msgid \"$key\"" "$PO_EN"; then
    echo -e "\nmsgid \"$key\"\nmsgstr \"$en_value\"" >> "$PO_EN"
    echo "Added $key to $PO_EN"
else
    echo "$key already exists in $PO_EN"
fi

# Add to Farsi .po
if ! grep -q "msgid \"$key\"" "$PO_FA"; then
    echo -e "\nmsgid \"$key\"\nmsgstr \"$fa_value\"" >> "$PO_FA"
    echo "Added $key to $PO_FA"
else
    echo "$key already exists in $PO_FA"
fi

# Run localization.sh to update and compile
./localization.sh 