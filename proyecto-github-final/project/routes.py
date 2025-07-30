# project/routes.py
"""Define todos los endpoints (rutas) de la API de la aplicación.

Este archivo utiliza un Blueprint de Flask para organizar las rutas.
Contiene la lógica para el registro, login, OCR y las operaciones
CRUD (Crear, Leer, Actualizar, Eliminar) para las boletas, así como
la gestión de usuarios y categorías por parte del administrador.
"""
import re
import os
import secrets
import easyocr
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from .models import User, Boleta, Categoria
from . import db
from functools import wraps

# Crea un Blueprint, que es como una mini-aplicación para agrupar rutas.
api_bp = Blueprint('api', __name__)

# Se inicializa el lector de OCR una sola vez al cargar la aplicación para mejorar el rendimiento.
# Se configura para español y para usar CPU.
reader = easyocr.Reader(['es'], gpu=False)

def parse_ocr_text(text_list):
    """
    Analiza el texto extraído de una imagen para encontrar la fecha y el monto total.

    Esta función utiliza una serie de expresiones regulares y lógicas de prioridad
    para identificar los datos más probables, manejando múltiples formatos de fecha
    y filtrando números irrelevantes para encontrar el monto correcto.

    Args:
        text_list (list): Una lista de strings extraídos de la imagen por EasyOCR.

    Returns:
        tuple: Una tupla conteniendo la fecha (str) y el monto (int) encontrados.
    """
    full_text = "\n".join(text_list)
    fecha = None
    monto = 0

    # --- LÓGICA DE FECHA UNIFICADA Y FINAL ---
    # Se definen los patrones de fecha en orden de especificidad para probarlos secuencialmente.
    date_patterns = [
        # Formato largo: 4 de marzo del 2020
        r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+del?\s+(\d{4})',
        # Formato corto: 07 jul 2023
        r'(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s+(\d{4})',
        # Formato AAAA-MM-DD: 2020-09-28
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
        # Formato DD-MM-AAAA: 28-09-2020
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})'
    ]
    
    month_map_full = {'enero':'01','febrero':'02','marzo':'03','abril':'04','mayo':'05','junio':'06','julio':'07','agosto':'08','septiembre':'09','octubre':'10','noviembre':'11','diciembre':'12'}
    month_map_short = {'ene':'01','feb':'02','mar':'03','abr':'04','may':'05','jun':'06','jul':'07','ago':'08','sep':'09','oct':'10','nov':'11','dic':'12'}

    for i, pattern in enumerate(date_patterns):
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                # Se normaliza la fecha encontrada al formato AAAA-MM-DD
                if i == 0: day, month_text, year = groups; month = month_map_full.get(month_text.lower()); fecha = f"{year}-{month}-{day.zfill(2)}"
                elif i == 1: day, month_text, year = groups; month = month_map_short.get(month_text.lower()); fecha = f"{year}-{month}-{day.zfill(2)}"
                elif i == 2: year, month, day = groups; fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                elif i == 3: day, month, year = groups; fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                if fecha:
                    break # Si se encuentra y procesa una fecha, se detiene la búsqueda
            except:
                continue # Si hay un error de formato, se prueba el siguiente patrón

    # --- LÓGICA DE MONTO FINAL: EL NÚMERO MÁS GRANDE ES EL TOTAL ---
    # Patrón para encontrar todos los números con formato de miles (ej. 1.234) o simples (ej. 238)
    amount_pattern = r'(\d{1,3}(?:[.,]\d{3})*)'
    
    amounts = re.findall(amount_pattern, full_text)
    
    if amounts:
        cleaned_amounts = []
        for a in amounts:
            num_str = a.replace('.', '').replace(',', '').replace(' ', '')
            # Filtro de seguridad: ignorar números muy largos (RUTs) o cortos (cantidades)
            if num_str.isdigit() and len(num_str) < 8 and len(num_str) > 2:
                cleaned_amounts.append(int(num_str))
        
        if cleaned_amounts:
            # Se elige el número más alto de la lista filtrada
            monto = max(cleaned_amounts)

    return fecha, monto

def api_key_required(fn):
    """Decorador personalizado para proteger rutas con una API Key.

    Verifica la presencia y validez de la cabecera 'X-Api-Key' en la petición.
    Si es válida, pasa el objeto 'User' correspondiente a la ruta.
    """
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-Api-Key')
        if not api_key: return jsonify({"msg": "Falta la cabecera X-Api-Key"}), 401
        user = db.session.execute(db.select(User).filter_by(api_key=api_key)).scalar_one_or_none()
        if not user: return jsonify({"msg": "API Key inválida"}), 401
        return fn(current_user=user, *args, **kwargs)
    return decorated_function

# --- Rutas de Autenticación y Usuarios ---

