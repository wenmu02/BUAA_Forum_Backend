from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime  # 导入datetime模块
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

pymysql.install_as_MySQLdb()
app = Flask(__name__)
CORS(app)
# 配置数据库连接信息，例如数据库的URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:lxj021105@localhost:3306/buaa'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 设置密钥，用于加密 JWT
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

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
@app.route('/logout/', methods=['POST'])
@jwt_required()
def logout(user_name):
    user = User.query.filter_by(user_name=user_name).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User logged out successfully!'}), 200


# 发帖
@app.route('/create_post', methods=['POST'])
def create_post():
    try:
        data = request.get_json()
        # 从请求中获取数据
        user_id = data['user_id']
        content = data['content']
        tag_name = data['tag_name']
        title = data['title']
        # 获取当前时间
        current_time = datetime.utcnow()

        # 创建新的帖子并添加到数据库
        user = User.query.get(user_id)
        if user:
            new_post = Post(content=content, u_id=user_id, title=title, post_time=current_time)
            db.session.add(new_post)
            tag = Tag.query.filter_by(tag_name=tag_name).first()
            if tag:
                new_post_tag = PostTag(post_id=new_post.post_id, tag_id=tag.tag_id)
                db.session.add(new_post_tag)
            else:
                return jsonify({'error': '标签不存在', 'code': 409})
            db.session.commit()
            return jsonify({'message': '发帖成功', 'code': 1000})
        else:
            return jsonify({'error': '用户不存在或未登录', 'code': 409})
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500})


@app.route('/show_posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()
    post_list = []

    for post in posts:
        post_info = {
            'post_id': post.post_id,
            'content': post.content,
            'user_id': post.user_id,
            'post_time': post.post_time,
            'title': post.title
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
        comment_time = data['comment_time']

        if user and post:
            # Insert new comment into the 'comments' table
            new_comment = Comment(content=content, from_user_id=from_user_id, to_post_id=to_post_id,
                                  comment_time=comment_time)
            db.session.add(new_comment)
            db.session.commit()

            return jsonify({'message': '评论发布成功', 'code': 1000})
        else:
            return jsonify({'message': '用户或帖子不存在', 'code': 409})
    except Exception as e:
        return jsonify({'error': str(e), 'code': 309})


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


@app.route('/comments', methods=['POST'])
def get_comments_for_post():
    try:
        data = request.json

        post_id = data.get('post_id')

        if post_id is None:
            return jsonify({'error': 'Missing post_id parameter', 'code': 400})

        post = Post.query.get(post_id)

        if not post:
            return jsonify({'error': 'Post not found', 'code': 404})

        comments = Comment.query.filter_by(to_id=post_id).all()

        comments_data = []
        for comment in comments:
            comment_data = {
                'comment_id': comment.comment_id,
                'content': comment.content,
                'from_user': {
                    'user_id': comment.user.user_id,
                    'username': comment.user.username
                },
                'comment_time': comment.comment_time
            }
            comments_data.append(comment_data)

        return jsonify({'comments': comments_data, 'code': 1000})

    except Exception as e:
        return jsonify({'error': str(e), 'code': 500})


if __name__ == '__main__':
    app.run(debug=True)
