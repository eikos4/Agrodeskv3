#!/usr/bin/env python3
# Script completo para cargar datos desde Excel a la base de datos AgroDESK
# Carga: Administradores, Técnicos, Huertos, Bodegas y ActivityTypes

import pandas as pd
import sys
import os
from werkzeug.security import generate_password_hash

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import User, Empresa, Huerto, Bodega, ActivityType

def cargar_datos_excel():
    app = create_app()
    
    with app.app_context():
        print("🌿 AGRODESK - CARGA DE DATOS DESDE EXCEL")
        print("=" * 50)
        
        # Verificar si el archivo Excel existe
        excel_file = "PREPARACION AGRODESK.xlsx"
        if not os.path.exists(excel_file):
            print(f"❌ No se encontró el archivo: {excel_file}")
            print("   Asegúrate de que el archivo esté en el mismo directorio")
            return
        
        try:
            # Cargar el archivo Excel
            print(f"📊 Cargando archivo: {excel_file}")
            xls = pd.ExcelFile(excel_file)
            print(f"   Hojas encontradas: {xls.sheet_names}")
            
            # 1. Cargar ActivityTypes primero
            print("\n🎨 === CARGANDO ACTIVITY TYPES ===")
            if 'ActivityTypes' in xls.sheet_names:
                df_activity = pd.read_excel(excel_file, sheet_name='ActivityTypes')
                print(f"   Encontrados {len(df_activity)} activity types")
                
                for index, row in df_activity.iterrows():
                    key = str(row['key']).strip()
                    nombre = str(row['nombre']).strip()
                    color = str(row['color']).strip()
                    fill_color = str(row['fill_color']).strip()
                    icon = str(row['icon']).strip()
                    
                    # Verificar si ya existe
                    existente = ActivityType.query.filter_by(key=key).first()
                    if existente:
                        print(f"   ⚠️  ActivityType ya existe: {nombre}")
                        continue
                    
                    # Crear nuevo ActivityType
                    new_activity = ActivityType(
                        key=key,
                        nombre=nombre,
                        color=color,
                        fill_color=fill_color,
                        icon=icon
                    )
                    db.session.add(new_activity)
                    print(f"   ✅ ActivityType creado: {nombre}")
                
                db.session.commit()
                print("   ✅ ActivityTypes cargados exitosamente")
            else:
                print("   ⚠️  No se encontró la hoja 'ActivityTypes'")
            
            # 2. Cargar Empresas
            print("\n🏢 === CARGANDO EMPRESAS ===")
            if 'Empresas' in xls.sheet_names:
                df_empresas = pd.read_excel(excel_file, sheet_name='Empresas')
                print(f"   Encontradas {len(df_empresas)} empresas")
                
                for index, row in df_empresas.iterrows():
                    nombre = str(row['nombre']).strip()
                    slug = str(row['slug']).strip()
                    
                    # Verificar si ya existe
                    existente = Empresa.query.filter_by(slug=slug).first()
                    if existente:
                        print(f"   ⚠️  Empresa ya existe: {nombre}")
                        continue
                    
                    # Crear nueva empresa
                    new_empresa = Empresa(
                        nombre=nombre,
                        slug=slug
                    )
                    db.session.add(new_empresa)
                    print(f"   ✅ Empresa creada: {nombre}")
                
                db.session.commit()
                print("   ✅ Empresas cargadas exitosamente")
            else:
                print("   ⚠️  No se encontró la hoja 'Empresas'")
            
            # Obtener empresa CONSULTORA CHS
            empresa_chs = Empresa.query.filter_by(slug='consultora-chs').first()
            if not empresa_chs:
                print("❌ No se encontró la empresa CONSULTORA CHS")
                return
            
            print(f"\n🏢 Empresa seleccionada: {empresa_chs.nombre} (ID: {empresa_chs.id})")
            
            # 3. Cargar Administradores
            print("\n👔 === CARGANDO ADMINISTRADORES ===")
            if 'Administradores' in xls.sheet_names:
                df_admins = pd.read_excel(excel_file, sheet_name='Administradores')
                print(f"   Encontrados {len(df_admins)} administradores")
                
                for index, row in df_admins.iterrows():
                    name = str(row['name']).strip()
                    email = str(row['email']).strip()
                    password = str(row['password']).strip()
                    role = str(row['role']).strip()
                    
                    # Verificar si ya existe
                    existente = User.query.filter_by(email=email).first()
                    if existente:
                        print(f"   ⚠️  Admin ya existe: {name}")
                        continue
                    
                    # Crear nuevo administrador
                    new_admin = User(
                        name=name,
                        email=email,
                        password=generate_password_hash(password),
                        role=role,
                        empresa_id=empresa_chs.id
                    )
                    db.session.add(new_admin)
                    print(f"   ✅ Admin creado: {name} - {email}")
                
                db.session.commit()
                print("   ✅ Administradores cargados exitosamente")
            else:
                print("   ⚠️  No se encontró la hoja 'Administradores'")
            
            # 4. Cargar Técnicos
            print("\n👷 === CARGANDO TÉCNICOS ===")
            if 'Técnicos' in xls.sheet_names:
                df_tecnicos = pd.read_excel(excel_file, sheet_name='Técnicos')
                print(f"   Encontrados {len(df_tecnicos)} técnicos")
                
                # Obtener el primer admin para created_by
                admin_creador = User.query.filter_by(role='admin', empresa_id=empresa_chs.id).first()
                if not admin_creador:
                    print("   ⚠️  No se encontró administrador para created_by")
                    admin_creador_id = None
                else:
                    admin_creador_id = admin_creador.id
                
                for index, row in df_tecnicos.iterrows():
                    name = str(row['name']).strip()
                    email = str(row['email']).strip()
                    password = str(row['password']).strip()
                    role = str(row['role']).strip()
                    telefono = str(row.get('telefono', '')).strip() if pd.notna(row.get('telefono', '')) else None
                    
                    # Verificar si ya existe
                    existente = User.query.filter_by(email=email).first()
                    if existente:
                        print(f"   ⚠️  Técnico ya existe: {name}")
                        continue
                    
                    # Crear nuevo técnico
                    new_tecnico = User(
                        name=name,
                        email=email,
                        password=generate_password_hash(password),
                        role=role,
                        empresa_id=empresa_chs.id,
                        created_by=admin_creador_id,
                        telefono=telefono if telefono else None
                    )
                    db.session.add(new_tecnico)
                    print(f"   ✅ Técnico creado: {name} - {email}")
                
                db.session.commit()
                print("   ✅ Técnicos cargados exitosamente")
            else:
                print("   ⚠️  No se encontró la hoja 'Técnicos'")
            
            # 5. Cargar Huertos
            print("\n🌳 === CARGANDO HUERTOS ===")
            if 'Huertos' in xls.sheet_names:
                df_huertos = pd.read_excel(excel_file, sheet_name='Huertos')
                print(f"   Encontrados {len(df_huertos)} huertos")
                
                for index, row in df_huertos.iterrows():
                    nombre = str(row['nombre']).strip()
                    tipo_cultivo = str(row['tipo_cultivo']).strip()
                    superficie_ha = float(row['superficie_ha']) if pd.notna(row['superficie_ha']) else 0.0
                    ubicacion = str(row.get('ubicacion', '')).strip() if pd.notna(row.get('ubicacion', '')) else None
                    responsable_id = None
                    
                    # Buscar responsable si existe
                    if pd.notna(row.get('responsable_email', '')):
                        responsable_email = str(row['responsable_email']).strip()
                        responsable = User.query.filter_by(email=responsable_email).first()
                        if responsable:
                            responsable_id = responsable.id
                    
                    # Verificar si ya existe
                    existente = Huerto.query.filter_by(nombre=nombre, empresa_id=empresa_chs.id).first()
                    if existente:
                        print(f"   ⚠️  Huerto ya existe: {nombre}")
                        continue
                    
                    # Crear nuevo huerto
                    new_huerto = Huerto(
                        nombre=nombre,
                        tipo_cultivo=tipo_cultivo,
                        superficie_ha=superficie_ha,
                        ubicacion=ubicacion,
                        responsable_id=responsable_id,
                        empresa_id=empresa_chs.id
                    )
                    db.session.add(new_huerto)
                    print(f"   ✅ Huerto creado: {nombre} ({superficie_ha} ha)")
                
                db.session.commit()
                print("   ✅ Huertos cargados exitosamente")
            else:
                print("   ⚠️  No se encontró la hoja 'Huertos'")
            
            # 6. Cargar Bodegas
            print("\n📦 === CARGANDO BODEGAS ===")
            if 'Bodegas' in xls.sheet_names:
                df_bodegas = pd.read_excel(excel_file, sheet_name='Bodegas')
                print(f"   Encontradas {len(df_bodegas)} bodegas")
                
                for index, row in df_bodegas.iterrows():
                    nombre = str(row['nombre']).strip()
                    descripcion = str(row.get('descripcion', '')).strip() if pd.notna(row.get('descripcion', '')) else None
                    capacidad = float(row.get('capacidad', 0)) if pd.notna(row.get('capacidad', 0)) else 0.0
                    
                    # Buscar huerto asociado
                    huerto_id = None
                    if pd.notna(row.get('huerto_nombre', '')):
                        huerto_nombre = str(row['huerto_nombre']).strip()
                        huerto = Huerto.query.filter_by(nombre=huerto_nombre, empresa_id=empresa_chs.id).first()
                        if huerto:
                            huerto_id = huerto.id
                    
                    # Verificar si ya existe
                    existente = Bodega.query.filter_by(nombre=nombre, empresa_id=empresa_chs.id).first()
                    if existente:
                        print(f"   ⚠️  Bodega ya existe: {nombre}")
                        continue
                    
                    # Crear nueva bodega
                    new_bodega = Bodega(
                        nombre=nombre,
                        descripcion=descripcion,
                        capacidad=capacidad,
                        huerto_id=huerto_id,
                        empresa_id=empresa_chs.id
                    )
                    db.session.add(new_bodega)
                    print(f"   ✅ Bodega creada: {nombre}")
                
                db.session.commit()
                print("   ✅ Bodegas cargadas exitosamente")
            else:
                print("   ⚠️  No se encontró la hoja 'Bodegas'")
            
            # Mostrar resumen final
            print("\n📊 === RESUMEN FINAL ===")
            print(f"🏢 Empresa: {empresa_chs.nombre}")
            print(f"👔 Administradores: {User.query.filter_by(role='admin', empresa_id=empresa_chs.id).count()}")
            print(f"👷 Técnicos: {User.query.filter_by(role='tecnico', empresa_id=empresa_chs.id).count()}")
            print(f"🌳 Huertos: {Huerto.query.filter_by(empresa_id=empresa_chs.id).count()}")
            print(f"📦 Bodegas: {Bodega.query.filter_by(empresa_id=empresa_chs.id).count()}")
            print(f"🎨 ActivityTypes: {ActivityType.query.count()}")
            
            print("\n✅ DATOS CARGADOS EXITOSAMENTE!")
            print("🚀 Sistema AgroDESK listo para usar")
            
        except Exception as e:
            print(f"\n❌ Error durante la carga: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    cargar_datos_excel()
