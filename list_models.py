"""List all available models on Cerebras."""
from dotenv import load_dotenv
import os
load_dotenv()

from openai import OpenAI
client = OpenAI(base_url="https://api.cerebras.ai/v1", api_key=os.getenv("CEREBRAS_API_KEY"))

models = client.models.list()
for m in models.data:
    print(m.id)
