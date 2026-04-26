#!/usr/bin/env python3
# Script para instalar dependencias necesarias para la carga de datos Excel

import subprocess
import sys

def instalar_dependencias():
    print("🔧 INSTALANDO DEPENDENCIAS PARA CARGA EXCEL")
    print("=" * 45)
    
    dependencias = [
        'pandas',
        'openpyxl',
        'xlrd'
    ]
    
    for dep in dependencias:
        print(f"📦 Instalando {dep}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"   ✅ {dep} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error al instalar {dep}: {e}")
    
    print("\n✅ Dependencias instaladas!")
    print("🚀 Ahora puedes ejecutar: python cargar_datos_excel.py")

if __name__ == '__main__':
    instalar_dependencias()
