""" 
    helpers.py - helper methods

    insta-likecom-bot v.3.0.4
    Automates likes and comments on an instagram account or tag

    Author: Shine Jayakumar
    Github: https://github.com/shine-jayakumar
    Copyright (c) 2023 Shine Jayakumar
    LICENSE: MIT
"""


from typing import List, Tuple
import random
from modules.constants import APP_VERSION
from ollama import Client
#TODO: move url to config
client = Client(host='http://localhost:11434')
STORY = "As a professional spiritual life coach, you discuss work-life balance, mindfulness, living harmoniously, and maintaining a healthy diet."


def remove_blanks(lst: List) -> List:
    """
    Removes empty elements from a list
    """
    return [el for el in lst if el != '']


def remove_carriage_ret(lst) -> List:
    """
    Remove carriage return - \r from a list
    """
    return list(map(lambda el: el.replace('\r',''), lst))


def bmp_emoji_safe_text(text) -> str:
    """
    Returns bmp emoji safe text
    ChromeDriver only supports bmp emojis - unicode < FFFF
    """
    transformed = [ch for ch in text if ch <= '\uFFFF']
    return ''.join(transformed)


def scroll_into_view(driver, element) -> None:
    """
    Scrolls an element into view
    """
    driver.execute_script('arguments[0].scrollIntoView()', element)


def get_delay(delay: tuple, default: tuple = (1,10)) -> Tuple[int]:
    """ Returns a random delay value between (st,en) """
    if not delay:
        return random.randint(default[0], default[1])
    if len(delay) < 2:
        return delay[0]
    return random.randint(delay[0], delay[1])


def get_random_index(total_items: int, nreq: int, all_specifier=111) -> list:
    """
    Generates random index numbers based on value of argname
    """
    if not nreq:
        return []
    if nreq == all_specifier or nreq > total_items:
        nreq = total_items
    return random.sample(range(total_items), nreq)


def generate_random_comment(comments, generate_with_ai = False, description = ''):
    """
    Returns a random comment from a list of comments
    """
    if generate_with_ai:
        """
        Generates an AI-based comment based on the given description using Ollama Local LLM.
        """
        # Define the prompt for the AI model
        prompt = f"{STORY} Generate a creative instagram comment with no hashtags for the following description on post: {description}. Make comment short, less then 80 characters. Make comment end with engaging question."
        
        response = client.chat(model='mistral', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ])
        
        # Extract the generated comment from the response
        generated_comment = response['message']['content']
        print(generated_comment)        
        
        return generated_comment
    else: 
        return comments[random.randint(0, len(comments)-1)]

def generate_ai_comment(description = ''):
    """
    Generates an AI-based comment based on the given description using Ollama Local LLM.
    """
    # Define the prompt for the AI model
    prompt = f"Generate a creative instagram comment for the following description: {description}. Make comment short, less then 80 characters. Make comment end with engaging question. "
    
    response = client.chat(model='mistral', messages=[
    {
        'role': 'user',
        'content': description,
    },
    ])
    print(response['message']['content'])
    
    # Extract the generated comment from the response
    generated_comment = response['message']['content']
    
    return generated_comment

def display_intro():

    intro = f"""
     ___ _  _ ___ _____ _      _    ___ _  _____ ___ ___  __  __     ___  ___ _____ 
    |_ _| \| / __|_   _/_\ ___| |  |_ _| |/ | __/ __/ _ \|  \/  |___| _ )/ _ |_   _|
     | || .` \__ \ | |/ _ |___| |__ | || ' <| _| (_| (_) | |\/| |___| _ | (_) || |  
    |___|_|\_|___/ |_/_/ \_\  |____|___|_|\_|___\___\___/|_|  |_|   |___/\___/ |_|  
    
    insta-likecom-bot {APP_VERSION}
    Automates likes and comments on an instagram account or tag

    Author: Shine Jayakumar
    Github: https://github.com/shine-jayakumar
    Copyright (c) 2023 Shine Jayakumar
    LICENSE: MIT
    
    """
    print(intro)