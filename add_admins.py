#!/usr/bin/env python3
# Script para agregar administradores adicionales sin eliminar la base de datos

from app import create_app
from app.extensions import db
from app.models import Empresa, User
from werkzeug.security import generate_password_hash

def add_additional_admins():
    """Agrega administradores adicionales a la base de datos existente"""
    
    print("=== AGREGANDO ADMINISTRADORES ADICIONALES ===\n")
    
    app = create_app()
    with app.app_context():
        # Obtener empresa CONSULTORA CHS
        empresa_chs = Empresa.query.filter_by(slug='consultora-chs').first()
        
        if not empresa_chs:
            print("❌ No se encontró la empresa CONSULTORA CHS")
            return False
        
        print(f"✅ Empresa encontrada: {empresa_chs.nombre} (ID: {empresa_chs.id})")
        
        # Datos de administradores adicionales
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
            }
        ]
        
        print('\n=== CREANDO ADMINISTRADORES ADICIONALES ===')
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
            print('\n✅ Administradores adicionales creados exitosamente!')
            
            # Mostrar todos los administradores
            print('\n=== TODOS LOS ADMINISTRADORES ===')
            todos_admins = User.query.filter_by(role='admin', empresa_id=empresa_chs.id).all()
            for i, admin in enumerate(todos_admins, 1):
                print(f'{i}. {admin.name} - {admin.email}')
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f'\n❌ Error al crear administradores: {e}')
            return False

if __name__ == '__main__':
    if add_additional_admins():
        print("\n🚀 Administradores agregados exitosamente!")
    else:
        print("\n❌ Hubo errores durante el proceso")
