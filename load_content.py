"""
Load educational content from markdown files into database
"""
import os
import re
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import EducationalContent, Base
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get DATABASE_URL from environment and convert to synchronous
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

# Convert asyncpg to psycopg2 (synchronous)
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

print(f"Using database: {DATABASE_URL[:50]}...")

# Create database engine (synchronous)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def parse_frontmatter(content: str):
    """Parse YAML frontmatter from markdown"""
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_text = parts[1].strip()
    body = parts[2].strip()
    
    metadata = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Parse lists
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip() for v in value[1:-1].split(',')]
            
            metadata[key] = value
    
    return metadata, body

def calculate_hash(content: str) -> str:
    """Calculate hash of content for change detection"""
    return hashlib.md5(content.encode()).hexdigest()

def count_words(text: str) -> int:
    """Count words in text"""
    return len(re.findall(r'\w+', text))

def load_content_files():
    """Load all markdown files from educational_content directory"""
    db = SessionLocal()
    
    content_dir = Path("educational_content")
    loaded_count = 0
    updated_count = 0
    skipped_count = 0
    
    # Find all markdown files
    md_files = list(content_dir.rglob("*.md"))
    
    print(f"\nFound {len(md_files)} markdown files\n")
    
    for file_path in md_files:
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter and content
            metadata, body = parse_frontmatter(content)
            
            if not metadata:
                print(f"⚠️  Skipping {file_path.name} - no frontmatter found")
                skipped_count += 1
                continue
            
            # Calculate content hash
            content_hash = calculate_hash(content)
            
            # Check if content already exists
            existing = db.query(EducationalContent).filter(
                EducationalContent.file_path == str(file_path)
            ).first()
            
            if existing:
                # Check if content changed
                if existing.content_hash == content_hash:
                    print(f"⏭️  {file_path.name} - already loaded, no changes")
                    skipped_count += 1
                    continue
                
                # Update existing content
                existing.title = metadata.get('title', 'Untitled')
                existing.subject = metadata.get('subject', 'general')
                existing.content = body
                existing.content_hash = content_hash
                existing.word_count = count_words(body)
                existing.updated_at = datetime.utcnow()
                
                # Handle grade_levels (could be list or string)
                grade_levels = metadata.get('grade_levels', [])
                if isinstance(grade_levels, list):
                    existing.grade_level = ','.join(str(g) for g in grade_levels)
                else:
                    existing.grade_level = str(grade_levels)
                
                # Handle topics (could be list or string)
                topics = metadata.get('topics', [])
                if isinstance(topics, list):
                    existing.topic = ','.join(topics)
                else:
                    existing.topic = str(topics)
                
                print(f"✓ Updated: {file_path.name}")
                updated_count += 1
            else:
                # Create new content entry
                grade_levels = metadata.get('grade_levels', [])
                if isinstance(grade_levels, list):
                    grade_level_str = ','.join(str(g) for g in grade_levels)
                else:
                    grade_level_str = str(grade_levels)
                
                topics = metadata.get('topics', [])
                if isinstance(topics, list):
                    topic_str = ','.join(topics)
                else:
                    topic_str = str(topics)
                
                new_content = EducationalContent(
                    title=metadata.get('title', 'Untitled'),
                    subject=metadata.get('subject', 'general'),
                    grade_level=grade_level_str,
                    topic=topic_str,
                    content=body,
                    file_path=str(file_path),
                    content_hash=content_hash,
                    word_count=count_words(body)
                )
                
                db.add(new_content)
                print(f"✓ Loaded: {file_path.name} ({metadata.get('title', 'Untitled')})")
                loaded_count += 1
            
            db.commit()
            
        except Exception as e:
            print(f"❌ Error loading {file_path.name}: {e}")
            db.rollback()
    
    db.close()
    
    print("\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   ✓ New files loaded: {loaded_count}")
    print(f"   ↻ Files updated: {updated_count}")
    print(f"   ⏭  Files skipped (no changes): {skipped_count}")
    print(f"   📁 Total processed: {len(md_files)}")
    print("="*60)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📚 Loading Educational Content into Database")
    print("="*60)
    load_content_files()
    print("\n✅ Done!\n")
