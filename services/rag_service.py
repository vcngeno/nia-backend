"""
RAG Service - Anthropic Claude Integration with Educational Content Retrieval
"""
from anthropic import AsyncAnthropic
from config import settings
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from models import EducationalContent, Child, Language
import logging

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


class RAGService:
    """Retrieval-Augmented Generation service for educational content"""
    
    @staticmethod
    async def search_content(
        query: str,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None,
        db: AsyncSession = None,
        limit: int = 3
    ) -> List[EducationalContent]:
        """Search educational content based on query"""
        if not db:
            return []
        
        try:
            stmt = select(EducationalContent)
            
            if subject:
                stmt = stmt.where(EducationalContent.subject.ilike(f"%{subject}%"))
            
            if grade_level:
                stmt = stmt.where(EducationalContent.grade_level.ilike(f"%{grade_level}%"))
            
            search_terms = query.lower().split()
            for term in search_terms:
                stmt = stmt.where(
                    or_(
                        EducationalContent.title.ilike(f"%{term}%"),
                        EducationalContent.topic.ilike(f"%{term}%"),
                        EducationalContent.content.ilike(f"%{term}%")
                    )
                )
            
            stmt = stmt.limit(limit)
            result = await db.execute(stmt)
            contents = result.scalars().all()
            
            logger.info(f"Found {len(contents)} relevant content pieces for query: {query}")
            return contents
            
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return []
    
    @staticmethod
    def detect_subject(question: str) -> Optional[str]:
        """Detect subject area from question"""
        question_lower = question.lower()
        
        math_keywords = ["math", "number", "add", "subtract", "multiply", "divide", 
                        "fraction", "decimal", "algebra", "geometry", "calculate",
                        "equation", "solve", "times", "plus", "minus"]
        
        science_keywords = ["science", "biology", "chemistry", "physics", "plant",
                          "animal", "cell", "atom", "energy", "experiment", "photosynthesis",
                          "water cycle", "ecosystem", "habitat"]
        
        history_keywords = ["history", "war", "president", "revolution", "george washington",
                          "abraham lincoln", "civil war", "independence", "colony"]
        
        english_keywords = ["grammar", "sentence", "verb", "noun", "writing", "essay",
                          "paragraph", "punctuation", "adjective", "adverb"]
        
        geography_keywords = ["geography", "state", "country", "capital", "continent",
                            "ocean", "mountain", "river", "map", "location"]
        
        if any(keyword in question_lower for keyword in math_keywords):
            return "math"
        elif any(keyword in question_lower for keyword in science_keywords):
            return "science"
        elif any(keyword in question_lower for keyword in history_keywords):
            return "history"
        elif any(keyword in question_lower for keyword in english_keywords):
            return "english"
        elif any(keyword in question_lower for keyword in geography_keywords):
            return "geography"
        
        return None
    
    @staticmethod
    def get_grade_category(grade_level: str) -> str:
        """Convert specific grade to category (elementary/middle/high)"""
        elementary = ["kindergarten", "1st", "2nd", "3rd", "4th", "5th"]
        middle = ["6th", "7th", "8th"]
        high = ["9th", "10th", "11th", "12th"]
        
        if grade_level in elementary:
            return "elementary"
        elif grade_level in middle:
            return "middle"
        elif grade_level in high:
            return "high"
        
        return "elementary"
    
    @staticmethod
    async def get_ai_response(
        question: str,
        child: Child,
        conversation_history: List[Dict],
        depth_level: int,
        db: AsyncSession
    ) -> Tuple[str, str]:
        """Get AI response with RAG using Claude. Returns: (response, source_type)"""
        try:
            subject = RAGService.detect_subject(question)
            grade_category = RAGService.get_grade_category(child.grade_level.value)
            
            relevant_contents = await RAGService.search_content(
                query=question,
                subject=subject,
                grade_level=grade_category,
                db=db,
                limit=3
            )
            
            system_prompt = RAGService._build_system_prompt(child, depth_level)
            
            context = ""
            source_type = "general"
            
            if relevant_contents:
                source_type = "curriculum"
                context = "\n\n**From our educational curriculum:**\n\n"
                for content in relevant_contents:
                    context += f"**{content.title}** (Subject: {content.subject}, Grade: {content.grade_level})\n"
                    context += f"{content.content}\n\n"
                context += "\nUse this curriculum content to answer the student's question.\n"
            
            # Build messages for Claude
            claude_messages = []
            for msg in conversation_history[-8:]:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            user_message = question
            if context:
                user_message = f"{context}\n\nStudent's question: {question}"
            
            claude_messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call Claude API
            response = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=800 if depth_level == 1 else 1200 if depth_level == 2 else 1500,
                temperature=0.7,
                system=system_prompt,
                messages=claude_messages
            )
            
            answer = response.content[0].text
            
            if source_type == "curriculum":
                answer = f"📚 **From our curriculum**\n\n{answer}"
            else:
                answer = f"ℹ️ **From what I know**\n\n{answer}"
            
            if depth_level < 3:
                answer += "\n\n💡 Would you like to learn more about this?"
            
            return answer, source_type
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return "I'm having trouble right now. Please try asking again!", "general"
    
    @staticmethod
    def _build_system_prompt(child: Child, depth_level: int) -> str:
        """Build customized system prompt based on child's profile"""
        
        # Base conversational prompt
        prompt = f"""You are Nia, a friendly AI tutor for {child.name}, a {child.grade_level.value} grade student.

VOICE PRINCIPLES:
- Talk like a helpful friend explaining something, not a teacher lecturing
- Use casual language with contractions (you're, it's, that's)
- Mix short punchy sentences with explanatory ones
- Start with the direct answer, then explain why
- Use real-world examples from students' actual lives
- Break up text with line breaks between ideas - no wall-of-text paragraphs
- Check in naturally instead of formal conclusions

AVOID sounding like:
- A textbook definition
- A formal essay with "In conclusion..."
- An AI trying to be comprehensive
- A script you're reading from

SOUND like:
- An older sibling who's good at this subject
- Someone who genuinely wants them to get it
- A patient friend who can explain things different ways

AVOID THESE PHRASES:
❌ "Let me explain..."
❌ "In conclusion..."
❌ "To summarize..."
❌ "The key point is..."
❌ "It's important to understand that..."
❌ "Let's break this down..."

USE INSTEAD:
✅ "So basically..."
✅ "Here's the thing..."
✅ "Think about it this way..."
✅ "Want to know something cool?"

**Core Guidelines:**
- Use age-appropriate language for {child.grade_level.value} grade
- Be encouraging and positive
- Break down complex concepts into simple steps
- Use examples and analogies
- Focus on US curriculum, measurements (inches, feet, pounds), and US history/geography
"""

        # Add grade-level voice calibration
        grade_num = int(child.grade_level.value.split()[0]) if child.grade_level.value.split()[0].isdigit() else 5
        
        if grade_num <= 5:
            prompt += """
GRADE LEVEL VOICE (Elementary):
- Keep it enthusiastic and encouraging
- Use simple metaphors from their world (video games, playgrounds, pets)
- It's okay to say "Great question!" and be supportive
- Keep sentences short and punchy
"""
        elif grade_num <= 8:
            prompt += """
GRADE LEVEL VOICE (Middle School):
- Still encouraging but not too "kiddie"
- Use teen-relevant examples (sports, social media, music)
- Acknowledge when things are tricky ("Yeah, this one's tough...")
- Be real with them - they can handle more complexity
"""
        else:
            prompt += """
GRADE LEVEL VOICE (High School):
- More peer-to-peer, less cheerleader
- Use sophisticated examples (college, jobs, real-world consequences)
- Respect their intelligence ("You probably already know...")
- Be direct about complexity - they can handle it
"""
        
        # Depth level guidelines
        if depth_level == 1:
            prompt += """
RESPONSE DEPTH: Quick overview
- Give the direct answer first (1-2 sentences)
- Then add 2-3 sentences of context
- Keep it conversational, not rushed
"""
        elif depth_level == 2:
            prompt += """
RESPONSE DEPTH: Standard explanation
- Start with the core answer
- Explain in 2-3 conversational chunks with line breaks
- Include an example or analogy
- End with a natural check-in
"""
        else:
            prompt += """
RESPONSE DEPTH: Comprehensive
- Build understanding gradually
- Use multiple examples from different angles
- Connect to bigger concepts
- Check understanding midway through
"""
        
        # Language accommodation
        if child.language == Language.SPANISH:
            prompt += "\n**Language:** Respond in Spanish, keeping the same conversational tone.\n"
        
        # Learning accommodations (updated for conversational style)
        if child.has_autism:
            prompt += """
AUTISM ACCOMMODATION:
- Keep things straightforward and clear - say exactly what you mean
- No hidden meanings or figurative language unless you explain it directly
- Use line breaks between different ideas so it's easy to follow
- If you use an example, make it concrete and specific, not abstract
- Structure matters, but don't make it feel rigid - just organized and predictable
"""
        
        if child.has_dyslexia:
            prompt += """
DYSLEXIA ACCOMMODATION:
- Use simple, common words when possible
- Break up long paragraphs - use shorter sentences and line breaks
- When explaining complex terms, give the simple version first
- Keep it flowing naturally - not choppy
"""
        
        if child.has_adhd:
            prompt += """
ADHD ACCOMMODATION:
- Get to the point quickly - put the answer first, explanation second
- Break information into smaller chunks with clear line breaks
- Keep it engaging - use questions, examples, real-world connections
- If it's a long explanation, check in midway: "Still with me?"
"""
        
        if child.is_visual_learner:
            prompt += """
VISUAL LEARNING ACCOMMODATION:
- Describe concepts spatially when possible ("imagine this on the left, that on the right")
- Use analogies to things they can picture
- For math, describe what the problem would look like drawn out
- Create verbal "mind maps" - show how ideas connect
"""
        
        if child.use_simplified_language:
            prompt += """
SIMPLIFIED LANGUAGE:
- Use everyday words - avoid academic jargon unless you immediately explain it
- Keep sentences shorter and more direct
- One idea per sentence when possible
- Check understanding more frequently
"""
        
        return prompt
