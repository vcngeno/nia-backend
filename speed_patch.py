with open('services/rag_service.py', 'r') as f:
    content = f.read()

# Ultra-fast settings
content = content.replace(
    'max_tokens=400 if depth_level == 1 else 600 if depth_level == 2 else 800',
    'max_tokens=200'  # Very short responses
)
content = content.replace(
    'temperature=0.7',
    'temperature=0.1'  # More direct, less creative
)
content = content.replace(
    'conversation_history[-4:]',
    'conversation_history[-1:]'  # Only last message
)

with open('services/rag_service.py', 'w') as f:
    f.write(content)

print("🚀 ULTRA FAST MODE ENABLED")
