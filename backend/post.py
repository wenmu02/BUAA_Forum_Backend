from flask import jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from model import *
from app import app, jwt
from datetime import datetime
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
            post_tags = (
                db.session.query(Tag.tag_name)
                .join(PostTag, Tag.tag_id == PostTag.tag_id)
                .filter(PostTag.post_id == post.post_id)
                .all()
            )

            tag_names = [tag.tag_name for tag in post_tags]
            post_info = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'like_num': post.likes_count(),
                'user_id': post.u_id,
                'user_name': post.user.user_name,
                'post_time': post.post_time,
                'comments': post.comment_count(),
                'tag_names': tag_names
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
            post_tags = (
                db.session.query(Tag.tag_name)
                .join(PostTag, Tag.tag_id == PostTag.tag_id)
                .filter(PostTag.post_id == post.post_id)
                .all()
            )

            tag_names = [tag.tag_name for tag in post_tags]
            post_info = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'like_num': post.likes_count(),
                'user_id': post.u_id,
                'user_name': post.user.user_name,
                'post_time': post.post_time,
                'comments': post.comment_count(),
                'tag_names': tag_names
                # Add more fields as needed
            }
            post_list.append(post_info)
    if end_index > cnt:
        end_index = cnt
    post_list = post_list[start_index - 1:end_index]
    return jsonify({'data': post_list, 'total_num': cnt, 'code': 1000})


# API endpoint for deleting a post
@app.route('/delete_post/<int:post_id>', methods=['POST'])
@jwt_required()
def delete_post(post_id):
    # Get the post by post_id
    post_to_delete = Post.query.get(post_id)

    # Check if the logged-in user is the owner of the post
    logged_in_user_id = get_jwt_identity()

    if post_to_delete.u_id == logged_in_user_id:
        # Delete the post if the user is the owner
        db.session.delete(post_to_delete)
        db.session.commit()
        return jsonify({'message': 'Post deleted successfully', 'code': 1000})
    else:
        # Return an error if the user is not the owner
        return jsonify({'error': 'You are not authorized to delete this post', 'code': 5090})
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post_of(post_id):
    # Query the database for the post with the given post_id
    post = Post.query.get(post_id)

    # Check if the post exists
    if post is None:
        return jsonify({'message': 'Post not found', 'code': 404})

    post_tags = (
        db.session.query(Tag.tag_name)
        .join(PostTag, Tag.tag_id == PostTag.tag_id)
        .filter(PostTag.post_id == post_id)
        .all()
    )

    tag_names = [tag.tag_name for tag in post_tags]

    # Create a dictionary with post information
    post_info = {
        'post_id': post.post_id,
        'title': post.title,
        'content': post.content,
        'user_id': post.user.user_id,
        'user_name': post.user.user_name,
        'post_time': post.post_time.isoformat(),
        'comment_count': post.comment_count(),
        'likes_count': post.likes_count(),
        'tag_names': tag_names
    }

    # Return the post information as JSON
    return jsonify({'post': post_info, 'code': 1000})



@app.route('/get_myposts', methods=['GET'])
@jwt_required()
def get_myposts():
    # Extract query parameters from the request
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 5))
    user_id = get_jwt_identity()

    posts = Post.query.filter_by(u_id=user_id)

    start_index = size * (page - 1) + 1
    end_index = start_index + size
    post_list = []
    cnt = 0
    for post in posts:
        cnt += 1
        if start_index <= cnt < end_index:
            post_tags = (
                db.session.query(Tag.tag_name)
                .join(PostTag, Tag.tag_id == PostTag.tag_id)
                .filter(PostTag.post_id == post.post_id)
                .all()
            )

            tag_names = [tag.tag_name for tag in post_tags]
            post_info = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'like_num': post.likes_count(),
                'user_id': post.u_id,
                'user_name': post.user.user_name,
                'post_time': post.post_time,
                'comments': post.comment_count(),
                'tag_names': tag_names
                # Add more fields as needed
            }
            post_list.append(post_info)
    return jsonify({'data': post_list, 'total_num': cnt, 'code': 1000})


@app.route('/search_mypost', methods=['GET'])
@jwt_required()
def search_myposts():
    # 获取前端传递的参数
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 5))
    keyword = request.args.get('keyword', '')
    user_id = get_jwt_identity()

    posts = Post.query.filter_by(u_id=user_id)

    start_index = size * (page - 1) + 1
    end_index = start_index + size
    post_list = []
    cnt = 0
    for post in posts:
        if keyword in post.title or keyword in post.content:
            cnt += 1
            post_tags = (
                db.session.query(Tag.tag_name)
                .join(PostTag, Tag.tag_id == PostTag.tag_id)
                .filter(PostTag.post_id == post.post_id)
                .all()
            )

            tag_names = [tag.tag_name for tag in post_tags]
            post_info = {
                'post_id': post.post_id,
                'title': post.title,
                'content': post.content,
                'like_num': post.likes_count(),
                'user_id': post.u_id,
                'user_name': post.user.user_name,
                'post_time': post.post_time,
                'comments': post.comment_count(),
                'tag_names': tag_names
                # Add more fields as needed
            }
            post_list.append(post_info)
    if end_index > cnt:
        end_index = cnt
    post_list = post_list[start_index - 1:end_index]
    return jsonify({'data': post_list, 'total_num': cnt, 'code': 1000})
