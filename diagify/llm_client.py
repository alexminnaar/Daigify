import os
import logging
from openai import OpenAI

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)


def call_openai(description, system_prompt, model):
    client = get_openai_client()
    prompt = f"Generate Mingrammer diagrams code for the following description:\n\n{description}\n\nCode:"
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        max_tokens=1084,
        temperature=0.5,
    )
    return response.choices[0].message.content


def call_openai_user_prompt_only(correction_prompt, model="gpt-4"):
    client = get_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": correction_prompt}],
        max_tokens=1084,
        temperature=0.5
    )
    corrected_code = response.choices[0].message.content.strip()
    return corrected_code
