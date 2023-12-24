from flask import jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from model import *
from app import app, jwt


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # 提取前端发送的数据
    username = data.get('username')
    academy = data.get('academy')
    email = data.get('email')
    gender = data.get('gender')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    # 检查数据是否为空
    if not all([username, gender, password, confirm_password]):
        return jsonify({'message': '请填写必填项', 'code': 309})

    # 检查用户名是否已存在
    existing_user = User.query.filter_by(user_name=username).first()
    if existing_user:
        return jsonify({'message': '用户名已存在，请更换用户名', 'code': 409})

    if password != confirm_password:
        return jsonify({'message': '确认密码错误', 'code': 509})
    hashed_password = generate_password_hash(password, method='sha256')

    new_user = User(user_name=username, user_key=hashed_password, gender=gender, academy=academy, email=email)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': '注册成功', 'code': 1000})


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        user_name = data.get('username')
        user_key = data.get('password')

        if not user_name or not user_key:
            return jsonify({'message': '用户名或密码为空', 'code': 409})

        user = User.query.filter_by(user_name=user_name).first()

        if not user or not check_password_hash(user.user_key, user_key):
            return jsonify({'message': '用户名或密码错误', 'code': 509})

        # You can generate a token here if you want to implement token-based authentication
        user_id = user.user_id
        access_token = create_access_token(identity=user_id)
        return jsonify({'message': '登录成功', 'code': 1000,
                        'user': {'access_token': access_token, 'user_id': user_id, 'user_name': user_name}})
    except Exception as e:
        return jsonify({'message': str(e), 'code': 500})


@app.route('/modify_password', methods=['POST'])
@jwt_required()
def modify_password():
    data = request.get_json()
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user and check_password_hash(user.user_key, data['oldPassword']):
        user.user_key = generate_password_hash(data['newPassword'], method='sha256')
        db.session.commit()
        return jsonify({'message': '密码修改成功', 'code': 1000}), 200
    else:
        return jsonify({'message': '无效的凭证或旧密码', 'code': 401}), 401


# 注销用户
@app.route('/logout/', methods=['POST'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User logged out successfully!'}), 200


@app.route('/change_user', methods=['POST'])
@jwt_required()
def update_user_info():
    # 从请求中获取用户信息
    user_id = get_jwt_identity()
    data = request.json
    user = User.query.get(user_id)

    if user:
        # 更新用户信息
        user.gender = data['gender']
        user.academy = data['academy']
        user.email = data['email']
        # 检查新用户名是否与其他用户冲突
        if user.user_name != data['user_name'] and User.query.filter_by(user_name=data['user_name']).first():
            return jsonify({'message': '新用户名已被占用', 'code': 409})
        user.user_name = data['user_name']
        # 提交更改到数据库
        db.session.commit()

        return jsonify({'message': '用户信息更新成功', 'code': 1000})
    else:
        return jsonify({'message': '找不到用户', 'code': 509})


@app.route('/get_user', methods=['GET'])
@jwt_required()
def get_user():
    # Get the user_id from the query parameters
    user_id = get_jwt_identity()

    # Check if user_id is provided
    if user_id is None:
        return jsonify({'message': 'Parameter user_id is missing', 'code': 400}), 400

    # Query the database for the user with the given user_id
    user = User.query.get(user_id)

    # Check if the user exists
    if user is None:
        return jsonify({'message': 'User not found', 'code': 404}), 404

    # If the user exists, create a dictionary with user information
    user_info = {
        'user_id': user.user_id,
        'user_name': user.user_name,
        'gender': user.gender,
        'academy': user.academy,
        'email': user.email
    }

    # Return the user information as JSON
    return jsonify({'user': user_info, 'code': 1000}), 200
