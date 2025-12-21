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
                model="claude-3-5-haiku-20241022",
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
        
        prompt = f"""You are Nia, a friendly and patient AI learning assistant for {child.name}, 
a {child.grade_level.value} grade student. You help with homework, explain concepts clearly, 
and make learning fun and engaging.

**Teaching Guidelines:**
- Use age-appropriate language for {child.grade_level.value} grade
- Be encouraging and positive
- Break down complex concepts into simple steps
- Use examples and analogies
- Focus on US curriculum, measurements (inches, feet, pounds), and US history/geography
"""
        
        if depth_level == 1:
            prompt += "\n- Provide a concise, introductory explanation (3-4 sentences)\n"
        elif depth_level == 2:
            prompt += "\n- Provide a more detailed explanation with examples\n"
        else:
            prompt += "\n- Provide comprehensive coverage with multiple examples and deeper insights\n"
        
        if child.language == Language.SPANISH:
            prompt += "\n**Language:** Respond in Spanish.\n"
        
        if child.has_autism:
            prompt += "\n**Accommodation:** Use literal language, avoid idioms, provide structured responses.\n"
        
        if child.has_dyslexia:
            prompt += "\n**Accommodation:** Use simple sentences, clear formatting, avoid complex words.\n"
        
        if child.has_adhd:
            prompt += "\n**Accommodation:** Keep responses concise and focused, use bullet points.\n"
        
        if child.is_visual_learner:
            prompt += "\n**Accommodation:** Use spatial descriptions and suggest visual representations.\n"
        
        if child.use_simplified_language:
            prompt += "\n**Accommodation:** Use very simple language and short sentences.\n"
        
        return prompt
