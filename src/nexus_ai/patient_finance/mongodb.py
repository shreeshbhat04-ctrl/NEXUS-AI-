from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import voyageai

from nexus_ai.config import get_settings

logger = logging.getLogger(__name__)

# Global clients
_mongo_client: AsyncIOMotorClient | None = None
_voyage_client: voyageai.AsyncClient | None = None

KNOWN_COLLECTIONS = {
    "bills",
    "bill_audits",
    "loan_offers",
    "patient_gaps",
    "policy_chunks",
    "consent_logs",
    "finance_sessions",
    "phi_mappings",
    "submissions",
    "shared_agent_memories", # New: Cross-Agent Memory Store
}


async def init_mongodb() -> None:
    global _mongo_client, _voyage_client
    settings = get_settings()
    
    logger.info(f"Connecting to MongoDB at {settings.mongodb_uri}")
    _mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    
    # Verify connection
    await _mongo_client.admin.command('ping')
    logger.info("MongoDB connected successfully.")

    if settings.voyage_api_key:
        _voyage_client = voyageai.AsyncClient(api_key=settings.voyage_api_key)
        logger.info("Voyage AI client initialized for embeddings.")
    else:
        logger.warning("Voyage API key not set. Embeddings will not be generated.")

async def close_mongodb() -> None:
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None

async def ensure_indexes() -> None:
    db = get_database()
    
    # bill_audits
    await db["bill_audits"].create_index([("patient_id", 1), ("audit_timestamp", -1)])
    # loan_offers
    await db["loan_offers"].create_index([("patient_id", 1)])
    # policy_chunks
    await db["policy_chunks"].create_index([("source_doc_id", 1)])
    # consent_logs
    await db["consent_logs"].create_index([("patient_id", 1), ("created_at", -1)])
    
    # shared_agent_memories search index (Requires Atlas Vector Search setup on UI, but we can do regular indexes here)
    await db["shared_agent_memories"].create_index([("patient_id", 1)])
    await db["shared_agent_memories"].create_index([("category", 1)])
    
    logger.info("MongoDB indexes verified.")


def get_database() -> AsyncIOMotorDatabase:
    if _mongo_client is None:
        raise RuntimeError("MongoDB client not initialized. Call init_mongodb() first.")
    settings = get_settings()
    return _mongo_client[settings.mongodb_database]

def get_collection(name: str) -> AsyncIOMotorCollection:
    if name not in KNOWN_COLLECTIONS:
        raise KeyError(f"Unknown patient finance collection: {name}")
    return get_database()[name]


async def upsert_document(collection: str, document_id: str, payload: dict) -> str:
    coll = get_collection(collection)
    payload["_id"] = document_id
    await coll.replace_one({"_id": document_id}, payload, upsert=True)
    return document_id

async def insert_document(collection: str, payload: dict, *, document_id: str | None = None) -> str:
    target_id = document_id or f"{collection[:-1]}-{uuid4().hex[:12]}"
    payload["_id"] = target_id
    coll = get_collection(collection)
    await coll.insert_one(payload)
    return target_id

async def get_document(collection: str, document_id: str) -> dict | None:
    coll = get_collection(collection)
    return await coll.find_one({"_id": document_id})

async def delete_document(collection: str, document_id: str) -> None:
    coll = get_collection(collection)
    await coll.delete_one({"_id": document_id})

async def list_documents(collection: str) -> list[dict]:
    coll = get_collection(collection)
    return await coll.find().to_list(length=1000)


# --- Finance Specific Helpers ---

