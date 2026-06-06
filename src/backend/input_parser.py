import uuid
from datetime import datetime
from typing import List

class InputParser:
    @staticmethod
    def parse_input(raw_text: str) -> List[dict]:
        """
        Splits text by '.', trims whitespace, ignores empty strings, 
        and returns a list of Task dictionaries.
        """
        if not raw_text or not raw_text.strip():
            return []

        # Split by period and ignore entirely empty strings or spaces only
        segments = [seg.strip() for seg in raw_text.split(".") if seg.strip()]
        
        tasks = []
        for segment in segments:
            tasks.append({
                "id": str(uuid.uuid4()),
                "text": segment,
                "done": False,
                "createdAt": datetime.now().isoformat(),
                "order": 0 # This can be updated by the caller later if needed
            })
            
        return tasks

