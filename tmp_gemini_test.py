import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path('.env'))
print('LLM_PROVIDER=', os.getenv('LLM_PROVIDER'))
print('GOOGLE_API_KEY_set=', bool(os.getenv('GOOGLE_API_KEY')))
print('GOOGLE_API_KEY=', os.getenv('GOOGLE_API_KEY'))

from utils.llm import get_llm, invoke_with_retry
from langchain_core.messages import SystemMessage, HumanMessage

llm = get_llm()
print('Got LLM:', type(llm))
messages = [
    SystemMessage(content='You are a helpful assistant.'),
    HumanMessage(content='Say hello.')
]
response = invoke_with_retry(llm, messages)
print('Response:', response)
