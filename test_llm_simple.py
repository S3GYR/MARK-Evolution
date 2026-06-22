#!/usr/bin/env python3
"""
MARK XLVI - Test simple de validation des providers LLM
"""

import asyncio
import os
import time

from jarvis.llm.client import LLMClient
from jarvis.llm.router import get_router, reset_router


async def test_basic_routing():
    """Test basique du routage LLM."""
    print("MARK XLVI - Test LLM Multi-Providers")
    print("=" * 40)
    
    # Vérifier les clés API
    print("Verification des cles API:")
    providers = {
        "nvidia": "NVIDIA_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY", 
        "gemini": "GEMINI_API_KEY"
    }
    
    available_providers = []
    for provider, env_var in providers.items():
        has_key = bool(os.getenv(env_var))
        status = "OK" if has_key else "MANQUANT"
        print(f"  {provider.upper()}: {status}")
        if has_key:
            available_providers.append(provider)
    
    if not available_providers:
        print("\nERREUR: Aucune cle API configuree!")
        return
    
    print(f"\nProviders disponibles: {', '.join(available_providers)}")
    
    # Initialiser le client
    print("\nInitialisation du client LLM...")
    client = LLMClient()
    
    # Test avec le meilleur provider disponible
    router = get_router()
    best_provider = router.get_best_provider()
    
    if best_provider:
        print(f"\nTest avec provider: {best_provider}")
        try:
            start_time = time.time()
            
            response = await client.chat(
                messages=[{"role": "user", "content": "Reponds uniquement: TEST OK"}],
                model="auto"
            )
            
            response_time = time.time() - start_time
            
            print(f"SUCCES!")
            print(f"  Reponse: {response.content}")
            print(f"  Modele: {response.model}")
            print(f"  Temps: {response_time:.2f}s")
            
            # Afficher les stats du router
            stats = router.get_provider_stats()
            print(f"\nStatistiques router:")
            for provider, stat in stats.items():
                status = "DISPONIBLE" if stat["available"] else "INDISPONIBLE"
                print(f"  {provider}: {status}")
            
        except Exception as e:
            print(f"ERREUR: {e}")
    else:
        print("Aucun provider disponible")


if __name__ == "__main__":
    asyncio.run(test_basic_routing())
