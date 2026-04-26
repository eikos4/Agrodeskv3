#!/usr/bin/env python3
# Script para eliminar y recrear la base de datos de AgroDesk

import os
import shutil
from app import create_app
from app.extensions import db
from app.models import Empresa, User
from werkzeug.security import generate_password_hash

def reset_database():
    """Elimina la base de datos existente y la recrea con datos iniciales"""
    
    print("=== INICIANDO LIMPIEZA DE BASE DE DATOS ===\n")
    
    # Ruta de la base de datos
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'agrocloud.db')
    
    # Eliminar base de datos existente
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"✅ Base de datos eliminada: {db_path}")
        except Exception as e:
            print(f"❌ Error al eliminar base de datos: {e}")
            return False
    else:
        print("ℹ️  No se encontró base de datos existente")
    
    # Eliminar carpeta instance si existe para limpieza completa
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if os.path.exists(instance_path):
        try:
            shutil.rmtree(instance_path)
            print(f"✅ Carpeta instance eliminada: {instance_path}")
        except Exception as e:
            print(f"❌ Error al eliminar carpeta instance: {e}")
            return False
    
    print("\n=== CREANDO NUEVA BASE DE DATOS ===\n")
    
    # Crear aplicación y contexto
    app = create_app()
    
    with app.app_context():
        try:
            # Crear todas las tablas
            db.create_all()
            print("✅ Tablas creadas exitosamente")
            
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
                role='adminkodesk',
                empresa_id=empresa_chs.id
            )
            
            db.session.add(admin_principal)
            db.session.commit()
            print(f"✅ Admin principal creado: {admin_principal.name} - {admin_principal.email}")
            
            print("\n=== BASE DE DATOS REINICIADA EXITOSAMENTE ===")
            print(f"📍 Ubicación: {db_path}")
            print("\n=== CREDENCIALES DE ACCESO ===")
            print(f"• Admin Principal: admin@chs.cl / Password: admin123")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al crear base de datos: {e}")
            db.session.rollback()
            return False

def create_additional_admins():
    """Crea los administradores adicionales después del reset"""
    
    print("\n=== CREANDO ADMINISTRADORES ADICIONALES ===\n")
    
    app = create_app()
    with app.app_context():
        # Obtener empresa CONSULTORA CHS
        empresa_chs = Empresa.query.filter_by(slug='consultora-chs').first()
        
        if not empresa_chs:
            print("❌ No se encontró la empresa CONSULTORA CHS")
            return False
        
        # Datos de administradores adicionales
        admins_data = [
            {
                'name': 'Carlos Henríquez',
                'email': 'carlos.henriquez@chs.cl',
                'password': 'Carlos123',
                'role': 'admin'
            },
            {
                'name': 'Manuel Vergara',
                'email': 'manuel.vergara@chs.cl', 
                'password': 'Manuel123',
                'role': 'admin'
            },

            {
                'name': 'Guido Castila',
                'email': 'g.castilla@chs.cl', 
                'password': 'Guido123',
                'role': 'admin'
            },

            {
                'name': 'Evelyn',
                'email': 'evelyn@chs.cl', 
                'password': 'Evelyn123',
                'role': 'admin'
            },
            {
                'name': 'Marcos Alegría',
                'email': 'marcos.alegria@chs.cl',
                'password': 'Marcos123', 
                'role': 'admin'
            }
        ]
        
        for i, admin_data in enumerate(admins_data, 1):
            # Verificar si ya existe
            existente = User.query.filter_by(email=admin_data['email']).first()
            if existente:
                print(f'{i}. ⚠️  Usuario ya existe: {admin_data["email"]}')
                continue
                
            nuevo_admin = User(
                name=admin_data['name'],
                email=admin_data['email'],
                password=generate_password_hash(admin_data['password']),
                role=admin_data['role'],
                empresa_id=empresa_chs.id
            )
            
            db.session.add(nuevo_admin)
            print(f'{i}. ✅ Administrador creado: {admin_data["name"]} - {admin_data["email"]}')
        
        try:
            db.session.commit()
            print('\n✅ Todos los administradores adicionales han sido creados!')
            return True
        except Exception as e:
            db.session.rollback()
            print(f'\n❌ Error al crear administradores adicionales: {e}')
            return False

if __name__ == '__main__':
    # Resetear base de datos
    if reset_database():
        # Crear administradores adicionales
        create_additional_admins()
        
        print("\n=== RESUMEN FINAL ===")
        print("✅ Base de datos eliminada y recreada")
        print("✅ Empresa CONSULTORA CHS creada")
        print("✅ 4 administradores creados (1 principal + 3 adicionales)")
        print("\n🚀 AgroDesk está listo para usar como nuevo!")
    else:
        print("\n❌ Hubo errores durante el proceso de reinicio")
