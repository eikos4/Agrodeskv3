# passenger_wsgi.py

import os
import sys

# 1) Añade la ruta raíz de tu proyecto al PYTHONPATH para que Python encuentre run.py
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# 2) (Opcional) Asegura que Flask se ejecute en modo producción
os.environ.setdefault('FLASK_ENV', 'production')

# 3) Importa tu fábrica de aplicación
#    Si en run.py defines:
#      def create_app():
#          ...
#      if __name__ == '__main__':
#          app = create_app()
#          app.run(...)
#
#    Entonces aquí hacemos:
from run import create_app

# 4) Llama a create_app() para obtener el objeto WSGI que Passenger usará
application = create_app()