import hashlib
import json
import math
from pathlib import Path

from sqlalchemy import text
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_ai.config import get_settings
from nexus_ai.db.models import MedicalMemory


class MedicalMemoryAdapter:
    def __init__(self, dimensions: int = 16) -> None:
        self.settings = get_settings()
        self.dimensions = dimensions

    def store_memory(
        self,
        db: Session,
        patient_id: int,
        source_type: str,
        modality: str,
        content: str,
        source_reference: str | None = None,
        drive_file_id: str | None = None,
        drive_file_url: str | None = None,
        drive_path: str | None = None,
        metadata: dict | None = None,
        embedding_vector: list[float] | None = None,
        embedding_model: str | None = None,
    ) -> tuple[MedicalMemory, bool]:
        resolved_embedding_model = embedding_model or self._embedding_model_for_modality(modality)
        vector = embedding_vector or self._build_placeholder_embedding(content, modality)
        memory = MedicalMemory(
            patient_id=patient_id,
            source_type=source_type,
            source_reference=source_reference,
            modality=modality,
            embedding_model=resolved_embedding_model,
            embedding_vector=json.dumps(vector),
            summary_text=content[:1000],
            drive_file_id=drive_file_id,
            drive_file_url=drive_file_url,
            drive_path=drive_path,
            metadata_json=json.dumps(metadata or {}),
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        synced = self._sync_to_vector_store(db, memory=memory, vector=vector)
        return memory, synced

    def search_similar(
        self,
        db: Session,
        patient_id: int,
        query_text: str,
        modality: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        query_vector = self._build_placeholder_embedding(query_text, modality or "text")
        vector_results = self._search_vector_store(
            db=db,
            patient_id=patient_id,
            query_vector=query_vector,
            limit=limit,
        )
        if vector_results:
            return vector_results
        statement = select(MedicalMemory).where(MedicalMemory.patient_id == patient_id)
        if modality is not None:
            statement = statement.where(MedicalMemory.modality == modality)
        records = db.scalars(statement).all()

        ranked: list[dict] = []
        for record in records:
            vector = json.loads(record.embedding_vector)
            similarity = self._cosine_similarity(query_vector, vector)
            ranked.append(
                {
                    "memory_id": record.id,
                    "source_type": record.source_type,
                    "source_reference": record.source_reference,
                    "modality": record.modality,
                    "embedding_model": record.embedding_model,
                    "summary_text": record.summary_text,
                    "drive_file_id": record.drive_file_id,
                    "drive_file_url": record.drive_file_url,
                    "drive_path": record.drive_path,
                    "metadata": json.loads(record.metadata_json or "{}"),
                    "similarity": round(similarity, 4),
                }
            )
        ranked.sort(key=lambda item: item["similarity"], reverse=True)
        return ranked[:limit]

    def build_content_from_inputs(self, query_text: str | None = None, file_path: str | None = None) -> tuple[str, str]:
        if file_path:
            path = Path(file_path)
            modality = "image" if self._is_image_file(file_path) else "document"
            content = f"{query_text or ''} {path.name} {path.suffix}".strip()
            return content, modality
        return (query_text or "").strip(), "text"

    def _embedding_model_for_modality(self, modality: str) -> str:
        if modality in {"image", "document"}:
            return self.settings.adk_model
        return f"{self.settings.adk_model}:text"

    def _build_placeholder_embedding(self, content: str, modality: str) -> list[float]:
        seed = f"{modality}:{content}".encode("utf-8")
        digest = hashlib.sha256(seed).digest()
        values: list[float] = []
        while len(values) < self.dimensions:
            digest = hashlib.sha256(digest).digest()
            for index in range(0, len(digest), 2):
                chunk = digest[index : index + 2]
                raw = int.from_bytes(chunk, byteorder="big", signed=False)
                values.append((raw / 65535.0) * 2 - 1)
                if len(values) >= self.dimensions:
                    break
        return values

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def _is_image_file(self, file_path: str) -> bool:
        lowered = file_path.lower()
        return lowered.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".heic"))

    def _sync_to_vector_store(self, db: Session, memory: MedicalMemory, vector: list[float]) -> bool:
        if db.bind is None or db.bind.dialect.name != "postgresql":
            return False
        if len(vector) != self.settings.medical_embedding_dimensions:
            return False

        vector_literal = "[" + ",".join(f"{item:.8f}" for item in vector) + "]"
        try:
            db.execute(
                text(
                    f"""
                    INSERT INTO {self.settings.medical_vector_table_name}
                    (memory_id, patient_id, source_type, modality, embedding_model, embedding, summary_text)
                    VALUES
                    (:memory_id, :patient_id, :source_type, :modality, :embedding_model, CAST(:embedding AS vector), :summary_text)
                    ON CONFLICT (memory_id) DO UPDATE SET
                        patient_id = EXCLUDED.patient_id,
                        source_type = EXCLUDED.source_type,
                        modality = EXCLUDED.modality,
                        embedding_model = EXCLUDED.embedding_model,
                        embedding = EXCLUDED.embedding,
                        summary_text = EXCLUDED.summary_text
                    """
                ),
                {
                    "memory_id": memory.id,
                    "patient_id": memory.patient_id,
                    "source_type": memory.source_type,
                    "modality": memory.modality,
                    "embedding_model": memory.embedding_model,
                    "embedding": vector_literal,
                    "summary_text": memory.summary_text,
                },
            )
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    def _search_vector_store(
        self,
        db: Session,
        patient_id: int,
        query_vector: list[float],
        limit: int,
    ) -> list[dict]:
        if db.bind is None or db.bind.dialect.name != "postgresql":
            return []
        if len(query_vector) != self.settings.medical_embedding_dimensions:
            return []

        vector_literal = "[" + ",".join(f"{item:.8f}" for item in query_vector) + "]"
        try:
            rows = db.execute(
                text(
                    f"""
                    SELECT
                        m.id AS memory_id,
                        m.source_type,
                        m.source_reference,
                        m.modality,
                        m.embedding_model,
                        m.summary_text,
                        m.drive_file_id,
                        m.drive_file_url,
                        m.metadata_json,
                        1 - (v.embedding <=> CAST(:query_vector AS vector)) AS similarity
                    FROM {self.settings.medical_vector_table_name} v
                    JOIN medical_memories m ON m.id = v.memory_id
                    WHERE v.patient_id = :patient_id
                    ORDER BY v.embedding <=> CAST(:query_vector AS vector)
                    LIMIT :limit
                    """
                ),
                {"patient_id": patient_id, "query_vector": vector_literal, "limit": limit},
            ).mappings().all()
            return [
                {
                    "memory_id": row["memory_id"],
                    "source_type": row["source_type"],
                    "source_reference": row["source_reference"],
                    "modality": row["modality"],
                    "embedding_model": row["embedding_model"],
                    "summary_text": row["summary_text"],
                    "drive_file_id": row["drive_file_id"],
                    "drive_file_url": row["drive_file_url"],
                    "metadata": json.loads(row["metadata_json"] or "{}"),
                    "similarity": round(float(row["similarity"]), 4),
                }
                for row in rows
            ]
        except Exception:
            return []
