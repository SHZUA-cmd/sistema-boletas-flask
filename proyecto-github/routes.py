# project/routes.py
from flask import Blueprint, request, jsonify
from .models import User, Boleta
from . import db, jwt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

api_bp = Blueprint('api', __name__)

# Mantenemos esto comentado por ahora para simplificar
#@jwt.additional_claims_loader
#def add_claims_to_jwt(identity):
#    user = db.session.get(User, identity)
#    if user:
#        return {"role": user.role}
#    return {}

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Faltan el nombre de usuario o la contraseña"}), 400

    # --- CONSULTA CORREGIDA A ESTILO MODERNO ---
    user_exists = db.session.execute(db.select(User).filter_by(username=data['username'])).scalar_one_or_none()
    if user_exists:
        return jsonify({"msg": "El nombre de usuario ya existe"}), 409

    user = User(username=data['username'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "Usuario creado exitosamente"}), 201

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Faltan el nombre de usuario o la contraseña"}), 400

    # --- CONSULTA CORREGIDA A ESTILO MODERNO ---
    user = db.session.execute(db.select(User).filter_by(username=data['username'])).scalar_one_or_none()

    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=1) # PRUEBA: Usamos un ID fijo)
        return jsonify(access_token=access_token)

    return jsonify({"msg": "Nombre de usuario o contraseña incorrectos"}), 401

@api_bp.route('/boletas/manual', methods=['POST'])
@jwt_required()
def create_boleta():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    if not data or not data.get('fecha') or not data.get('monto_total') or not data.get('categoria'):
        return jsonify({"msg": "Faltan campos requeridos"}), 400
    new_boleta = Boleta(
        fecha=data['fecha'],
        monto_total=float(data['monto_total']),
        categoria=data['categoria'],
        notas=data.get('notas'),
        user_id=current_user_id
    )
    db.session.add(new_boleta)
    db.session.commit()
    return jsonify(new_boleta.to_dict()), 201

@api_bp.route('/boletas', methods=['GET'])
@jwt_required()
def get_boletas():
    # Lógica simplificada que ya tenías
    current_user_id = get_jwt_identity()
    boletas = db.session.execute(db.select(Boleta).filter_by(user_id=current_user_id)).scalars().all()
    return jsonify([boleta.to_dict() for boleta in boletas])