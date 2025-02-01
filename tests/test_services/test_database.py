import pytest
from datetime import datetime
from political_discourse_analyzer.services.database_service import DatabaseService

@pytest.fixture
async def sample_conversation(test_db_service):
    """Crear una conversación de prueba."""
    return await test_db_service.save_conversation(
        thread_id="test_thread_1",
        mode="neutral"
    )

async def test_save_conversation(test_db_service):
    """Probar guardar una conversación."""
    conversation = await test_db_service.save_conversation(
        thread_id="test_thread",
        mode="neutral"
    )
    assert conversation.thread_id == "test_thread"
    assert conversation.mode == "neutral"
    assert isinstance(conversation.created_at, datetime)

async def test_save_interaction(test_db_service, sample_conversation):
    """Probar guardar una interacción."""
    await test_db_service.save_interaction(
        thread_id="test_thread_1",
        query="test query",
        response="test response",
        mode="neutral",
        citations=["citation 1", "citation 2"]
    )
    
    history = await test_db_service.get_conversation_history("test_thread_1")
    assert len(history) == 1
    assert history[0]["query"] == "test query"
    assert history[0]["response"] == "test response"

async def test_get_analytics(test_db_service, sample_conversation):
    """Probar obtener analíticas."""
    analytics = await test_db_service.get_analytics()
    assert "total_conversations" in analytics
    assert "total_interactions" in analytics
    assert "modes_distribution" in analytics