import os
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DB_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

C_TITLE = os.getenv("C_TITLE")
C_OFFER = os.getenv("C_OFFER")


C_COMMENT_PROMPT = """You are a professional marketer and working for {C_TITLE} You need to provide a comment for an Instagram story.
 Your reply will be based on story description from user
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
- do not write Acknowledge or Complement in output"""

C_PROMPT_EVAL_COMMENT = """
You are a professional quality assurance and working for {C_TITLE} 
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


INSTRUCTIONS_PROMPT_S2 = """
        You are on STAGE 2: 
        Ask needs to be around "time", "money", and "motivation or energy"
        We ask to sell our services, we dont ask for advice. 
        Ask needs to be less than 40 characters. 
        Conversation history:
        """
INSTRUCTIONS_PROMPT_S3 = """
        You are on STAGE 3: 
        Ask if you know somebody you can offer your services. This is not direct sell. 
        Example: I'm offering 1 to 1 sessions on spiritual growth. Do you know anymone who might be interested?
        Ask needs to be less than 60 characters. 
        OFFER: {C_OFFER}
        """
