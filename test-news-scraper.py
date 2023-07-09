import discord
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import json
import html

# Load configuration from the JSON file
with open('config.json') as config_file:
    config = json.load(config_file)

# Retrieve configuration values
WEBHOOK_URL = config['webhook_url']
WEBSITE_URL = config['website_url']
LOG_FILE = config['log_file']
CONCURRENCY_LIMIT = config['concurrency_limit']

# Initialize the Discord client and webhook
client = discord.Webhook.partial(WEBHOOK_URL, adapter=discord.RequestsWebhookAdapter())

# Configure the logging module
logging.basicConfig(filename='app.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')


class WebsiteScraper:
    """
    A class responsible for scraping website content.

    Attributes:
        semaphore (asyncio.Semaphore): A semaphore to limit concurrent requests.

    Methods:
        scrape(): Fetches and extracts information from the website.
    """

    def __init__(self):
        self.semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def scrape(self):
        """
        Fetches and extracts information from the website.

        Returns:
            list: A list of sanitized and formatted information extracted from the website.
        """
        try:
            async with self.semaphore, self.session.get(WEBSITE_URL) as response:
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
                try:
                    header = item.find('h2').get_text(strip=True)
                    header = f"**{html.unescape(header)}**"
                    summary = item.find('div', class_='news__summary').get_text(strip=True)
                    summary = html.unescape(summary)
                    formatted_info.append(f'{header}\n{summary}\n')
                except AttributeError:
                    logging.error(f"Error extracting information from HTML element: {item}")

            return formatted_info

        except aiohttp.ClientError as e:
            logging.error(f"Failed to connect to the website. Error: {str(e)}")
            return [f"ERROR: Failed to connect to the website.\n{str(e)}"]
        except Exception as e:
            logging.error(f"An unexpected error occurred. Error: {str(e)}")
            return [f"ERROR: An unexpected error occurred.\n{str(e)}"]


class LogFileHandler:
    """
    A class responsible for handling the log file.

    Methods:
        read_log_file(): Reads the existing log file and returns a set of titles.
        append_to_log_file(title): Appends a title to the log file.
    """

    @staticmethod
    def read_log_file():
        """
        Reads the existing log file and returns a set of titles.

        Returns:
            set: A set of titles from the log file.
        """
        try:
            with open(LOG_FILE, 'r') as file:
                return {line.strip() for line in file}
        except FileNotFoundError:
            return set()
        except Exception as e:
            logging.error(f"Error reading log file. Error: {str(e)}")
            return set()

    @staticmethod
    def append_to_log_file(title):
        """
        Appends a title to the log file.

        Args:
            title (str): The title to be appended to the log file.
        """
        try:
            with open(LOG_FILE, 'a') as file:
                file.write(f'{title}\n')
        except Exception as e:
            logging.error(f"Error appending to log file. Error: {str(e)}")


class DiscordNotifier:
    """
    A class responsible for sending messages to Discord.

    Methods:
        send_message(message): Sends a message to the Discord server.
    """

    @staticmethod
    async def send_message(message):
        """
        Sends a message to the Discord server.

        Args:
            message (str): The message to be sent to the Discord server.
        """
        await client.send(f"{message}")


async def main():
    """
    The main functionis there a specific part of the code you would like me to optimize?
