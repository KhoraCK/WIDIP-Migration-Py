"""
Client pour le RAG Memory (Knowledge Base).

Ce client gère la mémoire à long terme des agents IA:
- Recherche de cas similaires via embeddings vectoriels
- Ajout de nouvelles connaissances extraites des tickets résolus
- Utilise PostgreSQL + pgvector pour le stockage vectoriel
- Utilise Ollama pour la génération d'embeddings
"""

from typing import Any, Optional

import asyncpg
import httpx
import structlog

from ..config import settings

logger = structlog.get_logger(__name__)


class MemoryClient:
    """
    Client pour la base de connaissances RAG.

    Utilise:
    - PostgreSQL avec pgvector pour la recherche vectorielle
    - Ollama avec nomic-embed-text pour les embeddings
    """

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_pool(self) -> asyncpg.Pool:
        """Retourne le pool de connexions PostgreSQL."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                settings.postgres_dsn,
                min_size=2,
                max_size=10,
            )
            logger.info("memory_pool_created")
        return self._pool

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Retourne le client HTTP pour Ollama."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    async def close(self) -> None:
        """Ferme les connexions."""
        if self._pool:
            await self._pool.close()
            self._pool = None
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    async def _get_embedding(self, text: str) -> list[float]:
        """
        Génère un embedding via Ollama.

        Args:
            text: Texte à encoder

        Returns:
            Vecteur d'embedding
        """
        try:
            response = await self.http_client.post(
                f"{settings.ollama_url}/api/embeddings",
                json={
                    "model": settings.ollama_embed_model,
                    "prompt": text,
                },
            )

            if not response.is_success:
                raise Exception(f"Ollama error: {response.status_code}")

            data = response.json()
            return data.get("embedding", [])

        except Exception as e:
            logger.exception("embedding_error", error=str(e))
            raise

    async def search_similar_cases(
        self,
        query: str,
        limit: int = 3,
        min_similarity: float = 0.6,
    ) -> dict[str, Any]:
        """
        Recherche des cas similaires dans la base de connaissances.

        Args:
            query: Description du problème à rechercher
            limit: Nombre max de résultats
            min_similarity: Seuil de similarité minimum (0-1)

        Returns:
            Liste des cas similaires avec leur score
        """
        logger.info("memory_search", query=query[:100], limit=limit)

        try:
            # Générer l'embedding de la requête
            query_embedding = await self._get_embedding(query)

            if not query_embedding:
                return {
                    "knowledge_found": False,
                    "message": "Impossible de générer l'embedding",
                }

            # Recherche vectorielle dans PostgreSQL
            pool = await self._get_pool()

            # Convertir l'embedding en string pour pgvector
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            sql = """
                SELECT
                    ticket_id,
                    problem_summary,
                    solution_summary,
                    quality_score,
                    1 - (embedding <=> $1::vector) as similarity
                FROM widip_knowledge_base
                WHERE 1 - (embedding <=> $1::vector) > $2
                    AND quality_score >= 0.4  -- Filtrer les solutions de faible qualité
                ORDER BY similarity DESC
                LIMIT $3
            """

            rows = await pool.fetch(sql, embedding_str, min_similarity, limit)

            if not rows:
                return {
                    "knowledge_found": False,
                    "message": "Aucun cas similaire trouvé dans la mémoire.",
                }

            cases = [
                {
                    "ticket": row["ticket_id"],
                    "problem": row["problem_summary"],
                    "solution": row["solution_summary"],
                    "similarity": f"{row['similarity'] * 100:.0f}%",
                    "quality": f"{row['quality_score']:.2f}",
                }
                for row in rows
            ]

            logger.info("memory_search_results", count=len(cases))

            return {
                "knowledge_found": True,
                "count": len(cases),
                "cases": cases,
            }

        except Exception as e:
            logger.exception("memory_search_error", error=str(e))
            return {
                "knowledge_found": False,
                "error": str(e),
            }

    async def add_knowledge(
        self,
        ticket_id: str,
        problem_summary: str,
        solution_summary: str,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        quality_score: float = 0.0,
    ) -> dict[str, Any]:
        """
        Ajoute une nouvelle connaissance à la base (ticket résolu).

        Args:
            ticket_id: ID du ticket source
            problem_summary: Résumé du problème
            solution_summary: Résumé de la solution
            category: Catégorie (optionnel)
            tags: Tags pour faciliter la recherche
            quality_score: Score de qualité 0.0-1.0 (défaut: 0.0)

        Returns:
            Résultat de l'ajout
        """
        logger.info("memory_add", ticket_id=ticket_id)

        try:
            # Générer l'embedding du problème + solution
            text_to_embed = f"{problem_summary}\n\n{solution_summary}"
            embedding = await self._get_embedding(text_to_embed)

            if not embedding:
                return {
                    "success": False,
                    "error": "Impossible de générer l'embedding",
                }

            pool = await self._get_pool()

            # Convertir l'embedding en string pour pgvector
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

            # Insérer ou mettre à jour
            sql = """
                INSERT INTO widip_knowledge_base
                    (ticket_id, problem_summary, solution_summary, category, tags, embedding, quality_score, created_at)
                VALUES ($1, $2, $3, $4, $5, $6::vector, $7, NOW())
                ON CONFLICT (ticket_id)
                DO UPDATE SET
                    problem_summary = EXCLUDED.problem_summary,
                    solution_summary = EXCLUDED.solution_summary,
                    category = EXCLUDED.category,
                    tags = EXCLUDED.tags,
                    embedding = EXCLUDED.embedding,
                    quality_score = EXCLUDED.quality_score,
                    updated_at = NOW()
                RETURNING id
            """

            row = await pool.fetchrow(
                sql,
                ticket_id,
                problem_summary,
                solution_summary,
                category,
                tags or [],
                embedding_str,
                quality_score,
            )

            logger.info("memory_added", ticket_id=ticket_id, id=row["id"])

            return {
                "success": True,
                "ticket_id": ticket_id,
                "id": row["id"],
                "message": "Connaissance ajoutée à la base",
            }

        except Exception as e:
            logger.exception("memory_add_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
            }

    async def get_stats(self) -> dict[str, Any]:
        """Retourne les statistiques de la base de connaissances."""
        try:
            pool = await self._get_pool()

            stats_sql = """
                SELECT
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT category) as categories,
                    MIN(created_at) as oldest_entry,
                    MAX(created_at) as newest_entry
                FROM widip_knowledge_base
            """

            row = await pool.fetchrow(stats_sql)

            return {
                "success": True,
                "total_entries": row["total_entries"],
                "categories": row["categories"],
                "oldest_entry": str(row["oldest_entry"]) if row["oldest_entry"] else None,
                "newest_entry": str(row["newest_entry"]) if row["newest_entry"] else None,
            }

        except Exception as e:
            logger.exception("memory_stats_error", error=str(e))
            return {"success": False, "error": str(e)}


# Instance singleton
memory_client = MemoryClient()
