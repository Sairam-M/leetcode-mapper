from openai import OpenAI
from dotenv import load_dotenv

import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

REASONING_PROMPT = """
Here is an input problem and its normalized form for which we are looking to find an equivalent Leetcode problem

/*Input Problem: */
/*{input_problem}*/

/*Input Normalized: */
/*{normalized_input}*/

Using FAISS we found that the below 5 leetcode problem are the closest matches to the input problem

/* Candidate Problems */
/* {candidates_text} */


First analyse the input problem and its normalized form against all the 5 candidate problem and 
Choose the best match for the input among the 5 FAISS listed Problems
IMPORTANT: You MUST choose from the 5 candidates listed above only. Do not suggest any other problem.

Analyze why this choice is a strong (or weak) match for the input problem.
Structure your response as:

Title: [Exact Title of the chosen problem from the 5 candidates]
Pattern: [e.g. two-pointer, sliding window, DP]
Core Constraint: [e.g. O(n) time, no extra space]
Why it matches: [1-2 sentences on shared algorithmic structure]
Key difference: [1 sentence on what's different, if anything]
Confidence: [Strong / Moderate / Weak match]
"""


def build_candidate_text(sub_df, desc_char_limit):

    candidates = []
    for i in range(len(sub_df)):
        candidates.append({
            "title": sub_df.iloc[i]['title'],
            "description": sub_df.iloc[i]['description_clean'][:desc_char_limit]
        })
    
    candidates_text = ""
    for i, c in enumerate(candidates):
        candidates_text += f"/* Problem {i+1} */\n/* Title: {c['title']} */\n/* Description: {c['description']} */\n\n"
    return candidates_text

def build_prompt(input_problem, normalized_input, sub_df, desc_char_limit):
    candidate_text = build_candidate_text(sub_df, desc_char_limit)
    prompt = REASONING_PROMPT.format(
        input_problem=input_problem,
        normalized_input=normalized_input,
        candidates_text=candidate_text
    )
    return prompt


def get_llm_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def parse_reasoning(response_text: str) -> dict:
    lines = response_text.strip().split('\n')
    result = {}
    
    field_map = {
        'title': 'title',
        'pattern': 'pattern',
        'core constraint': 'core_constraint',
        'why it matches': 'why_it_matches',
        'key difference': 'key_difference',
        'confidence': 'confidence'
    }
    
    for line in lines:
        line = line.strip().lstrip('*').rstrip('*').strip()
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        key = key.strip().lstrip('*').rstrip('*').strip().lower()
        value = value.strip().lstrip('*').rstrip('*').strip()
        if key in field_map:
            result[field_map[key]] = value
    
    return result

def enrich_reasoning_with_meta_data(reasoning_dict, sub_df):
    title = reasoning_dict.get('title', '')
    match_row = sub_df[sub_df['title'] == title]
    if not match_row.empty:
        reasoning_dict['leetcode_title'] = match_row.iloc[0]['title']
        reasoning_dict['leetcode_link'] = match_row.iloc[0]['url']
        reasoning_dict['difficulty'] = match_row.iloc[0]['difficulty']
        reasoning_dict['acceptance_rate'] = match_row.iloc[0]['acceptance_rate']
        reasoning_dict['topics'] = match_row.iloc[0]['related_topics']
    else:
        reasoning_dict['leetcode_title'] = ''
        reasoning_dict['leetcode_link'] = ''
        reasoning_dict['difficulty'] = ''
        reasoning_dict['acceptance_rate'] = 0.0
        reasoning_dict['topics'] = ''
    return reasoning_dict
    

def generate_reasoning(input_problem: str, 
                        normalized_input: str, 
                        df, 
                        candidate_indices,
                        desc_char_limit=300):
    # index.search returns shape (n_queries, k) — we always query one problem at a time, so [0] gives the single result row
    sub_df = df.iloc[[idx for idx in candidate_indices[0]]]
    prompt = build_prompt(input_problem, normalized_input, sub_df, desc_char_limit)
    response = get_llm_response(prompt)
    reasoning_dict = parse_reasoning(response)
    enriched_result = enrich_reasoning_with_meta_data(reasoning_dict, sub_df)
    return enriched_result