from groq import Groq

def summarize_text_groq(text, lang="English", size="medium"):
    LENGTH_CONFIG = {
        "short":  "Summarize in 1 short paragraph (3–4 sentences).",
        "medium": "Summarize in 2–3 paragraphs (4–5 sentences each).",
        "long":   "Summarize in 4–5 detailed paragraphs (5–7 sentences each).",
       "topic":  (
            "Analyze this transcript which contains timestamps in [M:SS] format.\n"
            "Organize the summary into these 4 fixed sections.\n"
            "For each section, find the start timestamp where that topic begins "
            "and the end timestamp where it ends, then include the duration range.\n\n"
            "Format your response exactly like this:\n"
            "**Introduction** `[0:00 - M:SS]`\n"
            "[2-3 sentences about what the video covers]\n\n"
            "**Main Concepts** `[M:SS - M:SS]`\n"
            "[6-7 sentences about the core ideas presented]\n\n"
            "**Key Examples** `[M:SS - M:SS]`\n"
            "[2-3 sentences about specific examples or demos shown]\n\n"
            "**Conclusion** `[M:SS - M:SS]`\n"
            "[2-3 sentences about final takeaways]\n\n"
            "Use only timestamps that actually appear in the transcript.\n"
            "The end timestamp of one section should be the start timestamp of the next."
        )
    }
    client = Groq(api_key="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") # other
    # client = Groq(api_key = "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") # Pavithra's account
    prompt = f"{LENGTH_CONFIG[size]}\n\nRespond in {lang}.\n\nTranscript:\n{text}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )
    return response.choices[0].message.content