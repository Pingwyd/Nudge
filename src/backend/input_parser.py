import uuid
import re
from datetime import datetime
from typing import List

# Words that legitimately end with a period mid-sentence (abbreviations)
_ABBREVIATIONS = frozenset({
    "Dr", "Mr", "Mrs", "Ms", "Prof", "Sr", "Jr",
    "St", "Ave", "Blvd", "Dept", "Est", "Fig", "Gov",
    "Inc", "Ltd", "Mt", "Rev", "Sgt", "vs", "etc",
    "al", "approx",
})


class InputParser:
    @staticmethod
    def parse_input(raw_text: str) -> List[dict]:
        """
        Splits text into tasks by identifying sentence boundaries.

        A period ends a sentence if followed by a space and an uppercase
        letter, AND the word before the period is NOT an abbreviation.

        Handles: abbreviations, ellipsis, decimals, trailing periods.
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

        # Final cleanup: trim trailing periods, strip, remove empties
        tasks = []
        for seg in segments:
            seg = seg.replace('\x00', '...').strip().rstrip('.').strip()
            if not seg:
                continue
            tasks.append({
                "id": str(uuid.uuid4()),
                "text": seg,
                "done": False,
                "createdAt": datetime.now().isoformat(),
                "order": 0,
            })

        return tasks

