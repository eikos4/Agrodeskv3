#!/usr/bin/env python3
from app import create_app
from app.extensions import db

def update_inventory_schema():
    print("=== ACTUALIZANDO ESQUEMA DE INVENTARIO ===\n")
    app = create_app()
    with app.app_context():
        try:
            connection = db.engine.connect()
            
            # 1. Crear tabla movimientos_inventario si no existe
            sql_create_movimientos = """
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quimico_id INTEGER NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                cantidad FLOAT NOT NULL,
                fecha DATETIME NOT NULL,
                usuario_id INTEGER,
                referencia_actividad_id INTEGER,
                empresa_id INTEGER NOT NULL,
                FOREIGN KEY(quimico_id) REFERENCES quimicos(id),
                FOREIGN KEY(usuario_id) REFERENCES users(id),
                FOREIGN KEY(referencia_actividad_id) REFERENCES actividad_huerto(id),
                FOREIGN KEY(empresa_id) REFERENCES empresas(id)
            )
            """
            connection.execute(db.text(sql_create_movimientos))
            print("Tabla movimientos_inventario verificada/creada.")

            # 2. Agregar columnas a actividad_huerto
            nuevas_columnas = [
                ("quimico_id", "INTEGER"),
                ("cantidad_aplicada", "FLOAT")
            ]
            
            result = connection.execute(db.text(f"PRAGMA table_info(actividad_huerto)"))
            columnas_existentes = [row[1] for row in result.fetchall()]
            
            for columna, tipo in nuevas_columnas:
                if columna not in columnas_existentes:
                    sql = f"ALTER TABLE actividad_huerto ADD COLUMN {columna} {tipo}"
                    connection.execute(db.text(sql))
                    print(f"Columna agregada en actividad_huerto: {columna}")
                else:
                    print(f"Columna ya existe: {columna}")
                    
            connection.commit()
            connection.close()
            print("\nEsquema de inventario actualizado exitosamente!")
            return True
        except Exception as e:
            print(f"Error actualizando esquema: {e}")
            return False

if __name__ == '__main__':
    update_inventory_schema()
