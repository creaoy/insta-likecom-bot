""" 
    insta.py - Insta class and helper methods

    insta-likecom-bot v.3.0.6
    Automates likes and comments on an instagram account or tag

    Author: Shine Jayakumar
    Github: https://github.com/shine-jayakumar
    Copyright (c) 2023 Shine Jayakumar
    LICENSE: MIT
"""


from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
# Added for FireFox support
from webdriver_manager.firefox import GeckoDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver import ActionChains
# import chromedriver_binary
from selenium_recaptcha_solver import RecaptchaSolver
import undetected_chromedriver as uc
from emunium import EmuniumSelenium


import os
from pprint import pprint
import re
import time
import random
from datetime import datetime
from sys import platform
import sys
import base64

from modules.applogger import AppLogger
from typing import List, Tuple
from functools import wraps
from enum import Enum
from modules.constants import INSTA_URL
from modules.helpers import *
from modules.locators import (
    LoginLocators, PostLocators, StoryLocators, ReelsLocators, 
    FollowersLocators, AccountLocators, LOCATORS
)


logger = AppLogger(__name__).getlogger()

# suppress webdriver manager logs
os.environ['WDM_LOG_LEVEL'] = '0'


class Seconds(Enum):
    Year: int = 31536000
    Month: int = 2592000
    Day: int = 86400
    Hour: int = 3600
    Min: int = 60
    Sec: int = 1


class TParam(Enum):
    y: str = 'year'
    M: str = 'month'
    d: str = 'day'
    h: str = 'hour'
    m: str = 'min'
    s: str = 'sec'



def retry(func):
    """
    Adds retry functionality to functions
    """
    # wrapper function
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_tries = 2
        attempt = 1
        status = False
        while not status and attempt < max_tries:
            logger.info(f'[{func.__name__}]: Attempt - {attempt}')
            status = func(*args, **kwargs)
            if status == 'skip_retry':
                status = False
                break         
            if status == None:
                break           
            attempt +=  1
        return status
    return wrapper

@retry
def click_element_with_retry(element):
    try:
        element.click()
        return True  # Click successful, exit the loop
    except StaleElementReferenceException:
        print("[click_element_with_retry]: Attempt failed due to stale element reference. Retrying...")
        time.sleep(1)  # Wait for a short duration before retrying

def random_wait(base_wait: int, variance: int = 1) -> int:
    """
    Generates a random wait time around a base value.

    Args:
    base_wait (int): The base wait time in seconds.
    variance (int): The maximum deviation from the base wait time, in seconds.

    Returns:
    int: A random wait time.
    """
    return random.randint(base_wait - variance, base_wait + variance)

