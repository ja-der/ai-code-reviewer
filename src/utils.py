def chunk_text(text: str, max_chars: int):
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        nl = text.rfind("\n", start, end)
        if nl > start:
            end = nl
        chunks.append(text[start:end])
        start = end
    return chunks
