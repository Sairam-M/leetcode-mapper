from openai import OpenAI
from dotenv import load_dotenv

import numpy as np

import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

NORMALIZATION_PROMPT = """
Extract the core algorithmic problem from the below problem. 
Remove example-specific framing, output format differences. 
Return just the essential problem in neutral language.

/*{input_problem}*/
"""

def normalize_problem_statement(problem_statement: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", 
                   "content": NORMALIZATION_PROMPT.format(input_problem=problem_statement)}]
    )

    return response.choices[0].message.content.strip()

def embed_input_problem(normalized_input: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[normalized_input]
    )

    return np.array([response.data[0].embedding], dtype='float32')

def faiss_search(query_vector, index, top_k):
    distances, indices = index.search(query_vector, top_k)

    return distances, indices


def search_similar_problems(input_problem: str, index, top_k=5):
    normalized_problem = normalize_problem_statement(input_problem)
    query_vector = embed_input_problem(normalized_problem)
    distances, indices = faiss_search(query_vector, index, top_k)

    return distances, indices