#!/usr/bin/env python3
# Script para crear 4 perfiles de técnicos

from app import create_app
from app.extensions import db
from app.models import User, Empresa
from werkzeug.security import generate_password_hash

def create_tecnicos():
    app = create_app()
    with app.app_context():
        # Obtener empresa CONSULTORA CHS
        empresa_chs = Empresa.query.filter_by(slug='consultora-chs').first()
        
        if empresa_chs:
            print(f'Empresa encontrada: {empresa_chs.nombre} (ID: {empresa_chs.id})')
            
            # Crear 4 perfiles de técnicos
            tecnicos_data = [
                {
                    'name': 'Juan Pérez',
                    'email': 'juan.perez@chs.cl',
                    'password': 'temp123',
                    'role': 'tecnico'
                },
                {
                    'name': 'María González',
                    'email': 'maria.gonzalez@chs.cl', 
                    'password': 'temp123',
                    'role': 'tecnico'
                },
                {
                    'name': 'Carlos Rodríguez',
                    'email': 'carlos.rodriguez@chs.cl',
                    'password': 'temp123', 
                    'role': 'tecnico'
                },
                {
                    'name': 'Ana Silva',
                    'email': 'ana.silva@chs.cl',
                    'password': 'temp123',
                    'role': 'tecnico'
                }
            ]
            
            print('\n=== CREANDO 4 PERFILES DE TÉCNICOS ===')
            for i, tecnico_data in enumerate(tecnicos_data, 1):
                # Verificar si ya existe
                existente = User.query.filter_by(email=tecnico_data['email']).first()
                if existente:
                    print(f'{i}. ❌ Usuario ya existe: {tecnico_data["email"]}')
                    continue
                    
                nuevo_tecnico = User(
                    name=tecnico_data['name'],
                    email=tecnico_data['email'],
                    password=generate_password_hash(tecnico_data['password']),
                    role=tecnico_data['role'],
                    empresa_id=empresa_chs.id
                )
                
                db.session.add(nuevo_tecnico)
                print(f'{i}. ✅ Técnico creado: {tecnico_data["name"]} - {tecnico_data["email"]}')
            
            try:
                db.session.commit()
                print('\n✅ Todos los técnicos han sido creados exitosamente!')
                print('\n=== CREDENCIALES DE ACCESO ===')
                for tecnico in tecnicos_data:
                    print(f'• {tecnico["name"]}: {tecnico["email"]} / Password: temp123')
            except Exception as e:
                db.session.rollback()
                print(f'\n❌ Error al crear técnicos: {e}')
        else:
            print('❌ No se encontró la empresa CONSULTORA CHS')

if __name__ == '__main__':
    create_tecnicos()