@api_bp.route('/register', methods=['POST'])
def register():
    """Registra un nuevo usuario. El primer usuario registrado es un administrador."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'): return jsonify({"msg": "Faltan campos requeridos"}), 400
    if db.session.execute(db.select(User).filter_by(username=data['username'])).scalar_one_or_none(): return jsonify({"msg": "El nombre de usuario ya existe"}), 409
    
    is_first_user = db.session.execute(db.select(User)).first() is None
    user = User(username=data['username'])
    user.set_password(data['password'])
    user.generate_api_key()
    if is_first_user: user.role = 'admin'
    
    db.session.add(user)
    db.session.commit()
    msg = "Usuario Administrador creado exitosamente" if is_first_user else "Usuario creado exitosamente"
    return jsonify({"msg": msg}), 201

@api_bp.route('/login', methods=['POST'])
def login():
    """Autentica a un usuario y devuelve su API Key y rol."""
    data = request.get_json()
    user = db.session.execute(db.select(User).filter_by(username=data['username'])).scalar_one_or_none()
    if user and user.check_password(data['password']):
        return jsonify(api_key=user.api_key, role=user.role)
    return jsonify({"msg": "Credenciales incorrectas"}), 401

@api_bp.route('/users', methods=['POST'])
@api_key_required
def create_user_by_admin(current_user):
    """Permite a un administrador crear nuevos usuarios (normales o admins)."""
    if current_user.role != 'admin': return jsonify({"msg": "Permisos de administrador requeridos"}), 403
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = 'admin' if data.get('is_admin') else 'user'
    if not username or not password: return jsonify({"msg": "Faltan campos requeridos"}), 400
    if db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none(): return jsonify({"msg": "El nombre de usuario ya existe"}), 409
    user = User(username=username, role=role)
    user.set_password(password)
    user.generate_api_key()
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": f"Usuario '{username}' creado con rol '{role}'."}), 201

# --- Rutas de Gestión de Boletas (CRUD) ---

@api_bp.route('/boletas/manual', methods=['POST'])
@api_key_required
def create_boleta(current_user):
    """Crea una nueva boleta a partir de datos de formulario y una imagen."""
    fecha = request.form.get('fecha')
    monto_total = request.form.get('monto_total')
    categoria_id = request.form.get('categoria_id')
    razon_modificacion = request.form.get('razon_modificacion')
    if not fecha or not monto_total or not categoria_id: return jsonify({"msg": "Los campos fecha, monto y categoría son obligatorios."}), 400
    try: monto_procesado = int(float(monto_total))
    except (ValueError, TypeError): return jsonify({"msg": "El monto total debe ser un número válido."}), 400
    
    imagen_nombre_archivo = None
    if 'boleta_image' in request.files:
        file = request.files['boleta_image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            unique_filename = f"{secrets.token_hex(8)}_{filename}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(save_path)
            imagen_nombre_archivo = unique_filename

    new_boleta = Boleta(fecha=fecha, monto_total=monto_procesado, categoria_id=int(categoria_id), notas=request.form.get('notas'), razon_modificacion=razon_modificacion, imagen_url=imagen_nombre_archivo, user_id=current_user.id)
    db.session.add(new_boleta)
    db.session.commit()
    return jsonify(new_boleta.to_dict()), 201

@api_bp.route('/boletas', methods=['GET'])
@api_key_required
def get_boletas(current_user):
    """Obtiene una lista paginada y filtrada de boletas."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    creador_username = request.args.get('creador', None, type=str)
    fecha_inicio = request.args.get('fecha_inicio', None, type=str)
    fecha_fin = request.args.get('fecha_fin', None, type=str)
    categoria_nombre = request.args.get('categoria', None, type=str)
    razon = request.args.get('razon', None, type=str)
    
    query = db.select(Boleta)
    if creador_username: query = query.join(User).filter(User.username.ilike(f"%{creador_username}%"))
    if fecha_inicio: query = query.filter(Boleta.fecha >= fecha_inicio)
    if fecha_fin: query = query.filter(Boleta.fecha <= fecha_fin)
    if categoria_nombre: query = query.join(Categoria).filter(Categoria.nombre == categoria_nombre)
    if razon: query = query.filter(Boleta.razon_modificacion == razon)
    if current_user.role != 'admin': query = query.filter(Boleta.user_id == current_user.id, Boleta.is_deleted == False)
    
    query = query.order_by(Boleta.fecha.desc())
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    boletas = pagination.items
    return jsonify({"boletas": [b.to_dict() for b in boletas], "total_pages": pagination.pages, "current_page": pagination.page, "has_next": pagination.has_next, "has_prev": pagination.has_prev})

