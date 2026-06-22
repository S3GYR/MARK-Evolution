#!/usr/bin/env python3
"""
MARK XLVI - Test de validation de la migration LiteLLM
Test du provider unique LiteLLM Gateway
"""

import asyncio
import time

from jarvis.llm.client import LLMClient
from jarvis.llm.litellm_provider import get_litellm_provider


async def test_litellm_connection():
    """Test la connexion au gateway LiteLLM."""
    print("MARK XLVI - Test Migration LiteLLM")
    print("=" * 40)
    
    # Test du provider LiteLLM
    print("\n1. Test Provider LiteLLM...")
    provider = get_litellm_provider()
    
    try:
        # Test de connexion
        result = await provider.test_connection()
        
        if result["success"]:
            print(f"   CONNEXION OK")
            print(f"   Modele: {result['model']}")
            print(f"   Temps: {result['response_time']:.2f}s")
            print(f"   Reponse: {result['response']}")
        else:
            print(f"   CONNEXION ÉCHEC: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   ERREUR PROVIDER: {e}")
        return False
    
    # Test du client LLM
    print("\n2. Test Client LLM...")
    client = LLMClient()
    
    try:
        start_time = time.time()
        
        response = await client.chat(
            messages=[{"role": "user", "content": "Reponds uniquement: LITELLM OK"}],
            model="qwen-fast"
        )
        
        response_time = time.time() - start_time
        
        print(f"   CLIENT OK")
        print(f"   Reponse: {response.content}")
        print(f"   Modele: {response.model}")
        print(f"   Temps: {response_time:.2f}s")
        
        if response.usage:
            print(f"   Usage: {response.usage}")
        
    except Exception as e:
        print(f"   ERREUR CLIENT: {e}")
        return False
    
    # Test avec différents modèles
    models_to_test = ["qwen-fast", "deepseek-chat", "nemotron"]
    
    print("\n3. Test Multi-Modèles...")
    for model in models_to_test:
        try:
            start_time = time.time()
            
            response = await client.chat(
                messages=[{"role": "user", "content": f"Reponds uniquement: {model.upper()} OK"}],
                model=model,
                max_tokens=20
            )
            
            response_time = time.time() - start_time
            
            print(f"   {model}: OK ({response_time:.2f}s) - {response.content}")
            
        except Exception as e:
            print(f"   {model}: ÉCHEC - {e}")
    
    # Afficher les statistiques
    print("\n4. Statistiques LiteLLM...")
    stats = provider.get_stats()
    
    print(f"   Requêtes totales: {stats['total_requests']}")
    print(f"   Succès: {stats['successful_requests']}")
    print(f"   Échecs: {stats['failed_requests']}")
    print(f"   Taux succès: {stats['success_rate']:.1f}%")
    print(f"   Temps moyen: {stats['avg_response_time']:.2f}s")
    print(f"   URL Gateway: {stats['base_url']}")
    print(f"   Modele par défaut: {stats['default_model']}")
    
    if stats.get('last_error'):
        print(f"   Dernière erreur: {stats['last_error']}")
    
    return True


async def test_model_switching():
    """Test le changement de modèle dynamique."""
    print("\n5. Test Changement de Modèle...")
    
    client = LLMClient()
    
    # Test avec modèle spécifique
    try:
        response1 = await client.chat(
            messages=[{"role": "user", "content": "Quel modèle es-tu?"}],
            model="qwen-fast"
        )
        print(f"   qwen-fast: {response1.content[:50]}...")
        
        response2 = await client.chat(
            messages=[{"role": "user", "content": "Quel modèle es-tu?"}],
            model="deepseek-chat"
        )
        print(f"   deepseek-chat: {response2.content[:50]}...")
        
        response3 = await client.chat(
            messages=[{"role": "user", "content": "Quel modèle es-tu?"}],
            model="nemotron"
        )
        print(f"   nemotron: {response3.content[:50]}...")
        
    except Exception as e:
        print(f"   ÉCHEC changement modèle: {e}")


async def main():
    """Fonction principale de test."""
    print("Démarrage des tests de migration LiteLLM...")
    
    try:
        # Test principal
        success = await test_litellm_connection()
        
        if success:
            # Test additionnel
            await test_model_switching()
            
            print(f"\n" + "=" * 40)
            print("MIGRATION LITELLM: SUCCÈS")
            print("MARK XLVI utilise maintenant uniquement LiteLLM Gateway")
            print("=" * 40)
        else:
            print(f"\n" + "=" * 40)
            print("MIGRATION LITELLM: ÉCHEC")
            print("Vérifiez la configuration du gateway LiteLLM")
            print("=" * 40)
            
    except Exception as e:
        print(f"\nERREUR GLOBALE: {e}")
        print("Vérifiez que LiteLLM Gateway est accessible sur http://192.168.1.198:4000")


if __name__ == "__main__":
    asyncio.run(main())
