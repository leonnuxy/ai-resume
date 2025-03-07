# app/utils/text_cleaner.py
import re

def clean_text(text: str) -> str:
    """Cleans up text extracted from a resume PDF.

    This function addresses several common issues:
    - Removes excessive whitespace.
    - Handles bullet points and list items more intelligently.
    - Correctly separates lines that should be separate (headings, etc.).
    - Replaces specific characters (like '¥' with '-').
    """

    # 1. Replace problematic characters *before* splitting into lines
    text = text.replace('¥', '-')
    text = text.replace('Ð', '-')  # Replace other common problematic characters

    # 2. Split into lines, and remove leading/trailing whitespace from each line.
    lines = [line.strip() for line in text.splitlines()]

    cleaned_lines = []
    for line in lines:
        if not line:  # Skip completely empty lines
            if cleaned_lines and cleaned_lines[-1] != "": #add empty lines *only* if there is none before
                cleaned_lines.append("") # Preserve paragraph breaks (double newlines)
            continue

        # 3. Heuristic for line joining:
        if cleaned_lines:
            prev_line = cleaned_lines[-1]

            # Join lines if:
            # - The previous line ends with a comma, hyphen, colon, or is very short.
            # - The current line starts with lowercase (likely a continuation).
            # - The previous line *doesn't* end with a period (avoid merging sentences)
            # - The previous line isn't a likely heading (all caps, short).
            if (
                prev_line.endswith((':', ',', '-',)) or
                (len(prev_line) < 60 and not prev_line.endswith('.')) or  # Short line, not ending in .
                (line and line[0].islower() and not prev_line.endswith('.')) or
                (prev_line and not prev_line.isupper() and len(prev_line.split()) > 3 ) #not all CAPS
            ):
                cleaned_lines[-1] += " " + line #append
                continue

        cleaned_lines.append(line)

    # 4. Join the lines back together.
    cleaned_text = '\n'.join(cleaned_lines)

    # 5. Remove excessive whitespace (multiple spaces) within the text.
    cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)  # Replace 2+ spaces with one space
    cleaned_text = re.sub(r'\t', ' ', cleaned_text)  # Replace tabs

    return cleaned_text