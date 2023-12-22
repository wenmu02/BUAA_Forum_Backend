from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime  # 导入datetime模块
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

pymysql.install_as_MySQLdb()
app = Flask(__name__)
CORS(app)
# 配置数据库连接信息，例如数据库的URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:lxj021105@localhost:3306/buaa'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 设置密钥，用于加密 JWT
app.config['JWT_SECRET_KEY'] = 'qwsdcvhjkaok'
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


# 发帖
@app.route('/create_post', methods=['POST'])
@jwt_required()
def create_post():
    data = request.get_json()
    # 从请求中获取数据
    user_id = get_jwt_identity()
    content = data['content']
    tag_name = data['tag_name']
    title = data['title']
    # 获取当前时间
    current_time = datetime.utcnow()

    # 创建新的帖子并添加到数据库
    user = User.query.get(user_id)
    if user:
        if not content or not title:
            return jsonify({'message': '未填写标题和内容', 'code': 409})
        new_post = Post(content=content, u_id=user_id, title=title, post_time=current_time)
        db.session.add(new_post)

        tag = Tag.query.filter_by(tag_name=tag_name).first()
        if tag:
            new_post_tag = PostTag(post_id=new_post.post_id, tag_id=tag.tag_id)
            db.session.add(new_post_tag)
        else:
            return jsonify({'message': '标签不存在', 'code': 409})
        db.session.commit()
        return jsonify({'message': '发帖成功', 'code': 1000})
    else:
        return jsonify({'message': '用户不存在或未登录', 'code': 409})


@app.route('/get_tags', methods=['GET'])
@jwt_required()
def get_tags():
    tags = Tag.query.all()

    # 构建标签信息列表
    tag_list = []
    for tag in tags:
        tag_info = {
            'tag_id': tag.tag_id,
            'tag_name': tag.tag_name
        }
        tag_list.append(tag_info)

    return jsonify({'data': tag_list}), 200


@app.route('/get_posts', methods=['GET'])
def get_posts():
    # Extract query parameters from the request
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 5))
    order = request.args.get('order', 'time')  # Default to 'time' if not provided

    posts = Post.query.all()
    if order == 'time':
        sorted_posts = sorted(posts, key=lambda x: x.post_time, reverse=True)
    else:
        sorted_posts = sorted(posts, key=lambda x: x.likes_count(), reverse=True)

    start_index = size * (page - 1) + 1
    end_index = start_index + size
    post_list = []
    cnt = 0
    for post in sorted_posts:
        cnt += 1
        if start_index <= cnt < end_index:
            post_info = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'like_num': post.likes_count(),
                'user_id': post.u_id,
                'post_time': post.post_time,
                'comments': post.comment_count()
                # Add more fields as needed
            }
            post_list.append(post_info)
    return jsonify({'data': post_list, 'total_num': cnt, 'code': 1000})


@app.route('/search_post', methods=['GET'])
def search_posts():
    # 获取前端传递的参数
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 5))
    keyword = request.args.get('keyword', '')

    posts = Post.query.all()

    start_index = size * (page - 1) + 1
    end_index = start_index + size
    post_list = []
    cnt = 0
    for post in posts:
        if keyword in post.title or keyword in post.content:
            cnt += 1
            post_info = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'like_num': post.likes_count(),
                'user_id': post.u_id,
                'post_time': post.post_time,
                'comments': post.comment_count()
                # Add more fields as needed
            }
            post_list.append(post_info)
    if end_index > cnt:
        end_index = cnt
    post_list = post_list[start_index - 1:end_index]
    return jsonify({'data': post_list, 'total_num': cnt, 'code': 1000})


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


@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post_of(post_id):
    # Query the database for the post with the given post_id
    post = Post.query.get(post_id)

    # Check if the post exists
    if post is None:
        return jsonify({'message': 'Post not found', 'code': 404})

    # Create a dictionary with post information
    post_info = {
        'post_id': post.post_id,
        'title': post.title,
        'content': post.content,
        'user_id': post.user.user_id,
        'user_name': post.user.user_name,
        'post_time': post.post_time.isoformat(),
        'comment_count': post.comment_count(),
        'likes_count': post.likes_count()
    }

    # Return the post information as JSON
    return jsonify({'post': post_info, 'code': 1000})


@app.route('/vote', methods=['POST'])
@jwt_required()
def vote():
    try:
        # Get data from the request
        data = request.get_json()
        post_id = data.get('post_id')

        # Assuming you have a user authentication mechanism (replace this with your own logic)
        # For example, you can get user information from a session or token
        user_id = get_jwt_identity()

        # Check if the user has already liked the post
        existing_like = PostLikes.query.filter_by(user_id=user_id, post_id=post_id).first()
        if existing_like:
            return jsonify({'code': 1009, 'message': '请勿重复点赞'}), 200

        # Perform additional checks or business logic here...

        # Create a new like record
        new_like = PostLikes(user_id=user_id, post_id=post_id)
        db.session.add(new_like)
        db.session.commit()

        return jsonify({'code': 1000, 'message': '点赞成功'}), 200

    except Exception as e:
        # Handle exceptions (e.g., database errors) appropriately
        return jsonify({'code': 500, 'msg': str(e)}), 500


@app.route('/change_user', methods=['POST'])
@jwt_required()
def update_user_info():
    # 从请求中获取用户信息
    user_id = get_jwt_identity()
    data = request.json
    # 根据用户名查找用户
    user = User.query.get(user_id)

    if user:
        # 更新用户信息
        user.gender = data['gender']
        user.academy = data['academy']
        user.email = data['email']
        # 检查新用户名是否与其他用户冲突
        if User.query.filter_by(user_name=data['user_name']).first():
            return jsonify({'message': '新用户名已被占用', 'code': 409})
        user.user_name = data['user_name']
        # 提交更改到数据库
        db.session.commit()

        return jsonify({'message': '用户信息更新成功', 'code': 1000})
    else:
        return jsonify({'message': '找不到用户', 'code': 509})


if __name__ == '__main__':
    app.run(debug=True)