@api_bp.route('/boletas/upload', methods=['POST'])
@api_key_required
def upload_boleta(current_user):
    """Procesa una imagen de boleta con OCR y devuelve los datos sugeridos."""
    if 'boleta_image' not in request.files: return jsonify({"msg": "No se encontró el archivo de imagen"}), 400
    file = request.files['boleta_image']
    if file.filename == '': return jsonify({"msg": "No se seleccionó ningún archivo"}), 400
    
    image_bytes = file.read()
    result = reader.readtext(image_bytes, detail=0, paragraph=False)
    fecha, monto = parse_ocr_text(result)
    
    success = True
    message = "Datos extraídos con éxito."
    if not fecha or monto == 0:
        success = False
        message = "No se pudieron leer los datos clave (fecha y monto). La calidad de la imagen puede ser baja. Por favor, ingrese los datos manualmente."
    
    return jsonify({"fecha_sugerida": fecha, "monto_sugerido": int(monto) if monto else 0, "success": success, "message": message})

@api_bp.route('/boletas/<int:boleta_id>', methods=['PUT'])
@api_key_required
def update_boleta(current_user, boleta_id):
    """Actualiza los datos de una boleta existente."""
    boleta = db.session.get(Boleta, boleta_id)
    if not boleta: return jsonify({"msg": "Boleta no encontrada"}), 404
    if boleta.user_id != current_user.id and current_user.role != 'admin': return jsonify({"msg": "No autorizado"}), 403
    
    data = request.get_json()
    if not data: return jsonify({"msg": "No se recibieron datos JSON en la petición."}), 400
    
    boleta.fecha = data.get('fecha', boleta.fecha)
    boleta.monto_total = int(float(data.get('monto_total', boleta.monto_total)))
    boleta.categoria_id = int(data.get('categoria_id', boleta.categoria_id))
    boleta.notas = data.get('notas', boleta.notas)
    boleta.razon_modificacion = 'Corrección Manual'
    
    db.session.commit()
    return jsonify(boleta.to_dict()), 200

@api_bp.route('/boletas/<int:boleta_id>', methods=['DELETE'])
@api_key_required
def delete_boleta(current_user, boleta_id):
    """Marca una boleta como eliminada (soft delete)."""
    boleta = db.session.get(Boleta, boleta_id)
    if not boleta: return jsonify({"msg": "Boleta no encontrada"}), 404
    if boleta.user_id != current_user.id and current_user.role != 'admin': return jsonify({"msg": "No autorizado para eliminar"}), 403
    
    boleta.is_deleted = True
    db.session.commit()
    return jsonify({"msg": "Boleta marcada como eliminada"}), 200

@api_bp.route('/uploads/<path:filename>')
@api_key_required
def get_uploaded_file(current_user, filename):
    """Sirve un archivo de imagen guardado de forma segura."""
    boleta = db.session.execute(db.select(Boleta).filter_by(imagen_url=filename)).scalar_one_or_none()
    if not boleta: return "Archivo no encontrado", 404
    if current_user.role != 'admin' and boleta.user_id != current_user.id: return "No autorizado", 403
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# --- Rutas de Gestión de Categorías (Solo Admins) ---

@api_bp.route('/categorias', methods=['GET'])
@api_key_required
def get_categorias(current_user):
    """Obtiene una lista de todas las categorías disponibles."""
    categorias = db.session.execute(db.select(Categoria).order_by(Categoria.nombre)).scalars().all()
    return jsonify([c.to_dict() for c in categorias])

@api_bp.route('/categorias', methods=['POST'])
@api_key_required
def create_categoria(current_user):
    """Crea una nueva categoría de gasto."""
    if current_user.role != 'admin': return jsonify({"msg": "Permisos de administrador requeridos"}), 403
    data = request.get_json()
    if not data or not data.get('nombre'): return jsonify({"msg": "El nombre es requerido"}), 400
    if db.session.execute(db.select(Categoria).filter_by(nombre=data['nombre'])).scalar_one_or_none(): return jsonify({"msg": "La categoría ya existe"}), 409
    
    nueva_categoria = Categoria(nombre=data['nombre'])
    db.session.add(nueva_categoria)
    db.session.commit()
    return jsonify(nueva_categoria.to_dict()), 201

@api_bp.route('/categorias/<int:categoria_id>', methods=['DELETE'])
@api_key_required
def delete_categoria(current_user, categoria_id):
    """Elimina una categoría, solo si no está en uso."""
    if current_user.role != 'admin': return jsonify({"msg": "Permisos de administrador requeridos"}), 403
    categoria = db.session.get(Categoria, categoria_id)
    if not categoria: return jsonify({"msg": "Categoría no encontrada"}), 404
    if categoria.boletas: return jsonify({"msg": "No se puede eliminar la categoría porque está siendo usada en boletas existentes."}), 400
    
    db.session.delete(categoria)
    db.session.commit()
    return jsonify({"msg": "Categoría eliminada exitosamente"}), 200