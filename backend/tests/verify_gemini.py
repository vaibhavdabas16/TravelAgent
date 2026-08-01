import asyncio
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_gemini():
    print("=" * 50)
    print("VERIFYING GEMINI API")
    print("=" * 50)
    
    try:
        print(f"API Key present: {bool(settings.gemini_api_key)}")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0
        )
        
        print("Sending test message...")
        response = await llm.ainvoke([HumanMessage(content="Hello, are you working?")])
        
        print(f"\n✅ Success! Response: {response.content}")
        
    except Exception as e:
        print(f"\n❌ Gemini verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_gemini())
