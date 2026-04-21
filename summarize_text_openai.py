from openai import OpenAI

def summarize_text_openai(text, lang="English", size="topic"):
    LENGTH_CONFIG = {
         "short":  "Summarize in 1 short paragraph (3-4 sentences).",
        "medium": "Summarize in 2-3 paragraphs (4-5 sentences each).",
        "long":   "Summarize in 4-5 detailed paragraphs (5-7 sentences each).",
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

    client = OpenAI(api_key="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") # Pavithra's OpenAI API key

    prompt = f"{LENGTH_CONFIG[size]}\n\nRespond in {lang}.\n\nTranscript:\n{text}"
    


    response = client.chat.completions.create(
        model="gpt-3.5-turbo",   # or use "gpt-4o" for better quality
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )

    return response.choices[0].message.content