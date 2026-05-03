import gradio as gr
import requests

# API endpoint URL
URL = "https://leetcode-mapper.onrender.com/leetcode-equivalent"

##----------------------------------------------------------------------

def format_result(result):
    r = result['reasoning']
    return f"""
## 🎯 {result['leetcode_title']}

**🔗 Link:** [{result['leetcode_link']}]({result['leetcode_link']})  
**💪 Difficulty:** {result['difficulty']}  
**✅ Acceptance Rate:** {result['acceptance_rate']}%  
**🏷️ Topics:** {result['topics']}

---

## 🧠 Reasoning

**Pattern:** {r['pattern']}  
**Core Constraint:** {r['core_constraint']}  
**Why it matches:** {r['why_it_matches']}  
**Key Difference:** {r['key_difference']}  
**Confidence:** {r['confidence']}
"""

##----------------------------------------------------------------------

def find_leetcode_equivalent(input_problem):

    # Data payload (Python dictionary)
    payload = {
        "problem_statement": input_problem
    }

    # Send POST request
    # The json= parameter handles encoding and headers automatically
    response = requests.post(URL, json=payload)

    # Fetch and parse JSON response
    if response.status_code == 200:
        data = response.json()  # Converts JSON response into a Python dictionary
        return format_result(data)
    else:
        return f"Failed with status code: {response.status_code}"

##----------------------------------------------------------------------

if __name__ == "__main__":
    demo = gr.Interface(
        fn=find_leetcode_equivalent,
        inputs=gr.Textbox(lines=10, placeholder="Paste problem here..."),
        outputs=gr.Markdown(),
        api_name="get-leetcode-equivalent"
    )

    demo.launch()