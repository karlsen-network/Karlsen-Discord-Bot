# Karlsen Network Discord Bot

This Discord bot is designed to help manage and moderate the server while keeping members informed with live network statistics.

## Features

- **Channel Updates**: Automatically updates channel names with the latest Karlsen Network statistics.
- **Member Management**: Handles member verification and anti-spam measures.
- **Username Monitoring**: Monitors usernames and nicknames for flagged keywords and bans users if a keyword is found.
- **Keyword Ban List**: Monitors messages for banned keywords and takes action if any are found.

## Bot Commands

- `/b <address>`: Check the balance of a specified wallet address.
- `/c <hashrate_in_MH/s>`: Calculates and displays estimated mining rewards based on the provided hashrate in MH/s
- `/commands`: List all available bot commands.

## Username Monitoring

The bot monitors usernames and nicknames for the following flagged keywords:

- "Name1", "Name2", "Name3", "Name4", "Name5"
- Add more keywords as needed

If a username or nickname contains any of these keywords, the user is automatically banned and a log entry is created.

We have repeatedly observed a recurring behavior where phishing scammers frequently join using the display-name "announcement"

## Keyword Ban List

The bot monitors messages for the following banned keywords:

- "Word1", "Word2", "Word3", "Word4", "Word5"
- Add more keywords as needed

If a message contains any of these banned keywords, the message is deleted, the user is banned, and a log entry is created.

## License

Distributed under the MIT License. See `LICENSE` for more information.
