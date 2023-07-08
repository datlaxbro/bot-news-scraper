import discord
import asyncio
import aiohttp
from bs4 import BeautifulSoup

# Discord Webhook URL
WEBHOOK_URL = 'your_webhook_url_here'

# Website URL to scrape
WEBSITE_URL = 'your_website_url_here'

# Log file path
LOG_FILE = 'log.txt'

# Concurrency limit
CONCURRENCY_LIMIT = 5

# Initialize the Discord client and webhook
client = discord.Webhook.partial(WEBHOOK_URL, adapter=discord.RequestsWebhookAdapter())


class WebsiteScraper:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def scrape(self):
        try:
            async with self.semaphore:
                async with aiohttp.ClientSession() as session:
                    async with session.get(WEBSITE_URL) as response:
                        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                        content = await response.text()

                # Parse the HTML content using BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')

                # Find the elements containing the new information
                # Adjust the following code according to the structure of the website
                news_items = soup.find_all('div', class_=lambda cls: cls and cls.startswith('news__item news__tag-'))

                # Extract and format the information
                formatted_info = []
                for item in news_items:
                    header = item.find('h2').text.strip()
                    header = f"**{header}**"
                    summary = item.find('div', class_='news__summary').text.strip()
                    formatted_info.append(f'{header}\n{summary}\n')

                return formatted_info

        except aiohttp.ClientError as e:
            return [f"ERROR: Failed to connect to the website.\n{str(e)}"]
        except Exception as e:
            return [f"ERROR: An unexpected error occurred.\n{str(e)}"]


class LogFileHandler:
    @staticmethod
    def read_log_file():
        try:
            with open(LOG_FILE, 'r') as file:
                return set([line.strip() for line in file.readlines()])
        except FileNotFoundError:
            return set()
        except Exception as e:
            print(f'Error reading log file: {str(e)}')
            return set()

    @staticmethod
    def append_to_log_file(title):
        try:
            with open(LOG_FILE, 'a') as file:
                file.write(f'{title}\n')
        except Exception as e:
            print(f'Error appending to log file: {str(e)}')


class DiscordNotifier:
    @staticmethod
    async def send_message(message):
        await client.send(f"{message}")


async def main():
    scraper = WebsiteScraper()
    log_handler = LogFileHandler()

    # Read existing titles from the log file
    existing_titles = log_handler.read_log_file()

    # Scrape the website
    new_info_list = await scraper.scrape()

    # Check for duplicate titles and format the new information
    new_info = []
    for info in new_info_list:
        if info not in existing_titles:
            new_info.append(info)
            log_handler.append_to_log_file(info)

    # Send the new information or error message to the Discord server
    if new_info:
        formatted_message = '\n'.join(new_info)
        await DiscordNotifier.send_message(formatted_message)
    else:
        await DiscordNotifier.send_message('Sorry :( nothing new today.')


# Run the main script asynchronously
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
