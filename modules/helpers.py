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
from PIL import Image, ImageDraw, ImageFont

from selenium.webdriver.common.by import By
from typing import List, Tuple
import random
from modules.constants import APP_VERSION
from ollama import Client
from openai import OpenAI
import os, time
from modules.database import DbHelpers
from modules.variables import *

clientOpenAI = OpenAI()
client = Client(host=OLLAMA_URL)


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

def human_like_typing(input_element, message):
    """
    Simulate human-like typing by sending keys one by one with random delays.
    """
    input_element.click()
    for char in message:
        # Type one character
        input_element.send_keys(char)
        
        # Randomly wait between 0.1 and 0.3 seconds before typing the next character
        time.sleep(random.uniform(0.005, 0.01))


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
        prompt_image = f"{C_COMMENT_PROMPT} {description}"
        
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
                {"role": "system", "content": C_COMMENT_PROMPT},
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
                {"role": "system", "content": f"{C_PROMPT_EVAL_COMMENT} {response_for_comment}"},
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


def get_sales_message(username, last_message, message_history, stats: 'Stats'):
    """
    Returns ai generated sales message based sales stage
    """
    assistant_id = OPENAI_ASSISTANT_ID
    db_helpers = DbHelpers()

    # first need to get account from DB based on username
    account = db_helpers.get_or_create_account(username)

    instructions_prompt = ''
    # Get prompt based on Sales stage
    if account.stage == 0:
        # cold prospect
        # need to send a question query
        #add question!!!!
        instructions_prompt = INSTRUCTIONS_PROMPT_S2 + message_history
        account.stage = 2
        db_helpers.save_to_db(account)
        stats.message_stage_1 += 1
    elif account.stage == 2:
        instructions_prompt = INSTRUCTIONS_PROMPT_S3
        account.stage = 3
        db_helpers.save_to_db(account)
        stats.message_stage_2 += 1
    elif account.stage == 3:
        instructions_prompt = INSTRUCTIONS_PROMPT_S4
        account.stage = 4
        db_helpers.save_to_db(account)
        stats.message_stage_3 += 1
    else:
        # not not reply anymore
        instructions_prompt = ''
        return False

    stats.reply += 1

    # Open AI assistant connect, get thread_id
    thread_id = False
    
    if account.thread_id == "0" or account.thread_id is None:
        thread = clientOpenAI.beta.threads.create()
        thread_id = thread.id
        account.thread_id = thread_id
        db_helpers.save_to_db(account)
        print(f"New thread created with ID: {thread_id}")
    else:
        thread_id = account.thread_id
        print(f"Existing thread ID: {thread_id}")

    
    # Now create message we run from a user
    content_prompt = last_message
    message = clientOpenAI.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content_prompt
    )


    # Creating a run
    run = clientOpenAI.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=instructions_prompt
    )
  
    # Initialize an empty string to store the concatenated messages
    concatenated_message = ""
    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1) # Wait for 1 second
        run = clientOpenAI.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run.status == 'completed': 
            messages = clientOpenAI.beta.threads.messages.list(
                thread_id=thread_id
            )

            # Iterate through the messages in reverse order
            for message in messages.data:
                # Check if the message's role is 'assistant'
                if message.role == 'assistant':
                    # Extract the content of the message
                    content = message.content
                    if content:
                        # Extract the text content
                        text_content = content[0].text.value
                        # Concatenate the text content
                        concatenated_message += text_content + "\n"
                    # Break out of the loop after finding the last assistant message
                    break

    # add save stats message we sent
    stats.save()
    return concatenated_message


def get_By_strategy(locator: str) -> tuple[By,str] | tuple[None, None]:
    """ Returns By strategy and locator (xpath, css selector) """
    if not locator:
        return(None, None)
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
        

def display_intro():

    intro = f"""
     ___ _  _ ___ _____ _      _    ___ _  _____ ___ ___  __  __     ___  ___ _____ 
     INSTA BOT!!!
    
    """
    print(intro)


def save_to_file(content, file_path):
    if type(content) is list:
        string_content = '\n'.join(str(s) for s in content)
        content = string_content
    with open(file_path, "w") as file:
        file.write(content)


if __name__ == '__main__':
    pass
