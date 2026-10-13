import anthropic
import os

# Get API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("Set ANTHROPIC_API_KEY before running the model probe.")
    raise SystemExit(0)

print(f"Using API key: {api_key[:20]}...")
client = anthropic.Anthropic(api_key=api_key)

models_to_test = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620", 
    "claude-3-haiku-20240307",
    "claude-3-opus-20240229",
    "claude-sonnet-4-20250514",
    "claude-3-5-haiku-20241022",
]

print("\nTesting Anthropic models...\n")

for model in models_to_test:
    try:
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}]
        )
        print(f"✅ {model} - WORKS!")
    except Exception as e:
        error_msg = str(e)[:80]
        print(f"❌ {model} - {error_msg}")
