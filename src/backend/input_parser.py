import uuid
import re
from datetime import datetime
from typing import List, Tuple

# Words that legitimately end with a period mid-sentence (abbreviations)
_ABBREVIATIONS = frozenset({
    "Dr", "Mr", "Mrs", "Ms", "Prof", "Sr", "Jr",
    "St", "Ave", "Blvd", "Dept", "Est", "Fig", "Gov",
    "Inc", "Ltd", "Mt", "Rev", "Sgt", "vs", "etc",
    "al", "approx",
})


class InputParser:
    @staticmethod
    def _parse_prefixes(text: str) -> Tuple[str, str, list]:
        """
        Parse ! priority prefix and #tags from text.
        
        Returns: (priority, text_without_prefixes, tags)
        """
        priority = None
        tags = []
        
        # Extract #tags first (before removing ! to preserve order)
        tag_matches = re.findall(r'#(\w+)', text)
        tags = [tag.lower() for tag in tag_matches]
        
        # Remove #tags from text
        text_no_tags = re.sub(r'#\w+\s*', '', text).strip()
        
        # Check for ! priority prefix (must be at start)
        if text_no_tags.startswith('!'):
            priority = "high"
            text_no_priority = text_no_tags[1:].lstrip()
            # Handle edge case: ! alone with no other text
            if not text_no_priority:
                return None, "", []
            return priority, text_no_priority, tags
        
        return priority, text_no_tags, tags

    @staticmethod
    def parse_input(raw_text: str) -> List[dict]:
        """
        Splits text into tasks by identifying sentence boundaries.

        A period ends a sentence if followed by a space and an uppercase
        letter, AND the word before the period is NOT an abbreviation.

        Handles: abbreviations, ellipsis, decimals, trailing periods.
        Also parses ! priority prefix and #tags.
        """
        if not raw_text or not raw_text.strip():
            return []

        text = raw_text.strip()

        # Protect ellipsis sequences from being treated as sentence ends
        text = re.sub(r'\.{3,}', '\x00', text)

        # Split on ". " followed by uppercase letter
        raw_parts = re.split(r'\.\s+(?=[A-Z])', text)

        # Re-join parts where the left side is just an abbreviation
        segments = []
        i = 0
        while i < len(raw_parts):
            part = raw_parts[i].replace('\x00', '...').strip()
            # Check if this part is a bare abbreviation (e.g. "Dr")
            last_word = part.rsplit(None, 1)[-1] if part else ""
            if last_word in _ABBREVIATIONS and i + 1 < len(raw_parts):
                next_part = raw_parts[i + 1].replace('\x00', '...').strip()
                segments.append(f"{part}. {next_part}")
                i += 2
            else:
                segments.append(part)
                i += 1

        # Final cleanup: trim trailing periods, strip, remove empties, parse prefixes
        tasks = []
        for seg in segments:
            seg = seg.replace('\x00', '...').strip().rstrip('.').strip()
            if not seg:
                continue
            
            # Parse priority and tags from segment
            priority, clean_text, tags = InputParser._parse_prefixes(seg)
            
            # Skip if text is empty after parsing (e.g., just "!")
            if not clean_text:
                continue
            
            tasks.append({
                "id": str(uuid.uuid4()),
                "text": clean_text,
                "done": False,
                "createdAt": datetime.now().isoformat(),
                "order": 0,
                "dueDate": None,
                "priority": priority,
                "tags": tags,
                "recurrence": None,
            })

        return tasks

