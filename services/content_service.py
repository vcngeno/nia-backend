"""
Content Management Service - Educational Content Ingestion
"""
from pathlib import Path
from typing import List, Optional
import hashlib
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import EducationalContent

logger = logging.getLogger(__name__)


class ContentService:
    """Manages educational content ingestion and storage"""
    
    def __init__(self, content_dir: str = "educational_content"):
        self.content_dir = Path(content_dir)
    
    def parse_content_file(self, file_path: Path) -> Optional[dict]:
        """Parse markdown content file and extract metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            relative_path = file_path.relative_to(self.content_dir)
            parts = relative_path.parts
            
            subject = parts[0] if len(parts) > 0 else "general"
            grade_level = parts[1] if len(parts) > 1 else "general"
            topic = file_path.stem.replace('_', ' ').title()
            
            lines = content.split('\n')
            title = topic
            for line in lines:
                if line.startswith('# '):
                    title = line.replace('# ', '').strip()
                    break
            
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            return {
                'title': title,
                'subject': subject,
                'grade_level': grade_level,
                'topic': topic,
                'content': content,
                'content_hash': content_hash,
                'file_path': str(relative_path),
                'word_count': len(content.split())
            }
        
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None
    
    def discover_content_files(self) -> List[Path]:
        """Find all markdown files in content directory"""
        if not self.content_dir.exists():
            logger.warning(f"Content directory {self.content_dir} not found")
            return []
        
        files = list(self.content_dir.rglob("*.md"))
        logger.info(f"Found {len(files)} content files")
        return files
    
    async def ingest_content_file(
        self,
        file_path: Path,
        db: AsyncSession,
        force_update: bool = False
    ) -> Optional[EducationalContent]:
        """Ingest single content file into database"""
        
        metadata = self.parse_content_file(file_path)
        if not metadata:
            return None
        
        try:
            result = await db.execute(
                select(EducationalContent).where(
                    EducationalContent.file_path == metadata['file_path']
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                if force_update or existing.content_hash != metadata['content_hash']:
                    existing.content = metadata['content']
                    existing.content_hash = metadata['content_hash']
                    existing.word_count = metadata['word_count']
                    existing.title = metadata['title']
                    await db.commit()
                    logger.info(f"Updated: {metadata['title']}")
                    return existing
                else:
                    logger.info(f"Skipped (unchanged): {metadata['title']}")
                    return existing
            else:
                new_content = EducationalContent(**metadata)
                db.add(new_content)
                await db.commit()
                await db.refresh(new_content)
                logger.info(f"Added: {metadata['title']}")
                return new_content
        
        except Exception as e:
            logger.error(f"Error ingesting {file_path}: {e}")
            await db.rollback()
            return None
    
    async def ingest_all_content(self, db: AsyncSession) -> int:
        """Ingest all content files from directory"""
        files = self.discover_content_files()
        
        if not files:
            logger.warning("No content files found to ingest")
            return 0
        
        success_count = 0
        for file_path in files:
            result = await self.ingest_content_file(file_path, db)
            if result:
                success_count += 1
        
        logger.info(f"Content ingestion complete: {success_count}/{len(files)} files processed")
        return success_count
