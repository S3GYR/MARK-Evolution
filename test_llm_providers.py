#!/usr/bin/env python3
"""
MARK XLVI - Test de validation des providers LLM
Test NVIDIA, DeepSeek et le failover automatique
"""

import asyncio
import os
import time
from typing import Any

from jarvis.llm.client import LLMClient
from jarvis.llm.router import get_router, reset_router
from jarvis.config.settings import get_settings


async def test_provider_specific(client: LLMClient, provider: str, test_message: str) -> dict[str, Any]:
    """Test un provider spécifique."""
    print(f"\n[TEST] Test {provider.upper()}...")
    
    try:
        start_time = time.time()
        
        # Forcer l'utilisation du provider spécifique
        model_map = {
            "nvidia": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
            "deepseek": "deepseek/deepseek-chat", 
            "gemini": "gemini/gemini-2.5-flash"
        }
        
        response = await client.chat(
            messages=[{"role": "user", "content": test_message}],
            model=model_map.get(provider)
        )
        
        response_time = time.time() - start_time
        
        result = {
            "provider": provider,
            "success": True,
            "response": response.content,
            "model": response.model,
            "response_time": response_time,
            "usage": response.usage
        }
        
        print(f"[OK] {provider.upper()} OK")
        print(f"   Réponse: {response.content}")
        print(f"   Modèle: {response.model}")
        print(f"   Temps: {response_time:.2f}s")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] {provider.upper()} ÉCHEC: {e}")
        return {
            "provider": provider,
            "success": False,
            "error": str(e),
            "response_time": 0
        }


async def test_failover(client: LLMClient) -> dict[str, Any]:
    """Test le failover automatique."""
    print(f"\n🔄 Test FAILOVER automatique...")
    
    # Réinitialiser le router
    reset_router()
    router = get_router()
    
    # Simuler l'indisponibilité de NVIDIA et DeepSeek
    router.mark_provider_error("nvidia", "Simulated error")
    router.mark_provider_error("deepseek", "Simulated error")
    
    try:
        start_time = time.time()
        
        response = await client.chat(
            messages=[{"role": "user", "content": "Réponds uniquement: FAILOVER OK"}],
            model="auto"  # Doit utiliser le router automatique
        )
        
        response_time = time.time() - start_time
        
        # Vérifier que c'est Gemini qui a répondu (fallback)
        used_provider = getattr(response, '_used_provider', 'unknown')
        
        result = {
            "success": True,
            "response": response.content,
            "used_provider": used_provider,
            "response_time": response_time,
            "router_stats": router.get_provider_stats()
        }
        
        print(f"✅ FAILOVER OK")
        print(f"   Provider utilisé: {used_provider}")
        print(f"   Réponse: {response.content}")
        print(f"   Temps: {response_time:.2f}s")
        
        return result
        
    except Exception as e:
        print(f"❌ FAILOVER ÉCHEC: {e}")
        return {
            "success": False,
            "error": str(e),
            "router_stats": router.get_provider_stats()
        }


async def test_auto_routing(client: LLMClient) -> dict[str, Any]:
    """Test le routage automatique avec priorité."""
    print(f"\n🤖 Test ROUTAGE AUTOMATIQUE...")
    
    # Réinitialiser le router
    reset_router()
    router = get_router()
    
    try:
        start_time = time.time()
        
        response = await client.chat(
            messages=[{"role": "user", "content": "Quel provider utilises-tu? Réponds avec le nom du provider."}],
            model="auto"
        )
        
        response_time = time.time() - start_time
        used_provider = getattr(response, '_used_provider', 'unknown')
        
        result = {
            "success": True,
            "response": response.content,
            "used_provider": used_provider,
            "response_time": response_time,
            "router_stats": router.get_provider_stats()
        }
        
        print(f"✅ ROUTAGE AUTOMATIQUE OK")
        print(f"   Provider sélectionné: {used_provider}")
        print(f"   Réponse: {response.content}")
        print(f"   Temps: {response_time:.2f}s")
        
        return result
        
    except Exception as e:
        print(f"❌ ROUTAGE AUTOMATIQUE ÉCHEC: {e}")
        return {
            "success": False,
            "error": str(e),
            "router_stats": router.get_provider_stats()
        }


def check_api_keys() -> dict[str, bool]:
    """Vérifie quelles clés API sont disponibles."""
    api_keys = {}
    
    providers = {
        "nvidia": "NVIDIA_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY", 
        "gemini": "GEMINI_API_KEY"
    }
    
    for provider, env_var in providers.items():
        api_keys[provider] = bool(os.getenv(env_var))
        print(f"🔑 {provider.upper()}: {'✅' if api_keys[provider] else '❌'} ({env_var})")
    
    return api_keys


async def main():
    """Fonction principale de test."""
    print("🚀 MARK XLVI - Validation LLM Multi-Providers")
    print("=" * 50)
    
    # Vérifier les clés API
    api_keys = check_api_keys()
    
    if not any(api_keys.values()):
        print("\n❌ AUCUNE CLÉ API TROUVÉE!")
        print("Veuillez configurer au moins une clé API:")
        print("- NVIDIA_API_KEY")
        print("- DEEPSEEK_API_KEY") 
        print("- GEMINI_API_KEY")
        return
    
    # Initialiser le client
    print(f"\n🔧 Initialisation du client LLM...")
    client = LLMClient()
    
    results = {
        "api_keys": api_keys,
        "tests": {}
    }
    
    # Test 1: NVIDIA (si disponible)
    if api_keys.get("nvidia"):
        results["tests"]["nvidia"] = await test_provider_specific(
            client, "nvidia", "Réponds uniquement: NVIDIA OK"
        )
    
    # Test 2: DeepSeek (si disponible)
    if api_keys.get("deepseek"):
        results["tests"]["deepseek"] = await test_provider_specific(
            client, "deepseek", "Réponds uniquement: DEEPSEEK OK"
        )
    
    # Test 3: Gemini (si disponible)
    if api_keys.get("gemini"):
        results["tests"]["gemini"] = await test_provider_specific(
            client, "gemini", "Réponds uniquement: GEMINI OK"
        )
    
    # Test 4: Routage automatique
    if len([k for k, v in api_keys.items() if v]) > 1:
        results["tests"]["auto_routing"] = await test_auto_routing(client)
    
    # Test 5: Failover
    results["tests"]["failover"] = await test_failover(client)
    
    # Résumé
    print(f"\n📊 RÉSUMÉ DES TESTS")
    print("=" * 30)
    
    for test_name, result in results["tests"].items():
        status = "✅ SUCCÈS" if result.get("success") else "❌ ÉCHEC"
        print(f"{test_name.upper()}: {status}")
        
        if result.get("response_time"):
            print(f"   Temps: {result['response_time']:.2f}s")
        if result.get("used_provider"):
            print(f"   Provider: {result['used_provider']}")
    
    # Stats du router
    router = get_router()
    stats = router.get_provider_stats()
    print(f"\n📈 STATISTIQUES ROUTER")
    print("=" * 25)
    for provider, stat in stats.items():
        status = "🟢" if stat["available"] else "🔴"
        avg_time = f"{stat['avg_response_time']:.2f}s" if stat["avg_response_time"] else "N/A"
        print(f"{provider}: {status} | Temps moyen: {avg_time} | Erreurs: {stat['error_count']}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
