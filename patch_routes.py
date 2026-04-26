import os

ADMIN_FILE = r'c:\Users\eikos\Desktop\AgroDesk\app\routes\admin.py'
TECNICO_FILE = r'c:\Users\eikos\Desktop\AgroDesk\app\routes\tecnico.py'

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Agregar import de MovimientoInventario
    if "MovimientoInventario" not in content:
        content = content.replace("ActividadHuerto", "ActividadHuerto, MovimientoInventario", 1)

    # Buscar todas las instancias de `form = RegistrarActividadForm()` y agregar populate choices
    choices_code = """
    form = RegistrarActividadForm()
    quimicos_disponibles = Quimico.query.join(Bodega).filter(Bodega.empresa_id == current_user.empresa_id).all()
    form.quimico_id.choices = [(0, "— Sin químico del inventario —")] + [(q.id, f"{q.nombre} (Stock: {q.cantidad_litros})") for q in quimicos_disponibles]
    """
    content = content.replace("form = RegistrarActividadForm()\n", choices_code + "\n")

    # Inyectar el seteo de los campos en las variables "actividad"
    q_fields = """
            actividad.quimico_id = form.quimico_id.data if form.quimico_id.data != 0 else None
            actividad.cantidad_aplicada = form.cantidad_aplicada.data
            
            if actividad.quimico_id and actividad.cantidad_aplicada:
                q = Quimico.query.get(actividad.quimico_id)
                if q and q.cantidad_litros >= actividad.cantidad_aplicada:
                    q.cantidad_litros -= actividad.cantidad_aplicada
                    mov = MovimientoInventario(quimico_id=q.id, tipo="egreso", cantidad=actividad.cantidad_aplicada, usuario_id=current_user.id, empresa_id=current_user.empresa_id)
                    db.session.add(mov) # actividad.id se asociara manualmente o despues del commit, wait! Para enlazarlo:
                    actividad.movimientos = [mov] # No tenemos backref list, asi que lo agrego normal
"""
    # Para el caso que la declaracion de actividad sea `act = ActividadHuerto(...)` en tecnico.py
    q_fields_tecnico = """
            act.quimico_id = form.quimico_id.data if form.quimico_id.data != 0 else None
            act.cantidad_aplicada = form.cantidad_aplicada.data
            db.session.add(act)
            db.session.flush() # Para obtener el ID
            
            if act.quimico_id and act.cantidad_aplicada:
                q = Quimico.query.get(act.quimico_id)
                if q and q.cantidad_litros >= act.cantidad_aplicada:
                    q.cantidad_litros -= act.cantidad_aplicada
                    mov = MovimientoInventario(quimico_id=q.id, tipo="egreso", cantidad=act.cantidad_aplicada, usuario_id=current_user.id, referencia_actividad_id=act.id, empresa_id=current_user.empresa_id)
                    db.session.add(mov)
"""

    q_fields_admin = """
            actividad.quimico_id = form.quimico_id.data if form.quimico_id.data != 0 else None
            actividad.cantidad_aplicada = form.cantidad_aplicada.data
            db.session.add(actividad)
            db.session.flush() # Obtener ID
            
            if actividad.quimico_id and actividad.cantidad_aplicada:
                q = Quimico.query.get(actividad.quimico_id)
                if q and q.cantidad_litros >= actividad.cantidad_aplicada:
                    q.cantidad_litros -= actividad.cantidad_aplicada
                    mov = MovimientoInventario(quimico_id=q.id, tipo="egreso", cantidad=actividad.cantidad_aplicada, usuario_id=current_user.id, referencia_actividad_id=actividad.id, empresa_id=current_user.empresa_id)
                    db.session.add(mov)
            # 
"""

    if 'tecnico.py' in filepath:
        content = content.replace("db.session.add(act)", q_fields_tecnico)
    else:
        content = content.replace("db.session.add(actividad)", q_fields_admin)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

patch_file(ADMIN_FILE)
patch_file(TECNICO_FILE)
print("Archivos parcheados correctamente.")