class Insta:
    def __init__(
            self, username: str, password: str, timeout: int = 30, 
            browser: str = 'chrome', headless: bool = False, profile: str = None, proxy: str = None) -> None:
        """Insta class
        
        Automates Instagram interaction

        Args:
            username (str): Instagram username
            password (str): Instagram password
            timeout (int, optional): timeout for finding elements. Defaults to 30.
            browser (str, optional): browser - 'chrome', 'firefox'. Defaults to 'chrome'.
            headless (bool, optional): launch browser in headless mode. Defaults to False.
            profile (str, optional): browser profile. Defaults to None.
            proxy (str, optional): Proxy server. Defaults to None.
        """

        # current working directory/driver
        self.browser = 'chrome'
        self.driver_baseloc = os.path.join(os.getcwd(), 'driver')
        self.comment_disabled = False

        # Firefox
        if browser.lower() == 'firefox':
            self.browser = 'firefox'
            # Firefox Options
            options = FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            options.set_preference("dom.webnotifications.enabled", False)
            options.log.level = 'fatal'

            # current working directory/driver/firefox
            # self.driver = webdriver.Firefox(
            #     executable_path=GeckoDriverManager(path=os.path.join(self.driver_baseloc, 'firefox')).install(),
            #     options=options)
            self.driver = None
            try:
                self.driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
            except Exception as webdriver_ex:
                logger.error(f'[Driver Download Manager Error]: {str(webdriver_ex)}')
                sys.exit(1)

        # Chrome
        else:
            # Chrome Options
            options = ChromeOptions()
            if headless:
                # options.add_argument("--headless")
                # options.add_argument("--window-size=1920,1080")
                # options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
                options.add_argument('--no-sandbox')
                options.add_argument("--disable-extensions")
                options.add_argument("start-maximized")
                # options.add_experimental_option('useAutomationExtension', False)
            if profile:
                # Get the full path for the profile directory
                profile_dir = os.path.join(os.path.abspath(""), "profiles")
                profile_dir = os.path.abspath(profile_dir)  # Convert to absolute path

                # Create the directory if it doesn't exist
                if not os.path.exists(os.path.join(profile_dir, username)):
                    os.makedirs(os.path.join(profile_dir, username))

                options.add_argument(f'user-data-dir=r"{profile_dir}"')
                options.add_argument(f'--profile-directory={username}')

            if proxy:
                options.add_argument(f'--proxy-server={proxy}')


            options.add_argument("--disable-notifications")
            options.add_argument("--start-maximized")
            # options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument("--log-level=3")
            
            if platform == 'linux' or platform == 'linux2':
                options.add_argument('--disable-dev-shm-usage')

            # current working directory/driver/chrome
            self.driver = None
            try:
                # self.driver = webdriver.Chrome(
                #     executable_path=ChromeDriverManager(path=os.path.join(self.driver_baseloc, 'chrome')).install(),
                #     options=options)
                # self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
                # self.driver = webdriver.Chrome(options=options)
                print("Web driver options:")
                pprint(options.__dict__)
                if headless:
                    self.driver = uc.Chrome(headless=True, options=options)
                else:
                    self.driver = uc.Chrome(options=options)

            except Exception as webdriver_ex:
                logger.error(f'[Driver Download Manager Error]: {str(webdriver_ex)}')
                sys.exit(1)
                
        self.wait = WebDriverWait(self.driver, timeout)
        self.ac = ActionChains(self.driver)
        self.solver = RecaptchaSolver(driver=self.driver)
        self.emunium = EmuniumSelenium(self.driver)

        self.baseurl = INSTA_URL
        self.targeturl = self.baseurl
        self.username = username
        self.password = password
        self.tag = None
        self.account = None

    def target(self, accountname: str, tag: bool=False) -> None:
        """ Loads the target - account or hastag """
        if accountname.startswith('#'):
            self.tag = accountname[1:]
            self.targeturl = f"{self.baseurl}/explore/tags/{accountname[1:]}"
        else:
            self.account = accountname
            self.targeturl = f"{self.baseurl}/{accountname}"

    def validate_target(self) -> bool:
        """ Validates the target account or hashtag """
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, f'//*[text()="{self.account or self.tag}"]')))
            return True
        except:
            return False

    def validate_login(self) -> bool:
        """ Validates login """
        wait = WebDriverWait(self.driver, 5)
        for atmpt_cnt, xpath in enumerate(LoginLocators.validation, start=1):
            try:
                wait.until(EC.presence_of_element_located(get_By_strategy(xpath)))
                return True
            except:
                logger.error(f'Could not find xpath: {xpath}')

        return False

    def is_page_loaded(self) -> bool:
        """ Checks if page is loaded successfully """
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            return True
        except:
            return False

    @retry
    def open_target(self) -> bool:
        """ Opens the target account or hashtag """
        try:
            self.driver.get(self.targeturl)
            time.sleep(random_wait(1))
            # if unable to load the page
            if not self.is_page_loaded():
                logger.info("[open_target] Unable to load the page. Retrying...")
                time.sleep(1)
                return False

            # if not a valid account or tag
            elif not self.validate_target():
                logger.error('Failed to validate target')
                return False
        except:
            return False
        return True
    
    @retry
    def launch_insta(self) -> bool:
        """ Opens instagram """
        try:
            self.driver.get(self.baseurl)
        except Exception as ex:
            logger.error(f'{ex.__class__.__name__} {str(ex)}')
            return False
        return True
    
    def login(self, validate=True) -> bool:
        """ Initiates login with username and password """
        try:
            self.driver.get(self.baseurl)
            # el_username = self.wait.until(EC.presence_of_element_located(get_By_strategy(LoginLocators.username))).send_keys(self.username)
            el_username = self.wait.until(EC.presence_of_element_located(get_By_strategy(LoginLocators.username)))

            self.emunium.find_and_move(el_username, click=True)
            self.emunium.silent_type(self.username)
            self.wait.until(EC.presence_of_element_located(get_By_strategy(LoginLocators.password))).send_keys(self.password)
            self.wait.until(EC.presence_of_element_located(get_By_strategy(LoginLocators.submit))).click()

            if self.is_2factor_present():
                logger.info('2 factor authentication active. Enter your authentication code to continue')
                time.sleep(10)

            if validate:
                if not self.validate_login():
                    return False
        except Exception as ex:
            logger.error(f'[{ex.__class__.__name__} - {str(ex)}] Failed to login')
            return False
        return True


    def check_inbox(self, stats: 'Stats') -> bool | None:
        """
        Checks for new messages in the inbox
        """
        # chats_list = wait.until(EC.presence_of_element_located((By.XPATH, '//div/div/div[2]/div/div/div[1]/div[1]/div[2]/section/div/div/div/div[1]/div/div[1]/div/div[3]/div/div/div/div/div[2]/div')))
        #add check for new messages

        self.driver.get(INSTA_URL + '/direct/inbox/')
        self.dont_turn_on_notifications()
        wait = WebDriverWait(self.driver, timeout=20)
        try:
            logger.info('Open chat messages')

            #all unread messages
            #//span[contains(@class,'x6s0dn4 xzolkzo x12go9s9 x1rnf11y xprq8jg x9f619 x3nfvp2 xl56j7k x1tu34mt xdk7pt x1xc55vz x1emribx')]/ancestor::div[@role= 'button']

            # Define the XPath selector
            xpath_selector_unread_chat = "//span[contains(@class,'x6s0dn4 xzolkzo x12go9s9 x1rnf11y xprq8jg x9f619 x3nfvp2 xl56j7k x1tu34mt xdk7pt x1xc55vz x1emribx')]/ancestor::div[@role= 'button']"
            # xpath_selector_unread_chat = "//div[contains(@class,'x9f619 x1n2onr6 x1ja2u2z x78zum5 x1iyjqo2 xs83m0k xeuugli x1qughib x6s0dn4 x1a02dak x1q0g3np xdl72j9')]/ancestor::div[@role= 'button']"
            xpath_selector_chat_text = "//div[contains(@class,'x78zum5 xh8yej3')]/div/span/div"
            xpath_selector_username = "//div[@class='x1vjfegm']/div/div/div/a"

            # Find all unread messages elements
            elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath_selector_unread_chat)))

            # Check if elements array is empty
            if not elements:
                logger.info('No new messages found. Add logic to check where to followup.')
                time.sleep(get_delay(10))
                return True
            
            # Log the number of unread messages found
            logger.info("Found %s unread messages", len(elements))
            
                # Click on each element with a delay

            for element in elements:
                click_element_with_retry(element)

                logger.info(f'click: {element}')

                texts = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath_selector_chat_text)))
                # Extract the text of each chat message
                message_history = '\n'.join([text.text for text in texts])

                # Get the last message from the chat
                last_message = texts[-1].text if texts else None

                # Print last message
                logger.info("Last message in the chat: %s", last_message)

                # Print entire message history
                logger.info("Message history: %s", message_history)

                # Evaluate the XPath expression to get the first <a> element
                href_element = wait.until(EC.presence_of_element_located((By.XPATH, xpath_selector_username)))

                # Check if href_element is not empty
                if href_element:
                    # Get the href attribute value of the <a> element
                    href_value = href_element.get_attribute("href")
                    print("href_value:", href_value)

                    # Define a regular expression pattern to extract the username
                    pattern = r"https://www\.instagram\.com/([^/]+)/"
                    # Search for the pattern in the href_value
                    match = re.search(pattern, href_value)

                    # Check if a match is found
                    if match:
                        # Extract the username from the matched group
                        username = match.group(1)
                        print("Username:", username)
                    else:
                        print("Username not found in the href value.")

                else:
                    print("No <a> element found with the given XPath expression.")

                # Get AI generated message
                message = get_sales_message(username, last_message, message_history, stats)

                self.send_inbox_message(message)

                account = DbHelpers().get_or_create_account(username)
                if account:
                    #Save stats, 200 - message
                    DbHelpers().save_story_stats(account.id, 200, False, message)

                time.sleep(random_wait(5, 2))  # 5 seconds delay between clicks
                # break
            return True 
        except TimeoutException:
            logger.info("Timeout: No unread messages")
            return False
        except Exception as ex:
            print(ex)
            return False
        return None

    def send_inbox_message(self, message:str) -> bool | None:
        """
        Sends a message to the inbox
        """
        logger.info("Prepare to send message")
        cmt = self.driver.switch_to.active_element

        timeout = random_wait(5)
        try:
            human_like_typing(cmt, message)
            cmt.send_keys(Keys.ENTER)
            self.wait_until_comment_cleared(cmt, timeout)
            return True
        except ElementClickInterceptedException:
            logger.info("ElementClickInterceptedException")
            self.driver.execute_script('arguments[0].click();', cmt)
            self.wait_until_comment_cleared(cmt, timeout)
            return True
        except Exception as ex:
            print(ex)
            return False

    @retry
    def like(self) -> bool | None:
        """ Likes a post if not liked already """
        like_button:WebElement = None
        wait = WebDriverWait(self.driver, timeout=2)

        def is_already_liked():
            try:
                self.driver.find_element(*get_By_strategy(PostLocators.unlike))
                return True
            except:
                return False

        try:
            logger.info('Finding like button')
            like_button = wait.until(EC.presence_of_element_located(get_By_strategy(PostLocators.like)))
            like_button.click()
            return True
            # like_button_span = like_button.find_element(By.XPATH, 'div/div/span')
            # button_status = like_button_span.find_element(By.TAG_NAME, 'svg').get_attribute('aria-label')
            # # like only if not already liked
            # if button_status == 'Like':
            #     like_button.click()
            #     return True
        except ElementClickInterceptedException:
            logger.info('Failed to click - deploying Javascript')
            self.driver.execute_script('arguments[0].click();', like_button)
            return True
        
        except NoSuchElementException as nosuchelex:
            if is_already_liked():
                logger.info('Post is already liked')
                return None    
                    
            logger.warning('Like button seems to be disabled')
            logger.debug(str(nosuchelex))            
            return None
        
        except TimeoutException as timeoutex:
            if is_already_liked():
                logger.info('Post is already liked')
                return None
            logger.warning('Like button seems to be disabled')
            logger.debug(str(timeoutex))
            return False

        except Exception as ex:
            logger.error(f'{ex.__class__.__name__} - {str(ex)}')
            return False
        return None
    
    def wait_until_comment_cleared(self, element, timeout) -> None:
        """ Waits until the comment textarea is cleared, or until timeout """
        start = time.time()
        end = 0
        # wait until posted or until timeout
        while element.text != '' and (end - start) < timeout:
            end = time.time()
    
    def is_comment_disabled(self) -> bool:
        """ Checks if comment is disabled or not """
        try:
            # self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[normalize-space(text())="Comments on this post have been limited."]')))
            wait = WebDriverWait(self.driver, timeout=1)
            wait.until(EC.presence_of_element_located(get_By_strategy(PostLocators.comment_disabled)))
            self.comment_disabled = True
            return True
        except:
            return False

    @retry
    def comment(self, text, timeout, fs_comment = 'Perfect!') -> bool:
        """
        Comments on a post

        Args:
        timeout     wait until comment is posted
        fs_comment  failsafe comment in case bmp_emoji_safe_text returns an empty string
        """

        cmt_text = text
        cmt: WebElement = None
        wait = WebDriverWait(self.driver, 5)
        # remove non-bmp characters (for chrome)
        if self.browser == 'chrome':
            cmt_text = bmp_emoji_safe_text(text) or fs_comment

        try:
            cmt = wait.until(EC.presence_of_element_located(get_By_strategy(PostLocators.comment)))
            cmt.click()
            cmt.send_keys(cmt_text)
            wait.until(EC.presence_of_element_located(get_By_strategy(PostLocators.comment_post))).click()
            self.wait_until_comment_cleared(cmt, timeout)

        except ElementClickInterceptedException:
            self.driver.execute_script('arguments[0].click();', cmt)
            self.wait_until_comment_cleared(cmt, timeout)

        except Exception as ex:
            return False

        return True
    
    def get_number_of_posts(self) -> int:
        """ Returns number of post for an account or tag """
        try:
            num_of_posts = self.wait.until(EC.presence_of_element_located(get_By_strategy(PostLocators.num_of_posts))).text
            num_of_posts = num_of_posts.replace(',','')
            return int(num_of_posts)
        except:
            return None

    def click_first_post(self) -> bool:
        """ Clicks on the first post found for an account """
        try:
            self.wait.until(EC.presence_of_element_located(get_By_strategy(PostLocators.first_post))).click()
            return True
        except:
            return False

    def click_first_post_most_recent(self) -> bool:
        """ Clicks on the first post under most recent """
        try:
            # most recent div
            most_recent_div_el = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, '//h2[contains(text(),"Most recent")]//following-sibling::div')))
            # first post
            most_recent_div_el.find_element(By.CSS_SELECTOR, '._aagw').click()
            return True
        except Exception as ex:
            logger.error(f'[most_recent] Error: {ex.__class__.__name__}')
            return False

    def dont_save_login_info(self) -> bool:
        """ Clicks 'Not Now' button when prompted with 'Save Your Login Info?' """
        wait = WebDriverWait(self.driver, timeout=2)
        for xpath in LoginLocators.save_login.notnow:
            try:
                logger.info(f'Finding Not Now button with xpath: {xpath}')
                wait.until(EC.presence_of_element_located(get_By_strategy(xpath))).click()
                return True
            except:
                logger.error(f'Could not find Not Now button with xpath: {xpath}')
        return False
    
    def dont_turn_on_notifications(self) -> bool:
        """ Clicks 'Not Now' button when prompted with 'Turn On Notifications?' """
        wait = WebDriverWait(self.driver, timeout=2)
        # time.sleep(120)
        #Turn on Notifications
        for xpath in LoginLocators.notifications:
            try:
                logger.info(f'Finding Not Now button with xpath: {xpath}')
                wait.until(EC.presence_of_element_located(get_By_strategy(xpath))).click()
                return True
            except:
                logger.error(f'Could not find Not Now button with xpath: {xpath}')
        return False
    
    def save_login_info(self) -> bool:
        """ Saves login information """
        wait = WebDriverWait(self.driver, 2)
        for xpath in LoginLocators.save_login.save:
            try:
                logger.info(f'Finding Save Login with xpath: {xpath}')
                wait.until(EC.presence_of_element_located(get_By_strategy(xpath))).click()
                return True
            except:
                logger.error(f'Save Login info could not be found with xpath: {xpath}')
        return False

    def next_post(self) -> bool: 
        """ Moves to the next post """
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.RIGHT)
            return True
        except:
            return False

    def is_private(self) -> bool:
        """ Checks if an account is private """
        for xpath in AccountLocators.is_private:
            try:
                self.driver.find_element(*get_By_strategy(xpath))
                return True        
            except:
                return False        
                #logger.info(f'[is_private]: text=>({text}) not found')
        return False
    
    def is_2factor_present(self) -> bool:
        """ Checks if 2 factor verification screen is present """
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.presence_of_element_located(get_By_strategy(LoginLocators.twofactor)))
            return True
        except Exception as ex:
            logger.info('Could not locate 2 factor authentication screen')
        return False

    def quit(self) -> None:
        """ Quit driver """
        try:
            self.driver.quit()
        except Exception as ex:
            logger.error(f'Failed to close browser: {str(ex)}')
    
    def extract_username(self, text: str) -> str:
        """ Extracts username from text """
        if not text:
            return None

        username = text.split('https://www.instagram.com')[1]
        username = username.split('/')[1]
        return username

    def get_followers(self, amount: int = None) -> List:
        """ Gets followers from the target's page """
        if amount:
            logger.info(f'Restricting followers search to: {amount}')
            
        logger.info('Opening followers list')
        self.wait.until(EC.presence_of_element_located(get_By_strategy(FollowersLocators.link))).click()
        followers_div = self.wait.until(EC.presence_of_element_located(get_By_strategy(FollowersLocators.container)))

        # holds extracted usernames
        usernames = []

        div_read_start = 0
        div_read_end = 0

        num_previous_div = 0
        num_updated_div = 1

        time.sleep(3)

        running = True

        while(num_updated_div > num_previous_div and running):    

            logger.info('Getting updated list of username divs')
            username_links = None

            max_tries = 5
            tries = 0
            did_not_find_more_divs = True

            while tries < max_tries and did_not_find_more_divs:
                try:
                    # user_divs = followers_div.find_elements(By.TAG_NAME, 'div')
                    username_links = followers_div.find_elements(By.TAG_NAME, 'a')
                    num_previous_div = num_updated_div
                    num_updated_div = len(username_links)
                    if num_updated_div > num_previous_div:
                        did_not_find_more_divs = False
                    else:
                        logger.info('Scrolling')
                        scroll_into_view(self.driver, username_links[-1])
                        time.sleep(random_wait(5))
                        tries += 1

                except StaleElementReferenceException:
                    logger.error(f'StaleElementReferenceException exception occured while capturing username links')
                    logger.info("Capturing div containing followers' list")
                    followers_div = self.wait.until(EC.presence_of_element_located(get_By_strategy(FollowersLocators.container)))
                    time.sleep(random_wait(3))
    
            
            div_read_start = div_read_end
            div_read_end = len(username_links)
            
            logger.info(f'Processing userdiv range: {div_read_start} - {div_read_end}')
            for i in range(div_read_start, div_read_end):
                # get all text from the div
                # alltext = user_divs[i].text
                username_link = username_links[i].get_attribute('href')
                username = self.extract_username(username_link)

                # add found username to the list
                if username and username not in usernames:
                    usernames.append(username)

                # check if we have reached the desired amount
                if amount is not None and len(usernames) >= amount:
                    running = False
                    break
                    
            logger.info(f'Total username count: {len(usernames)}')
            logger.info('Scrolling')
            scroll_into_view(self.driver, username_links[-1])
            time.sleep(random_wait(7,5))
        
        return usernames
    
    def get_post_tags(self) -> List:
        """ Gets tags present in current post """
        tags = []
        try:
            tags_links = self.driver.find_elements(*get_By_strategy(PostLocators.properties.tags))
            tags = [taglink.text for taglink in tags_links]
        except Exception as ex:
            logger.error(f'{ex.__class__.__name__} {str(ex)}')
        return tags
    
    def get_tag_match_count(self, posttags: List, matchtags: List, min_match: int = 3) -> bool:
        """
        Checks if a minimum number of tags in matchtags match in
        tags from post
        """
        if not all([posttags, matchtags]):
            return False
        min_match = min(len(matchtags), min_match)
        return sum([tag in posttags for tag in matchtags]) >= min_match
    
    def get_post_description(self, author_username) -> str:
        """
        In our case we need to take first comment and compare username with author
        """
        wait = WebDriverWait(self.driver, 2)
        try:
            comment_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='_a9zr']")))
        except Exception as ex:
            logger.error(f'{ex.__class__.__name__} {str(ex)}')
            return ""
        
        if not comment_elements:
            return ""
        
        user, comment = self.get_user_and_comment_from_element(comment_elements[0])

        logger.info(f'user {user}, comment: {comment}')
        if user == author_username:
            return comment
        else:
            return ""

    def get_comment_usernames_from_post(self) -> List[str]:
        """ Returns usernames for comments on a post """
        wait = WebDriverWait(self.driver, 2)
        usernames = []
        try:
            comment_elements = wait.until(EC.presence_of_all_elements_located(get_By_strategy(PostLocators.properties.comment.comment_list)))
            for comment_el in comment_elements:
                uname = comment_el.find_element(*get_By_strategy(PostLocators.properties.comment.username)).text
                usernames.append(uname)
        except Exception as ex:
            logger.error(f'{ex.__class__.__name__} {str(ex)}')
        return list(set(usernames))

    def get_user_and_comment_from_element(self, comment_el) -> Tuple:
        """ Returns username and their comment from a comment element """
        if not comment_el:
            return ('','')
    
        username = ''
        comment = ''
        try:
            username = comment_el.find_element(*get_By_strategy(PostLocators.properties.comment.username)).text
            comment = comment_el.find_element(*get_By_strategy(PostLocators.properties.comment.comment)).text
        except Exception as ex:
            logger.error(f'{ex.__class__.__name__} {str(ex)}')
        return (username, comment)

    def is_commented(self) -> bool:
        """ Checks if a post already has a comment from the user """
        usernames = self.get_comment_usernames_from_post()        
        if not usernames:
            return False
        if self.username not in usernames:
            return False
        return True
    
    def like_comments(self, max_comments: int = 5) -> List[Tuple]:
        """ Likes post comments """
        def comment_not_liked(com_el):
            """ Check if like button is not already clicked """
            try:
                # like button svg
                 return com_el.find_element(*get_By_strategy(PostLocators.properties.comment.is_liked))\
                    .get_attribute('aria-label').lower() == 'like'
            except Exception as ex:
                logger.error(str(ex))
                return False
            
        wait = WebDriverWait(self.driver, 5)
        try:
            comment_elements = wait.until(EC.presence_of_all_elements_located(get_By_strategy(PostLocators.properties.comment.comment_list)))
        except Exception as ex:
            logger.error(f'{ex.__class__.__name__} {str(ex)}')
            return []
        
        if not comment_elements:
            return []
        
        successful_comments = []
        try:
            total_comments_liked = 0
            for com_el in comment_elements:
                if comment_not_liked(com_el):
                    # like button
                    com_el.find_element(*get_By_strategy(PostLocators.properties.comment.like)).click()
                    successful_comments.append(self.get_user_and_comment_from_element(com_el))    
                    total_comments_liked += 1
                    time.sleep(0.5)
                else:
                    user,comment = self.get_user_and_comment_from_element(com_el)
                    logger.info(f'Already Liked: [({user}) - {comment}]')
                if total_comments_liked == max_comments: 
                    break

        except Exception as ex:
            logger.error(f'{ex.__class__.__name__} {str(ex)}')
        return successful_comments

    def get_post_date(self) -> Tuple[str,float]:
        """ Returns post date (%Y-%m-%d %H:%M:%S, timestamp) """
        try:
            dt = self.driver.find_element(*get_By_strategy(PostLocators.properties.date)).get_attribute('datetime')
            if not dt:
                logger.error('Failed to find date for the post')
                return ('','')
            # %Y-%m-%d %H:%M:%S
            fmt_dt = re.sub(r'(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2}).+', r'\1 \2', dt)
            ts = datetime.strptime(fmt_dt, '%Y-%m-%d %H:%M:%S').timestamp()
            return (fmt_dt, ts)
        except Exception as ex:
            logger.error(f'{ex.__class__.__name__} {str(ex)}')
        return ('','')

    def post_within_last(self, ts: float, multiplier: int, tparam: str) -> bool:
        """ Checks if the post is within last n days """
        if not ts:
            return False
        current_ts = datetime.utcnow().timestamp()
 
        if tparam == 'y': return current_ts - ts <= multiplier * Seconds.Year.value
        if tparam == 'M': return current_ts - ts <= multiplier * Seconds.Month.value
        if tparam == 'd': return current_ts - ts <= multiplier * Seconds.Day.value
        if tparam == 'h': return current_ts - ts <= multiplier * Seconds.Hour.value
        if tparam == 'm': return current_ts - ts <= multiplier * Seconds.Min.value
        if tparam == 's': return current_ts - ts <= multiplier * Seconds.Sec.value

        return False

    def is_story_present(self):
        # return True
        """
        Checks if story is present
        """
        wait = WebDriverWait(self.driver, 5)
        try:
            # is_disabled = wait.until(EC.presence_of_element_located(get_By_strategy(storylocators.is_present)))
            # .get_attribute('aria-disabled')
            # return is_disabled == 'false'
            # canvas only appears when story is present
            wait.until(EC.presence_of_element_located(
                get_By_strategy(f"//span[@role='link']/img[contains(@alt, '{self.account}')]/../../canvas")
            ))
            # is_disabled = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "_aarf")]'))).get_attribute('aria-disabled')
            return True
        except Exception as ex:
            logger.info(f'Stories not found for the account')
        return False

    def open_story(self) -> bool:
        """
        Opens story for a user
        """
        wait = WebDriverWait(self.driver, 10)
        try:
            # wait.until(EC.presence_of_element_located((By.XPATH, "//div/div/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/header/div/div"))).click()
            wait.until(EC.presence_of_element_located((By.XPATH, f'//img[contains(@alt, "{self.account}")]'))).click()
            logger.info('[open_story]: Open to view')

            try:
                story_accept = self.driver.find_element(By.XPATH, "//div/div/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[3]/div")
                if story_accept:
                    story_accept.click()
                    logger.info('[accpet_story]: Accept to view')
                    return True
            except Exception as ex:
                # logger.info(f'[accpet_story] Error: {ex.__class__.__name__}')
                return True
            
        except Exception as ex:
            logger.error(f'[open_story] Error: {ex.__class__.__name__}')
        return False

    def pause_story(self) -> bool:
        """
        Pauses a story
        """
        wait = WebDriverWait(self.driver, random_wait(3))
        try:
            # story_pause = self.driver.find_element(By.XPATH, "//div/div/div[3]/div/div/div[3]/div/section/div[1]/div/div/div[1]/div[1]/div/div[2]/div[2]/div[2]/div").find_element(By.CSS_SELECTOR, 'svg[aria-label="Pause"]')
            wait.until(EC.presence_of_element_located(get_By_strategy(LOCATORS['locators']['story']['pause']['pause_button']))).click()
            # logger.info(f'Pause tag {LOCATORS["locators"]["story"]["pause"]["pause_button"]}')

            # if story_pause:
            #     story_pause.click()
            #     logger.info(f'[pause_story] Pause')
            # else:
            #     logger.error(f'[pause_story] Error')
            # wait.until(EC.presence_of_element_located((By.XPATH, "//div/div/div[3]/div/div/div[3]/div/section/div[1]/div/div/div[1]/div[1]/div[2]")).find_element(By.CSS_SELECTOR, 'svg[aria-label="Pause"]')).click()
            return True
        except Exception as ex:
            logger.error(f'[pause_story] Error: {ex.__class__.__name__}')
            # logger.error(f'[pause_story] Error: {ex}')
        return False
    
    def get_story_image(self) -> str:
        """
        Screenshot a story
        """
        try:
            story = self.driver.find_element(By.XPATH, "//div/div/div[3]/div/div/div[3]/div/section/div[1]/div/div/div[1]/div[2]/div[1]/div")
            # print(story.screenshot_as_base64)
            return base64.b64decode(story.screenshot_as_base64)
        except Exception as ex:
            logger.error(f'[image_story] Error: {ex.__class__.__name__}')
        return False
    
    # def like_story(self) -> bool | None:
    #     """
    #     Like a story
    #     """
    #     logger.info('[like_story]: Start')
    #     wait = WebDriverWait(self.driver, 2)
    #     try:
    #         wait.until(EC.presence_of_element_located((By.XPATH, "//div/div/div[3]/div/div/div[3]/div/section/div[1]/div/div/div[1]/div[2]/div[2]/div[1]/div[2]/span/div"))).click()
    #         logger.info('[like_story]: Liked')
            
    #         return True
    #     except Exception as ex:
    #         try:
    #             if self.driver.find_element(By.XPATH, "//div/div/div[3]/div/div/div[3]/div/section/div[1]/div/div/div[1]/div[2]/div[2]/div[1]/div[2]/span/div").find_element(By.CSS_SELECTOR, 'svg[aria-label="Unlike"]'):
    #                 logger.info('[like_story]: Already liked')
    #                 return None
    #         except Exception as ex2:
    #             logger.error(f'[image_story] Error: {ex2.__class__.__name__}')
    #             return False
    #         logger.error(f'[like_story] Error: {ex.__class__.__name__}')
    #     return False
    
    def like_story(self) -> bool | None:
        """ Pauses a story """
        wait = WebDriverWait(self.driver, 2)
        try:
            wait.until(EC.presence_of_element_located(get_By_strategy(StoryLocators.like.like_button))).click()
            return True
        except Exception as ex:
            try:
                if self.driver.find_element(*get_By_strategy(StoryLocators.like.unlike_button)):
                    logger.info('[like_story]: Already liked')
                    return True
            except Exception as ex2:
                logger.error(f'[image_story] Error: {ex2.__class__.__name__}')
                return False
            logger.error(f'[like_story] Error: {ex.__class__.__name__}')
        return False


    def next_story(self):
        """ Moves to next story """
        wait = WebDriverWait(self.driver, 5)
        try:
            wait.until(EC.presence_of_element_located(get_By_strategy(StoryLocators.next))).click()
            # wait.until(EC.presence_of_element_located((By.XPATH, "//div/div/div[3]/div/div/div[3]/div/section/div[1]/div/div/div[2]/div[2]"))).click()
            logger.info('[next_story]: Next')
            return True
        except Exception as ex:
            logger.error(f'[next_story] Error: {ex.__class__.__name__}')
        return False
    
    def get_total_stories(self) -> int:
        """ Get total stories """
        wait = WebDriverWait(self.driver, 10)
        try:
            # Find all elements matching the given XPath
            # story_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div/div/div[3]/div/div/div[3]/div/section/div[1]/div/div/div[1]/div[1]/div[1]/div")))
            # logger.info(f'[total_story]: {len(story_elements)} stories found')
            # Return the count of found elements
            # return len(story_elements)
            return len(wait.until(EC.presence_of_element_located(get_By_strategy(LOCATORS["locators"]["story"]["count"]["container"]))).find_elements(*get_By_strategy(LOCATORS["locators"]["story"]["count"]["story"])))
        except Exception as ex:
            logger.error(f'[get_total_stories] Error: {ex}')
        return 0
    
    @retry
    def comment_on_story(self, text) -> bool:
        """ Comments on a story """
        wait = WebDriverWait(self.driver, 5)
        try:

            cmt = wait.until(EC.presence_of_element_located(get_By_strategy(LOCATORS["locators"]["story"]["comment"]["comment_box"])))
            # logger.info(f'Comment tag {LOCATORS["locators"]["story"]["comment"]["comment_box"]}')

            # cmt = wait.until(EC.presence_of_element_located((By.XPATH, "//div/div/div[3]/div/div/div[3]/div/section/div[1]/div/div/div[1]/div[2]/div[2]/div[1]/div[1]/div[1]/textarea"))
            cmt.click()
            time.sleep(1)
            # cmt.send_keys(text)
            human_like_typing(cmt, text)
            cmt.send_keys(Keys.ENTER)
            time.sleep(1)
            return True
        except Exception as ex:
            logger.error(f'[comment_on_story] Could not comment on this story. Error: {ex.__class__.__name__}')
        return False
    
    def is_reels_present(self):
        """ Checks if reels is present for an account """
        wait = WebDriverWait(self.driver, 5)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, f'//a[contains(@href,"{self.account}/reels")]')))
            return True
        except Exception as ex:
            logger.error(f'[is_reels_present] Could not find reels')
        return False

    def open_reels(self):
        """ Opens reels page """
        wait = WebDriverWait(self.driver, 5)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, f'//a[contains(@href,"{self.account}/reels")]'))).click()
            return True
        except:
            logger.error(f'[open_reels] Failed to open reels page')
        return False
    
    def click_first_reel(self):
        """ Clicks on the first reel found on the account """
        try:
            reels = self.wait.until(EC.presence_of_all_elements_located(get_By_strategy(ReelsLocators.first_reel)))
            reels[0].click()
            return True
        except:
            logger.error(f'[click_first_reels] Failed to open first reel')
        return False

    def next_reel(self):
        """ Moves to the next reel """
        try:
            self.next_post()
            return True
        except:
            logger.error('[next_reel] Failed to move to the next reel')
        return False
    
    def like_reel(self):
        """ Likes a reel """
        try:
            self.like()
            return True
        except:
            logger.error(f'[like_reel] Failed to like reel')
        return False

    def comment_on_reel(self, text: str, timeout: int):
        """ Comments on a reel """
        try:
            self.comment(text=text, timeout=timeout)
            return True
        except Exception as ex:
            logger.error('[comment_on_reel] Failed to comment on the reel')
        return False

    def like_reel_comments(self, max_comments: int = 5):
        """ Likes comments on a reel """
        try:
            self.like_comments(max_comments=max_comments)
            return True
        except Exception as ex:
            logger.error('[like_reel_comments] Failed to comment on the reel')
        return False
    
    def check_and_solve_captcha(self):

        max_retries = 5
        try:
            WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@title="Google Recaptcha v2"]')))
            recaptcha_iframe = self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')

            print(recaptcha_iframe)
        except Exception as e:
            print("reCAPTCHA iframe not found.")
            print(e)
            
            return

        for retry in range(max_retries):
            try:    
                self.solver.click_recaptcha_v2(iframe=recaptcha_iframe)
                print("reCAPTCHA solved successfully.")
                self.driver.switch_to.default_content()
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button'][contains(.,'Next')]"))).click()   
                break
            except Exception as e:
                if retry == max_retries - 1:
                    print(f"Failed to solve reCAPTCHA after {max_retries} attempts.")
                else:
                    print(f"Attempt {retry + 1} failed. Retrying...")

