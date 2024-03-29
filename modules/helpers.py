""" 
    helpers.py - helper methods

    insta-likecom-bot v.3.0.6
    Automates likes and comments on an instagram account or tag

    Author: Shine Jayakumar
    Github: https://github.com/shine-jayakumar
    Copyright (c) 2023 Shine Jayakumar
    LICENSE: MIT
"""

import os
import base64
import io
import uuid

from selenium.webdriver.common.by import By
from typing import List, Tuple
import random
from modules.constants import APP_VERSION
from ollama import Client
from openai import OpenAI

from PIL import Image, ImageDraw, ImageFont

clientOpenAI = OpenAI()

#TODO: move url to config
client = Client(host='http://localhost:11434')
STORY = "professional spiritual life coach, you discuss work-life balance, mindfulness, living harmoniously, and maintaining a healthy diet."

PROMPT = f"""
You are a professional marketer and working for {STORY} You need to provide a comment for an Instagram story. Your reply will be based on story description from user
Use framework: Acknowledge, Complement. You acknowledge something interesting about the story and compliment the author about it. 
Example: Wow, you have kids. You must be a supermom. 
where acknowledge: Wow, you have kids
and complement: You must be a supermom
Use the same structure for comment: acknowledge on story topic, complement the story owner. Just give me two sentance with acknowledge and complement. 


Rules:
- Make comments short, less than 80 characters.
- no hashtags
- avoid explaining yourself
- pay attention to the text on the image

"""
#prompt_for_comment = f"Generate a creative Instagram story comment with no hashtags based on this image description: '{image_description}'. Keep the comment under 50 characters and end with an engaging question."

PROMPT_EVALUATE = f"""
You are a professional marketer. You need to evaluate an Instagram story from image description. 
Sometimes description does not make sence and you need to evaluate from 0 to 100 the image description and how likely your comment will bring value and would be interesting. 
The higher evaluation is about family, pets, children, emotional things. 

The story description starts after "==="


Topic you talk about: 
{STORY}

Rules:
- return just integer number from 0 to 100
- no description or explanation, just number
- if screen is black, rank 0

Story description
===
"""

PROMPT_EVAL_COMMENT = f"""
You are a professional quality assurance and working for {STORY} 
You need to evaluate an Instagram story comment based on image description. How relevant comment is. 
Image description is provided by user. 

The story comment start after "==="

Rules:
- return just integer number from 0 to 100
- no description or explanation, just number
- if image descripton has black screen mention, then rank 0
- ignore instagram interface description

Story comment
===
"""


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


def generate_random_comment(comments, generate_with_ai=False, description=''):
    """
    Returns a random comment from a list of comments
    """
    if generate_with_ai:
        """
        Generates an AI-based comment based on the given description using Ollama Local LLM.
        """
        # Define the prompt for the AI model
        # prompt = f"{STORY} Generate a creative instagram comment with no hashtags for the following description on post: {description}. Make comment short, less then 80 characters. Make comment end with engaging question."
        prompt_image = f"{PROMPT} {description}"

        print(prompt_image)

        response = client.chat(model='mistral', messages=[
        {
            'role': 'user',
            'content': prompt_image,
        },
        ])

        # Extract the generated comment from the response
        generated_comment = response['message']['content']
        # print(generated_comment)

        return generated_comment
    else:
        return comments[random.randint(0, len(comments)-1)]


def get_By_strategy(locator: str) -> tuple[By,str] | tuple[None, None]:
    """ Returns By strategy and locator (xpath, css selector) """
    if not locator:
        return (None, None)
    if locator.startswith('//'):
        return By.XPATH, locator
    return By.CSS_SELECTOR, locator


def create_dirs(dirlist: list[str]) -> None:
    """ Creates directories if doesn't exist """
    for dirname in dirlist:
        try:
            if not os.path.exists(dirname):
                os.mkdir(dirname)
        except Exception as ex:
            print(f'[{ex.__class__.__name__} - {str(ex)}] Error creating director: {dirname}')


