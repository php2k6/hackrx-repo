from g4f.client import Client
import g4f.Provider

def identify_structure_and_convert_to_md(text):
    client = Client(provider=g4f.Provider.Blackbox) 
    prompt = f"""
Analyze the following text and identify its structure (headings, paragraphs, lists, tables, etc.). 
Important: No text should be omitted; if you don't understand its structure, just return it as it is.
Then convert it to properly formatted Markdown (no need to convert it in ``` ```).
Text:
{text}

Please return only the Markdown formatted version of the text with appropriate structure.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or another available model
        messages=[{"role": "user", "content": prompt}],
        web_search=False
    )
    return response.choices[0].message.content