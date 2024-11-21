import os
import logging
from openai import OpenAI


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)


def generate_code_from_description(description, system_prompt):
    client = get_openai_client()
    prompt = f"Generate Mingrammer diagrams code for the following description:\n\n{description}\n\nCode:"
    logging.info("Sending request to OpenAI...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        max_tokens=1084,
        temperature=0.5,
    )
    return response.choices[0].message.content
