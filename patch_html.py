import os
import glob

html_dir_tecnico = r'c:\Users\eikos\Desktop\AgroDesk\app\templates\tecnico'
html_dir_admin = r'c:\Users\eikos\Desktop\AgroDesk\app\templates\admin'

files_to_patch = []
for file in glob.glob(os.path.join(html_dir_admin, '*registrar*.html')):
    files_to_patch.append(file)
for file in glob.glob(os.path.join(html_dir_tecnico, '*registrar*.html')):
    files_to_patch.append(file)

inventory_html = """
            <!-- Campos de Inventario (Kárdex) -->
            <div class="card bg-light mb-3 border-0">
              <div class="card-body py-2">
                <h6 class="card-subtitle mb-2 text-muted"><i class="bi bi-box-seam"></i> Consumo de Inventario (Opcional)</h6>
                <div class="row g-3">
                  <div class="col-md-8">
                    {{ form.quimico_id.label(class="form-label") }}
                    {{ form.quimico_id(class="form-select") }}
                  </div>
                  <div class="col-md-4">
                    {{ form.cantidad_aplicada.label(class="form-label") }}
                    {{ form.cantidad_aplicada(class="form-control", type="number", step="0.01") }}
                  </div>
                </div>
              </div>
            </div>
"""

for filepath in files_to_patch:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple injection after descripcion
    if "form.descripcion(class=" in content and "form.quimico_id" not in content:
        # Find the end of the div containing descripcion
        # Very hacky string manipulation for WTForms blocks:
        search_str = '{{ form.descripcion'
        idx = content.find(search_str)
        if idx != -1:
            div_end_idx = content.find('</div>', idx)
            if div_end_idx != -1:
                insert_pos = div_end_idx + 6
                new_content = content[:insert_pos] + '\n' + inventory_html + content[insert_pos:]
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Patched: {filepath}")
