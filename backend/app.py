from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
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
from user import *
from post import *
from community import *


@app.route('/post_comment', methods=['POST'])
@jwt_required()
def post_comment():
    try:
        data = request.get_json()
        content = data['content']
        from_user_id = get_jwt_identity()
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
@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@jwt_required()
def delete_comment(comment_id):
    try:
        # Get the comment by comment_id
        comment_to_delete = Comment.query.get(comment_id)

        # Check if the logged-in user is the owner of the post
        logged_in_user_id = jwt_required()

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


@app.route('/add_friendship', methods=['POST'])
@jwt_required()
def add_friendship():
    data = request.get_json()

    user1_id = get_jwt_identity()
    user2_id = data.get('user2_id')

    if not user1_id or not user2_id:
        return jsonify({'error': '无效的用户ID', 'code': 400})

    # Check if the friendship already exists
    existing_friendship = Friendship.query.filter_by(user1_id=user1_id, user2_id=user2_id).first()
    if existing_friendship:
        return jsonify({'error': '已关注', 'code': 400})

    # Create a new friendship
    new_friendship = Friendship(user1_id=user1_id, user2_id=user2_id)
    db.session.add(new_friendship)
    db.session.commit()

    return jsonify({'message': '成功关注', 'code': 1000})


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


if __name__ == '__main__':
    app.run(debug=True)
