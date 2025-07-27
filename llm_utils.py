from g4f.client import Client

def answer_from_chunks(query, chunks, model="gpt-4o"):
    if not chunks:
        return "No relevant content found."
    context = "\n\n".join([
        f"Section: {section}\n{content}" for section, content in chunks
    ])
    client = Client()
    prompt = f"""
You are an expert at reading insurance documents. Use the provided sections to answer the user's question. If the answer is not present, say so.

User question: {query}

Relevant document sections:
{context}

Return a well-structured, concise answer. If possible, cite the section(s) you used.
Do not include any Markdown formatting in the response.
keep it very concise and to the point.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        web_search=False
    )
    return response.choices[0].message.content
