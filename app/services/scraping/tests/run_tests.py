#!/usr/bin/env python3
"""
Script principal para ejecutar todos los tests del paquete de scraping.
"""

import sys
import os

# Agregar el directorio raíz del proyecto al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

# Importar tests directamente
from test_scraping_package import run_all_tests
from test_scraping_specific import test_specific_scraping

def main():
    """Ejecuta todos los tests del paquete."""
    
    print("🚀 EJECUTANDO TODOS LOS TESTS DEL PAQUETE DE SCRAPING")
    print("=" * 70)
    
    # Test 1: Paquete principal
    print("\n🧪 TEST 1: PAQUETE PRINCIPAL")
    print("-" * 40)
    main_success = run_all_tests()
    
    # Test 2: URL específica
    print("\n🧪 TEST 2: URL ESPECÍFICA")
    print("-" * 40)
    specific_success = test_specific_scraping()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("🏁 RESUMEN FINAL DE TODOS LOS TESTS")
    print("=" * 70)
    print(f"📋 Paquete principal: {'✅ EXITOSO' if main_success else '❌ FALLÓ'}")
    print(f"🔗 URL específica: {'✅ EXITOSO' if specific_success else '❌ FALLÓ'}")
    
    if main_success and specific_success:
        print("\n🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("✨ El paquete de scraping está funcionando perfectamente")
        print("🚀 Listo para usar en producción")
    else:
        print("\n⚠️ Algunos tests fallaron. Revisa los errores arriba.")
    
    print("\n🎯 Ejecución de tests completada")
    
    return main_success and specific_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
