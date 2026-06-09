import sys
import os
import asyncio
print("Built-ins loaded")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

print("Importing SharedMemoryManager...")
from nexus_ai.memory.shared_memory import SharedMemoryManager
print("Importing ModelRoutingService...")
from nexus_ai.services.model_routing import ModelRoutingService
print("Imports finished")

async def test_shared_memory():
    print("Testing SharedMemoryManager...")
    manager = SharedMemoryManager()
    
    # 1. Save a mock memory
    patient_id = 12345
    print("\n1. Saving memory from Diet Agent...")
    success = await manager.save_memory(
        patient_id=patient_id,
        source_agent="diet_agent",
        content="The patient has a severe peanut allergy and prefers a high-protein diet.",
        metadata={"confidence": 0.95}
    )
    if success:
        print("✅ Successfully saved memory with Voyage AI embeddings to MongoDB!")
    else:
        print("❌ Failed to save memory.")
        
    # 2. Test Model Routing Injection
    print("\n2. Testing Dynamic Thinking Style Injection (Cart Agent)...")
    router = ModelRoutingService()
    base_prompt = "You are the Cart Agent. Suggest items for the user to buy today."
    
    dynamic_prompt = await router.append_dynamic_thinking_style(
        patient_id=patient_id,
        base_prompt=base_prompt,
        context_query="Dietary restrictions and allergies"
    )
    
    print("\n--- Final Generated Prompt for Cart Agent ---")
    print(dynamic_prompt)
    print("---------------------------------------------")
    
if __name__ == "__main__":
    asyncio.run(test_shared_memory())
