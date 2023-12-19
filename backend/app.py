from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

pymysql.install_as_MySQLdb()
app = Flask(__name__)
CORS(app)
# 配置数据库连接信息，例如数据库的URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:lxj021105@localhost:3306/buaa'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from model import *


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

        user_name = data.get('user_name')
        user_key = data.get('user_key')
        if not user_name or not user_key:
            return jsonify({'message': 'Missing username or password'}), 400

        user = User.query.filter_by(user_name=user_name).first()

        if not user or not check_password_hash(user.user_key, user_key):
            return jsonify({'message': 'Invalid username or password'}), 401

        # You can generate a token here if you want to implement token-based authentication

        return jsonify({'message': 'Login successful!'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/modify_password', methods=['POST'])
def modify_password():
    data = request.get_json()
    user = User.query.filter_by(user_name=data['user_name']).first()

    if user and check_password_hash(user.user_key, data['old_password']):
        user.user_key = generate_password_hash(data['new_password'], method='sha256')
        db.session.commit()
        return jsonify({'message': '密码修改成功'}), 200
    else:
        return jsonify({'message': '无效的凭证或旧密码'}), 401


# 注销用户
@app.route('/logout/<string:user_name>', methods=['POST'])
def logout(user_name):
    user = User.query.filter_by(user_name=user_name).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User logged out successfully!'}), 200


@app.route('/create_post', methods=['POST'])
def create_post():
    try:
        # 从请求中获取数据
        user_id = request.json.get('user_id')
        content = request.json.get('content')
        # 创建新的帖子并添加到数据库
        user = User.query.get(user_id)
        if user:
            new_post = Post(content=content, u_id=user_id)
            db.session.add(new_post)
            db.session.commit()
            return jsonify({'message': 'Post created successfully!'}), 201
        else:
            return jsonify({'error': 'User not found!'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/show_posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()
    post_list = []

    for post in posts:
        post_info = {
            'post_id': post.post_id,
            'content': post.content,
            'user_id': post.user_id
            # Add more fields as needed
        }
        post_list.append(post_info)

    print(jsonify({'posts': post_list}))
    return jsonify({'posts': post_list})


# API endpoint for deleting a post
@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    try:
        # Get the post by post_id
        post_to_delete = Post.query.get(post_id)

        # Check if the logged-in user is the owner of the post
        logged_in_user_id = request.headers.get('user_id')

        if post_to_delete.user_id == logged_in_user_id:
            # Delete the post if the user is the owner
            db.session.delete(post_to_delete)
            db.session.commit()
            return jsonify({'message': 'Post deleted successfully'}), 200
        else:
            # Return an error if the user is not the owner
            return jsonify({'error': 'You are not authorized to delete this post'}), 403

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/post_comment', methods=['POST'])
def post_comment():
    try:
        data = request.get_json()
        content = data['content']
        from_user_id = data['from_user_id']
        user = User.query.get(from_user_id)
        to_post_id = data['to_post_id']
        post = Post.query.get(to_post_id)

        if user and post:
            # Insert new comment into the 'comments' table
            new_comment = Comment(content=content, from_user_id=from_user_id, to_post_id=to_post_id)
            db.session.add(new_comment)
            db.session.commit()

            return jsonify({'message': 'Comment posted successfully'}), 201
        else:
            return jsonify({'message': '用户或帖子不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# API endpoint for deleting a comment
@app.route('/delete_comment/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    try:
        # Get the comment by comment_id
        comment_to_delete = Comment.query.get(comment_id)

        # Check if the logged-in user is the owner of the post
        logged_in_user_id = request.headers.get('user_id')

        if comment_to_delete.user_id == logged_in_user_id:
            # Delete the post if the user is the owner
            db.session.delete(comment_to_delete)
            db.session.commit()

            return jsonify({'message': 'Comment deleted successfully'}), 200
        else:
            # Return an error if the user is not the owner
            return jsonify({'error': 'You are not authorized to delete this post'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
