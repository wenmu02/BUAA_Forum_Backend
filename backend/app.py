from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import func

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
from comment import *


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


@app.route('/get_followed_users', methods=['GET'])
@jwt_required()
def get_followed_users():
    user_id = get_jwt_identity()
    followed_users = db.session.query(User).join(Friendship, User.user_id == Friendship.user2_id).filter(
        Friendship.user1_id == user_id).all()
    user_list = [{'user_id': user.user_id, 'username': user.user_name} for user in followed_users]
    return jsonify({'followed_users': user_list, 'code': 1000})


@app.route('/get_user_communities', methods=['GET'])
@jwt_required()
def get_user_communities():
    user_id = get_jwt_identity()
    user_communities = db.session.query(Community).join(CommunityUser,
                                                        Community.community_id == CommunityUser.community_id).filter(
        CommunityUser.user_id == user_id).all()
    community_list = [
        {'community_id': community.community_id, 'name': community.community_name, 'description': community.description}
        for
        community in
        user_communities]
    return jsonify({'my_communities': community_list}), 200


@app.route('/top_tags/<int:n>', methods=['GET'])
def top_tags(n):
    try:
        top_tags = db.session.query(Tag.tag_name, func.count(PostTag.post_id).label('post_count')) \
            .join(PostTag, Tag.tag_id == PostTag.tag_id) \
            .group_by(Tag.tag_name) \
            .order_by(func.count(PostTag.post_id).desc()) \
            .limit(n) \
            .all()

        result = [{'tag_name': tag.tag_name, 'post_count': tag.post_count} for tag in top_tags]
        return jsonify({'top_tags': result, 'code': 1000})
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500})


if __name__ == '__main__':
    app.run(debug=True)