async def create_bill(
    *,
    patient_id: str,
    filename: str,
    content_type: str,
    raw_bytes: bytes,
    parsed_data: dict | None = None,
    drive_file_id: str | None = None,
    drive_link: str | None = None,
) -> str:
    bill_id = f"bill-{uuid4().hex[:12]}"
    payload = {
        "bill_id": bill_id,
        "patient_id": str(patient_id),
        "filename": filename,
        "content_type": content_type,
        "raw_size": len(raw_bytes),
        "parsed_data": parsed_data or {},
        "status": "uploaded",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if drive_file_id:
        payload["drive_file_id"] = drive_file_id
    if drive_link:
        payload["drive_link"] = drive_link
    await insert_document("bills", payload, document_id=bill_id)
    return bill_id

async def save_audit(bill_id: str, payload: dict) -> str:
    return await upsert_document("bill_audits", bill_id, payload)

async def get_audit(bill_id: str) -> dict | None:
    return await get_document("bill_audits", bill_id)

async def save_gap(bill_id: str, payload: dict) -> str:
    return await upsert_document("patient_gaps", bill_id, payload)

async def get_gap(bill_id: str) -> dict | None:
    return await get_document("patient_gaps", bill_id)


# --- Policy & Embeddings ---

async def generate_embedding(text: str) -> list[float]:
    if not _voyage_client:
        return []
    try:
        # Using Voyage-2 which is a standard general embedding model
        response = await _voyage_client.embed(
            texts=[text],
            model="voyage-2"
        )
        return response.embeddings[0]
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return []

async def save_policy_chunks(source_doc_id: str, payload: Iterable[dict]) -> None:
    collection = get_collection("policy_chunks")
    for chunk in payload:
        chunk_id = chunk.get("chunk_id")
        if chunk_id is None:
            raise KeyError("Policy chunk is missing a chunk_id.")
        
        # Generate Voyage embedding for semantic search
        text = chunk.get("text", "")
        if text and _voyage_client:
            chunk["embedding"] = await generate_embedding(text)
            
        doc_id = f"{source_doc_id}:{chunk_id}"
        chunk["_id"] = doc_id
        await collection.replace_one({"_id": doc_id}, chunk, upsert=True)

async def get_policy_chunks(source_doc_id: str) -> list[dict]:
    collection = get_collection("policy_chunks")
    prefix = f"{source_doc_id}:"
    return await collection.find({"_id": {"$regex": f"^{prefix}"}}).to_list(length=1000)

async def search_policy_chunks(query: str, limit: int = 5) -> list[dict]:
    # Semantic search using Voyage AI embeddings
    if not _voyage_client:
        return []
    query_emb = await generate_embedding(query)
    
    # Requires MongoDB Atlas Vector Search index named "vector_index" on policy_chunks
    collection = get_collection("policy_chunks")
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_emb,
                "numCandidates": limit * 10,
                "limit": limit
            }
        }
    ]
    try:
        results = await collection.aggregate(pipeline).to_list(length=limit)
        return results
    except Exception as e:
        logger.error(f"Vector search failed (check Atlas index): {e}")
        return []


# --- Shared Agent Memory (Cross-Agent Context) ---

async def write_shared_memory(patient_id: str, source_agent: str, category: str, memory_text: str, importance_score: float = 1.0) -> str:
    """
    Writes a memory to the global agent shared memory store.
    Categories: 'financial', 'dietary', 'emotional', 'adherence'
    """
    memory_id = f"mem-{uuid4().hex[:12]}"
    embedding = await generate_embedding(memory_text)
    
    payload = {
        "_id": memory_id,
        "patient_id": str(patient_id),
        "source_agent": source_agent,
        "category": category,
        "text": memory_text,
        "importance_score": importance_score,
        "embedding": embedding,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await get_collection("shared_agent_memories").insert_one(payload)
    return memory_id

async def search_shared_memories(patient_id: str, query: str, limit: int = 5) -> list[dict]:
    """
    Retrieves relevant memories for a specific patient across all agents.
    """
    if not _voyage_client:
        return []
    query_emb = await generate_embedding(query)
    
    collection = get_collection("shared_agent_memories")
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_emb,
                "numCandidates": limit * 10,
                "limit": limit,
                "filter": {"patient_id": {"$eq": str(patient_id)}}
            }
        }
    ]
    try:
        results = await collection.aggregate(pipeline).to_list(length=limit)
        return results
    except Exception:
        return []


# --- Other Helpers ---

async def save_offers(bill_id: str, patient_id: str, offers: list[dict]) -> None:
    await upsert_document(
        "loan_offers",
        bill_id,
        {
            "bill_id": bill_id,
            "patient_id": str(patient_id),
            "offers": offers,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

async def get_offers(bill_id: str) -> list[dict]:
    payload = await get_document("loan_offers", bill_id)
    if not payload:
        return []
    return payload.get("offers", [])

async def save_consent(payload: dict, *, consent_id: str) -> str:
    return await upsert_document("consent_logs", consent_id, payload)

async def get_consent(consent_id: str) -> dict | None:
    return await get_document("consent_logs", consent_id)

async def save_submission(submission_id: str, payload: dict) -> str:
    return await upsert_document("submissions", submission_id, payload)

async def save_phi_mapping(session_id: str, mapping: dict[str, str]) -> None:
    await upsert_document(
        "phi_mappings",
        session_id,
        {
            "session_id": session_id,
            "mapping": mapping,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

async def get_phi_mapping(session_id: str) -> dict[str, str]:
    payload = await get_document("phi_mappings", session_id)
    if not payload:
        return {}
    return payload.get("mapping", {})

async def save_session_snapshot(patient_id: str, payload: dict) -> None:
    await upsert_document("finance_sessions", str(patient_id), payload)

async def get_session_snapshot(patient_id: str) -> dict | None:
    return await get_document("finance_sessions", str(patient_id))

async def clear_session_snapshot(patient_id: str) -> None:
    await delete_document("finance_sessions", str(patient_id))
