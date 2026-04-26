#!/usr/bin/env python3
# Script forzado para reiniciar base de datos

import os
import shutil
import time
from app import create_app
from app.extensions import db
from app.models import Empresa, User
from werkzeug.security import generate_password_hash

def force_reset():
    """Reinicio forzado de la base de datos"""
    
    print("=== REINICIO FORZADO DE BASE DE DATOS ===\n")
    
    # Ruta de la base de datos
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'agrocloud.db')
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    
    # Intentar eliminar varias veces
    for i in range(3):
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"✅ Base de datos eliminada: {db_path}")
                break
        except Exception as e:
            print(f"Intento {i+1}: {e}")
            if i < 2:
                time.sleep(1)
    
    # Eliminar carpeta instance
    if os.path.exists(instance_path):
        try:
            shutil.rmtree(instance_path)
            print(f"✅ Carpeta instance eliminada")
        except Exception as e:
            print(f"❌ Error eliminando instance: {e}")
    
    print("\n=== CREANDO NUEVA BASE DE DATOS ===\n")
    
    # Crear aplicación
    app = create_app()
    
    with app.app_context():
        try:
            # Importar todos los modelos para asegurar que se registren
            from app import models
            
            # Crear todas las tablas
            db.create_all()
            print("✅ Tablas creadas exitosamente")
            
            # Verificar que la tabla empresas existe
            result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='empresas'"))
            if result.fetchone():
                print("✅ Tabla 'empresas' verificada")
            else:
                print("❌ Tabla 'empresas' no encontrada")
                return False
            
            # Crear empresa CONSULTORA CHS
            empresa_chs = Empresa(
                nombre='CONSULTORA CHS',
                slug='consultora-chs'
            )
            
            db.session.add(empresa_chs)
            db.session.commit()
            print(f"✅ Empresa creada: {empresa_chs.nombre} (ID: {empresa_chs.id})")
            
            # Crear administrador principal
            admin_principal = User(
                name='Administrador Principal',
                email='admin@chs.cl',
                password=generate_password_hash('admin123'),
                role='admin',
                empresa_id=empresa_chs.id
            )
            
            db.session.add(admin_principal)
            db.session.commit()
            print(f"✅ Admin principal creado: {admin_principal.name} - {admin_principal.email}")
            
            # Crear administradores adicionales
            admins_data = [
                {
                    'name': 'Guido Castilla Mora',
                    'email': 'g.castilla@agrodesk.cl',
                    'password': 'Guido123',
                    'role': 'admin'
                },
                {
                    'name': 'Evelyn',
                    'email': 'evelyn@agrodesk.cl',
                    'password': 'Evelyn',
                    'role': 'admin'
                },
                {
                    'name': 'Carlos Henríquez',
                    'email': 'carlos.henriquez@chs.cl',
                    'password': 'temp123',
                    'role': 'admin'
                },
                {
                    'name': 'Manuel Vergara',
                    'email': 'manuel.vergara@chs.cl', 
                    'password': 'temp123',
                    'role': 'admin'
                },
                {
                    'name': 'Marcos Alegría',
                    'email': 'marcos.alegria@chs.cl',
                    'password': 'temp123', 
                    'role': 'admin'
                }
            ]
            
            for admin_data in admins_data:
                nuevo_admin = User(
                    name=admin_data['name'],
                    email=admin_data['email'],
                    password=generate_password_hash(admin_data['password']),
                    role=admin_data['role'],
                    empresa_id=empresa_chs.id
                )
                db.session.add(nuevo_admin)
                print(f"✅ Administrador creado: {admin_data['name']} - {admin_data['email']}")
            
            db.session.commit()
            
            print("\n=== BASE DE DATOS REINICIADA EXITOSAMENTE ===")
            print(f"📍 Ubicación: {db_path}")
            print("\n=== CREDENCIALES DE ACCESO ===")
            print(f"• Admin Principal: admin@chs.cl / Password: admin123")
            print(f"• Guido Castilla Mora: g.castilla@agrodesk.cl / Password: Guido123")
            print(f"• Evelyn: evelyn@agrodesk.cl / Password: Evelyn")
            print(f"• Carlos Henríquez: carlos.henriquez@chs.cl / Password: temp123")
            print(f"• Manuel Vergara: manuel.vergara@chs.cl / Password: temp123")
            print(f"• Marcos Alegría: marcos.alegria@chs.cl / Password: temp123")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al crear base de datos: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    if force_reset():
        print("\n🚀 AgroDesk está listo para usar como nuevo!")
    else:
        print("\n❌ Hubo errores durante el proceso")