def generate_ai_comment_for_story(image_bytes):
    """
    Returns ai generated comment based on image
    """

    prompt = "What is on the image? Don't mention Instagram interface"
    try:
        response = client.chat(model='llava', messages=[
            {
                'role': 'user',
                'content': prompt,
                'images': [image_bytes]
            },
        ])
        image_description = response['message']['content']
        print(f'image_description: {image_description}')
    except Exception as e:
        print(f"Failed to get image description from Ollama: {e}")
        image_description = None



    # prompt_for_comment = f"{PROMPT} {image_description}"
    # response_for_comment = client.chat(model='mistral', messages=[
    #     {
    #         'role': 'user',
    #         'content': prompt_for_comment,
    #     },
    # ])

    try:
        # Create request with openai lib for getting rank
        request = clientOpenAI.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": f"{image_description}"}
            ],
            temperature=0.7,
            max_tokens=60,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
    except clientOpenAI.APIConnectionError as e:
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.

    except clientOpenAI.RateLimitError as e:
        print("A 429 status code was received; we should back off a bit.")

    except clientOpenAI.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)

    else:
        # Assuming the response object has a 'choices' attribute that is a list of choice objects
        if request.choices:
            first_choice = request.choices[0]
            response_for_comment = first_choice.message.content
            print(f"Comment response: {response_for_comment}")

    # Get rank from OpenAI
    try:
        # Create request with openai lib for getting rank
        request = clientOpenAI.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"{PROMPT_EVAL_COMMENT} {response_for_comment}"},
                {"role": "user", "content": image_description}
            ],
            temperature=0.7,
            max_tokens=60,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
    except clientOpenAI.APIConnectionError as e:
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.

    except clientOpenAI.RateLimitError as e:
        print("A 429 status code was received; we should back off a bit.")

    except clientOpenAI.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)

    else:
        # Assuming the response object has a 'choices' attribute that is a list of choice objects
        if request.choices:
            first_choice = request.choices[0]
            response_for_rank = first_choice.message.content
            print(f"Rank response: {response_for_rank}")

    # Extract the generated comment from the response
    generated_comment = f"Rank: {response_for_rank}\n {response_for_comment}"
    print(f'Comment: {generated_comment}')

    # Overlay the comment on the image with a black overlay and padding
    image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("./arial.ttf", 11)  # Font file is in the same directory as this script

    # Split the comment into two lines if it's too long
    if len(generated_comment) > 50:  # Assuming an average of 25 characters can fit in one line
        split_index = generated_comment[:50].rfind(' ')
        generated_comment = generated_comment[:split_index] + '\n' + generated_comment[split_index+1:]

    _, _, text_width, text_height = draw.textbbox((0, 0), text=generated_comment, font=font)
    image_width, image_height = image.size
    x = (image_width - text_width) / 2
    y = image_height - text_height - 20  # 20 pixels from the bottom to accommodate two lines and padding

    # Calculate padding for the black overlay
    padding = 5
    overlay_width = text_width + padding * 2
    overlay_height = text_height + padding * 2
    overlay_x = x - padding
    overlay_y = y - padding

    # Draw black overlay with padding
    draw.rectangle([overlay_x, overlay_y, overlay_x + overlay_width, overlay_y + overlay_height], fill=(0, 0, 0))

    # Draw the text over the black overlay
    draw.text((x, y), generated_comment, font=font, fill=(255, 255, 255))

    # Create a folder for images if it does not exist
    folder_path = "generated_images"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Save the image with a unique name in the created folder
    file_path = os.path.join(folder_path, f"generated_comment_{uuid.uuid4()}.png")
    image.save(file_path)

    try:
        numeric_response_for_rank = int(response_for_rank)
        if numeric_response_for_rank > 50:
            return {'comment': response_for_comment, 'image_description': image_description, 'rank': response_for_rank}
        else:
            return None
    except ValueError:
        return None


def display_intro():

    intro = f"""
     ___ _  _ ___ _____ _      _    ___ _  _____ ___ ___  __  __     ___  ___ _____ 

    """
    print(intro)


def save_to_file(content, file_path):
    if type(content) is list:
        string_content = '\n'.join(str(s) for s in content)
        content = string_content
    with open(file_path, "w") as file:
        file.write(content)
