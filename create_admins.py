#!/usr/bin/env python3
# Script para crear administradores adicionales

from app import create_app
from app.extensions import db
from app.models import User, Empresa
from werkzeug.security import generate_password_hash

def create_admins():
    app = create_app()
    with app.app_context():
        # Obtener empresa CONSULTORA CHS
        empresa_chs = Empresa.query.filter_by(slug='consultora-chs').first()
        
        if empresa_chs:
            print(f'Empresa encontrada: {empresa_chs.nombre} (ID: {empresa_chs.id})')
            
            # Crear 3 perfiles de administradores adicionales
            admins_data = [
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
            
            print('\n=== CREANDO 3 PERFILES DE ADMINISTRADORES ===')
            for i, admin_data in enumerate(admins_data, 1):
                # Verificar si ya existe
                existente = User.query.filter_by(email=admin_data['email']).first()
                if existente:
                    print(f'{i}. ❌ Usuario ya existe: {admin_data["email"]}')
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
                print('\n✅ Todos los administradores han sido creados exitosamente!')
                print('\n=== CREDENCIALES DE ACCESO ===')
                for admin in admins_data:
                    print(f'• {admin["name"]}: {admin["email"]} / Password: temp123')
                    
                # Mostrar todos los admins de la empresa
                print('\n=== TODOS LOS ADMINISTRADORES DE CONSULTORA CHS ===')
                todos_admins = User.query.filter_by(role='admin', empresa_id=empresa_chs.id).all()
                for i, admin in enumerate(todos_admins, 1):
                    print(f'{i}. {admin.name} - {admin.email}')
                    
            except Exception as e:
                db.session.rollback()
                print(f'\n❌ Error al crear administradores: {e}')
        else:
            print('❌ No se encontró la empresa CONSULTORA CHS')

if __name__ == '__main__':
    create_admins()
