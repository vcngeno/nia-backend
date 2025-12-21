"""
Conversation Management Service - Automatic Folder Categorization
"""
from models import FolderCategory
import logging

logger = logging.getLogger(__name__)


class ConversationService:
    """Manages conversation categorization and organization"""
    
    @staticmethod
    def categorize_conversation(title: str, first_message: str) -> FolderCategory:
        """Automatically categorize conversation into appropriate folder"""
        content = f"{title} {first_message}".lower()
        
        math_keywords = [
            "math", "number", "add", "subtract", "multiply", "divide", "fraction",
            "decimal", "algebra", "geometry", "equation", "calculate", "sum",
            "product", "quotient", "percent", "ratio", "solve", "times", "plus",
            "minus", "equal", "graph", "angle", "triangle", "area", "perimeter"
        ]
        
        science_keywords = [
            "science", "biology", "chemistry", "physics", "experiment", "cell",
            "atom", "molecule", "energy", "force", "matter", "plant", "animal",
            "ecosystem", "photosynthesis", "respiration", "water cycle", "weather",
            "climate", "rock", "mineral", "solar system", "planet", "gravity",
            "organism", "habitat", "species"
        ]
        
        history_keywords = [
            "history", "war", "president", "revolution", "george washington",
            "abraham lincoln", "civil war", "independence", "constitution",
            "colony", "native american", "explorer", "settlement", "slavery",
            "amendment", "declaration", "battle", "treaty", "ancient", "century"
        ]
        
        english_keywords = [
            "grammar", "writing", "sentence", "verb", "noun", "adjective",
            "essay", "paragraph", "punctuation", "comma", "period", "pronoun",
            "adverb", "conjunction", "reading", "story", "poem", "author",
            "character", "plot", "theme", "metaphor"
        ]
        
        geography_keywords = [
            "geography", "state", "country", "capital", "continent", "ocean",
            "mountain", "river", "map", "location", "region", "population",
            "border", "territory", "hemisphere", "equator", "latitude", "longitude",
            "climate zone", "landscape"
        ]
        
        travel_keywords = [
            "travel", "trip", "vacation", "visit", "distance", "miles", "kilometers",
            "how far", "journey", "destination", "route", "flight", "drive"
        ]
        
        scores = {
            FolderCategory.MATH: sum(1 for kw in math_keywords if kw in content),
            FolderCategory.SCIENCE: sum(1 for kw in science_keywords if kw in content),
            FolderCategory.HISTORY: sum(1 for kw in history_keywords if kw in content),
            FolderCategory.ENGLISH: sum(1 for kw in english_keywords if kw in content),
            FolderCategory.GEOGRAPHY: sum(1 for kw in geography_keywords if kw in content),
            FolderCategory.TRAVEL: sum(1 for kw in travel_keywords if kw in content),
        }
        
        max_score = max(scores.values())
        
        if max_score == 0:
            logger.info(f"No specific category detected, using General folder")
            return FolderCategory.GENERAL
        
        for category, score in scores.items():
            if score == max_score:
                logger.info(f"Categorized as {category.value} (score: {score})")
                return category
        
        return FolderCategory.GENERAL
    
    @staticmethod
    def generate_title(first_message: str, max_length: int = 50) -> str:
        """Generate conversation title from first message"""
        title = first_message.strip()
        title = title.replace('?', '')
        
        if title:
            title = title[0].upper() + title[1:]
        
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0] + '...'
        
        return title if title else "New Conversation"
