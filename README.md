# Karlsen Network Discord Bot

This Discord bot is designed to manage and interact with the Karlsen Network community. It fetches cryptocurrency data from the Karlsen API, manages various server functions, and integrates with OpenAI's Assistant API to provide AI-driven responses.

## Features

- **Channel Updates**: Automatically updates channel names with the latest Karlsen Network statistics.
- **Member Management**: Handles member verification and provides anti-raid and anti-spam measures.
- **AI Assistance**: Uses OpenAI's Assistant API to respond to user queries and provide AI-driven insights.
- **Username Monitoring**: Monitors usernames and nicknames for flagged keywords and bans users if a keyword is found.
- **Keyword Ban List**: Monitors messages for banned keywords and takes action if any are found.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Bot Commands](#bot-commands)
- [Username Monitoring](#username-monitoring)
- [Keyword Ban List](#keyword-ban-list)
- [APIs Interaction](#apis-interaction)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/karlsen-network/Karlsen-Discord-Bot.git
    cd Karlsen-Discord-Bot
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Configure Your Login Information**:
    ```plaintext
    DISCORD_TOKEN=your_discord_token
    OPENAI_API_KEY=your_openai_api_key
    ASSISTANT_ID=your_assistant_id
    ```

## Configuration

Update the configuration variables in `bot.py` to match your server setup:

- `CATEGORY_ID`
- `ROLE_ID`
- `MEMBER_COUNT_CHANNEL_ID`
- `VERIFICATION_CHANNEL_ID`
- `VERIFIED_ROLE_ID`
- `VERIFICATION_MESSAGE_ID`
- `LOG_CHANNEL_ID`
- `COMMAND_LOG_CHANNEL_ID`

## Usage

Run the bot with the following command:
```sh
python bot.py
```

## Bot Commands

- `/b <address>`: Check the balance of a specified wallet address.
- `/ask <question>`: Ask the OpenAI Assistant a question.
- `/commands`: List all available bot commands.

## Username Monitoring

The bot monitors usernames and nicknames for the following flagged keywords:
- "bannedword1"
- "bannedword2"
- "bannedword3"

If a username or nickname contains any of these keywords, the user is automatically banned and a log entry is created.

We have repeatedly observed a recurring behavior where phishing scammers frequently join using the display-name "announcement"

## Keyword Ban List

The bot monitors messages for the following banned keywords:
- "bannedword1"
- "bannedword2"
- "bannedword3"
- Add more keywords as needed

If a message contains any of these banned keywords, the message is deleted, the user is banned, and a log entry is created.

## APIs Interaction

### Karlsen API

The bot interacts with the Karlsen API to fetch various cryptocurrency statistics such as max supply, circulating supply, hashrate, block reward, halving data, price, and market cap. Here is an example of how the bot fetches the circulating supply:

```python
async def get_circulating_supply():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.karlsencoin.com/info/coinsupply/circulating?in_billion=false', headers={'accept': 'text/plain'}) as response:
            circulating_supply = float(await response.text())
            logging.info(f"Circulating supply fetched: {circulating_supply}")
            return circulating_supply
```

### OpenAI Assistant API

The bot uses the OpenAI Assistant API to generate AI-driven responses to user queries. Here is an example of how the bot interacts with the OpenAI Assistant API:

1. **Create a thread**:
    ```python
    async def create_thread(headers):
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.openai.com/v1/threads', headers=headers) as response:
                if response.status == 200:
                    thread_data = await response.json()
                    logging.debug(f"Thread created successfully with ID: {thread_data['id']}")
                    return thread_data['id']
                else:
                    logging.error(f"Failed to create thread. Response: {await response.text()}")
                    return None
    ```

2. **Send a message to the thread**:
    ```python
    async def send_message_to_thread(headers, thread_id, user_input):
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://api.openai.com/v1/threads/{thread_id}/messages', headers=headers, json={'role': 'user', 'content': user_input}) as response:
                if response.status != 200:
                    logging.error(f"Failed to send message. Response: {await response.text()}")
                logging.debug("Message sent successfully to the thread.")
    ```

3. **Run the thread using the assistant**:
    ```python
    async def run_thread(headers, thread_id):
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://api.openai.com/v1/threads/{thread_id}/runs', headers=headers, json={'assistant_id': ASSISTANT_ID}) as response:
                if response.status == 200:
                    run_data = await response.json()
                    run_id = run_data['id']
                    status = run_data['status']
                    start_time = time.time()
                    logging.debug(f"Thread run initiated with ID: {run_id}, initial status: {status}")
                    while status in ['queued', 'in_progress']:
                        await asyncio.sleep(0.5)
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f'https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}', headers=headers) as check_response:
                                status = (await check_response.json())['status']
                                logging.debug(f"Current status of run ID {run_id}: {status}")
                                if time.time() - start_time > 29:
                                    logging.error("Timeout waiting for the run to complete.")
                                    return run_id, 'timeout'
                    return run_id, status
                else:
                    logging.error(f"Failed to run thread. Response: {await response.text()}")
                    return None, 'error'
    ```

4. **Fetch the final result**:
    ```python
    async def fetch_final_result(headers, thread_id, run_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.openai.com/v1/threads/{thread_id}/messages', headers=headers) as response:
                if response.status == 200:
                    messages_data = await response.json()
                    for message in reversed(messages_data['data']):
                        if message['role'] == 'assistant' and message['content']:
                            content_item = next((c for c in message['content'] if c['type'] == 'text'), None)
                            if content_item and content_item['text']['value']:
                                return content_item['text']['value']
                    logging.error("Assistant's final response not found.")
                    return "Assistant's final response not found."
                else:
                    logging.error(f"Failed to fetch messages. Response: {await response.text()}")
                    return "Failed to fetch messages."
    ```

## Contributing

1. Fork the repository.
2. Create your feature branch.
3. Commit your changes.
4. Push to the branch.
5. Open a pull request.

## License

Distributed under the MIT License. See `LICENSE` for more information.

