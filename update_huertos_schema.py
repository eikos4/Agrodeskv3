#!/usr/bin/env python3
# Script para actualizar el esquema de la tabla huertos con los nuevos campos

from app import create_app
from app.extensions import db

def update_huertos_schema():
    """Actualiza el esquema de la tabla huertos agregando los nuevos campos"""
    
    print("=== ACTUALIZANDO ESQUEMA DE HUERTOS ===\n")
    
    app = create_app()
    with app.app_context():
        try:
            # Conexión directa a la base de datos para agregar columnas
            connection = db.engine.connect()
            
            # Lista de columnas a agregar
            nuevas_columnas = [
                ("propietario", "VARCHAR(120)"),
                ("rut", "VARCHAR(20)"),
                ("codigo_productor", "VARCHAR(50)"),
                ("localidad", "VARCHAR(100)"),
                ("comuna", "VARCHAR(100)"),
                ("provincia", "VARCHAR(100)"),
                ("region", "VARCHAR(100)"),
                ("distrito_agroclimatico", "VARCHAR(100)"),
                ("telefono", "VARCHAR(20)"),
                ("administrador", "VARCHAR(120)"),
                ("encargado_huerto", "VARCHAR(120)"),
                ("direccion", "VARCHAR(250)"),
                ("empresas", "TEXT"),
                ("exportadoras", "TEXT")
            ]
            
            for columna, tipo in nuevas_columnas:
                try:
                    # Verificar si la columna ya existe
                    result = connection.execute(db.text(f"PRAGMA table_info(huertos)"))
                    columnas_existentes = [row[1] for row in result.fetchall()]
                    
                    if columna not in columnas_existentes:
                        # Agregar la columna
                        sql = f"ALTER TABLE huertos ADD COLUMN {columna} {tipo}"
                        connection.execute(db.text(sql))
                        print(f"✅ Columna agregada: {columna}")
                    else:
                        print(f"⚠️  Columna ya existe: {columna}")
                        
                except Exception as e:
                    print(f"❌ Error agregando columna {columna}: {e}")
            
            connection.commit()
            connection.close()
            
            print("\n✅ Esquema de huertos actualizado exitosamente!")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando esquema: {e}")
            return False

if __name__ == '__main__':
    if update_huertos_schema():
        print("\n🚀 La tabla huertos ahora incluye los campos de identificación del predio!")
    else:
        print("\n❌ Hubo errores durante la actualización")
