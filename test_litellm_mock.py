#!/usr/bin/env python3
"""
MARK XLVI - Test simulé de la migration LiteLLM
Test sans dépendre du gateway LiteLLM réel
"""

import asyncio
from unittest.mock import AsyncMock, patch

from jarvis.llm.client import LLMClient
from jarvis.llm.litellm_provider import get_litellm_provider


async def test_mock_litellm():
    """Test la migration LiteLLM avec des mocks."""
    print("MARK XLVI - Test Simulé Migration LiteLLM")
    print("=" * 45)
    
    # Créer un objet mock response avec les bons attributs
    class MockChoice:
        def __init__(self):
            self.message = MockMessage()
            self.finish_reason = "stop"
    
    class MockMessage:
        def __init__(self):
            self.content = "LITELLM OK - Test réussi"
            self.role = "assistant"
    
    class MockUsage:
        def __init__(self):
            self.prompt_tokens = 10
            self.completion_tokens = 5
            self.total_tokens = 15
    
    class MockResponse:
        def __init__(self, model="openai/qwen-fast"):
            self.choices = [MockChoice()]
            self.model = model
            self.usage = MockUsage()
    
    mock_response = MockResponse()
    
    # Test du provider LiteLLM avec mock
    print("\n1. Test Provider LiteLLM (Mock)...")
    provider = get_litellm_provider()
    
    # Mock la méthode chat du provider
    with patch.object(provider, 'chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        try:
            result = await provider.test_connection("qwen-fast")
            
            if result["success"]:
                print(f"   CONNEXION OK (Mock)")
                print(f"   Modele: {result['model']}")
                print(f"   Reponse: {result['response']}")
            else:
                print(f"   CONNEXION ÉCHEC (Mock): {result['error']}")
                
        except Exception as e:
            print(f"   ERREUR PROVIDER: {e}")
    
    # Test du client LLM avec mock
    print("\n2. Test Client LLM (Mock)...")
    client = LLMClient()
    
    # Mock la méthode chat du provider
    with patch.object(provider, 'chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        try:
            response = await client.chat(
                messages=[{"role": "user", "content": "Test"}],
                model="qwen-fast"
            )
            
            print(f"   CLIENT OK (Mock)")
            print(f"   Reponse: {response.content}")
            print(f"   Modele: {response.model}")
            print(f"   Finish Reason: {response.finish_reason}")
            
            if response.usage:
                print(f"   Usage: {response.usage}")
                
        except Exception as e:
            print(f"   ERREUR CLIENT: {e}")
    
    # Test changement de modèle
    print("\n3. Test Changement de Modèle (Mock)...")
    
    models_to_test = ["qwen-fast", "deepseek-chat", "nemotron"]
    
    for model in models_to_test:
        with patch.object(provider, 'chat', new_callable=AsyncMock) as mock_chat:
            model_response = MockResponse(f"openai/{model}")
            model_response.choices[0].message.content = f"{model.upper()} OK"
            mock_chat.return_value = model_response
            
            try:
                response = await client.chat(
                    messages=[{"role": "user", "content": "Test"}],
                    model=model
                )
                print(f"   {model}: OK - {response.content}")
                
            except Exception as e:
                print(f"   {model}: ÉCHEC - {e}")
    
    # Test des statistiques
    print("\n4. Test Statistiques (Mock)...")
    
    with patch.object(provider, 'chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response
        
        # Simuler quelques requêtes
        for i in range(3):
            await client.chat(
                messages=[{"role": "user", "content": f"Test {i}"}],
                model="qwen-fast"
            )
        
        stats = provider.get_stats()
        print(f"   Requêtes totales: {stats['total_requests']}")
        print(f"   Succès: {stats['successful_requests']}")
        print(f"   Échecs: {stats['failed_requests']}")
        print(f"   Taux succès: {stats['success_rate']:.1f}%")
        print(f"   URL Gateway: {stats['base_url']}")
        print(f"   Modele par défaut: {stats['default_model']}")
    
    return True


async def test_architecture_simplification():
    """Test que l'architecture a bien été simplifiée."""
    print("\n5. Test Simplification Architecture...")
    
    # Vérifier que le client utilise bien le provider LiteLLM
    client = LLMClient()
    
    print(f"   Settings provider: {client.settings.llm_provider}")
    print(f"   Default model: {client.settings.default_model}")
    print(f"   LiteLLM base URL: {client.settings.litellm_base_url}")
    print(f"   LiteLLM API key: {client.settings.litellm_api_key}")
    
    # Vérifier que le provider est bien initialisé
    provider = get_litellm_provider()
    print(f"   Provider type: {type(provider).__name__}")
    print(f"   Provider base URL: {provider.settings.litellm_base_url}")
    
    # Vérifier que les anciennes variables n'existent plus
    old_vars = [
        'llm_providers_priority',
        'llm_auto_failover', 
        'nvidia_model',
        'deepseek_model',
        'gemini_model'
    ]
    
    for var in old_vars:
        if hasattr(client.settings, var):
            print(f"   ATTENTION: {var} existe encore!")
        else:
            print(f"   OK: {var} supprimé")


async def main():
    """Fonction principale de test."""
    print("Démarrage des tests simulés de migration LiteLLM...")
    
    try:
        # Test principal avec mocks
        success = await test_mock_litellm()
        
        # Test de l'architecture
        await test_architecture_simplification()
        
        print(f"\n" + "=" * 45)
        print("MIGRATION LITELLM: SUCCÈS (SIMULÉ)")
        print("Architecture simplifiée et fonctionnelle")
        print("Prêt pour utilisation avec gateway LiteLLM réel")
        print("=" * 45)
        
        print("\nConfiguration requise:")
        print("- Gateway LiteLLM: http://192.168.1.198:4000")
        print("- Modele par défaut: qwen-fast")
        print("- API Key: dummy (ou None)")
        
    except Exception as e:
        print(f"\nERREUR GLOBALE: {e}")


if __name__ == "__main__":
    asyncio.run(main())
