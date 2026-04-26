#!/usr/bin/env python3
"""
Migración para agregar el campo telefono a la tabla users
"""

import sqlite3
import os

def add_telefono_column():
    # Ruta a la base de datos
    db_path = 'instance/agrodesk.db'
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return False
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'telefono' in columns:
            print("✅ La columna 'telefono' ya existe en la tabla users")
            return True
        
        # Agregar la columna telefono
        print("📝 Agregando columna 'telefono' a la tabla users...")
        cursor.execute("ALTER TABLE users ADD COLUMN telefono VARCHAR(20)")
        
        # Confirmar cambios
        conn.commit()
        print("✅ Columna 'telefono' agregada exitosamente")
        
        # Verificar la nueva estructura
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\n📋 Nueva estructura de la tabla users:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al agregar columna: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔄 Iniciando migración para agregar campo telefono...")
    success = add_telefono_column()
    
    if success:
        print("\n✅ Migración completada exitosamente")
    else:
        print("\n❌ Falló la migración")
