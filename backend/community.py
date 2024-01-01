from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from model import *
from app import app, jwt


@app.route('/community', methods=['POST'])
@jwt_required()
def create_community():
    data = request.json
    community_name = data.get('community_name')
    description = data.get('description')

    new_community = Community(community_name=community_name, description=description)

    try:
        db.session.add(new_community)
        db.session.commit()
        return jsonify({"message": "Community created successfully", 'code': 1000})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Community created failed", 'code': 500})


@app.route('/join_community', methods=['POST'])
@jwt_required()
def join_community():
    data = request.json
    user_id = get_jwt_identity()
    community_id = data.get('community_id')

    new_community_user = CommunityUser(user_id=user_id, community_id=community_id)

    if CommunityUser.query.filter_by(user_id=user_id, community_id=community_id).first():
        return jsonify({"message": "重复加入社区", 'code': 509})
    db.session.add(new_community_user)
    db.session.commit()
    return jsonify({"message": "成功加入社区", "code": 1000})


@app.route('/leave_community', methods=['POST'])
@jwt_required()
def leave_community():
    data = request.json
    user_id = get_jwt_identity()
    community_id = data.get('community_id')

    community_user = CommunityUser.query.filter_by(user_id=user_id, community_id=community_id).first()

    if not community_user:
        return jsonify({"message": "用户未加入社区", 'code': 404})

    db.session.delete(community_user)
    db.session.commit()

    return jsonify({"message": "成功退出社区", "code": 1000})


@app.route('/get_communities', methods=['GET'])
def get_communities():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 5))
    start_index = size * (page - 1) + 1
    end_index = start_index + size

    communities = Community.query.all()
    community_list = []
    cnt = 0
    for community in communities:
        cnt += 1
        if start_index <= cnt < end_index:
            users = db.session.query(User).join(CommunityUser).filter(
                CommunityUser.community_id == community.community_id).all()
            community_info = {
                'community_id': community.community_id,
                'community_name': community.community_name,
                'description': community.description,
                'users': [{'user_id': user.user_id, 'user_name': user.user_name} for user in users]
                # Add more fields as needed
            }
            community_list.append(community_info)
    return jsonify({'data': community_list, 'total_num': cnt, 'code': 1000})


@app.route('/search_community', methods=['GET'])
def search_community():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 5))
    keyword = str(request.args.get('keyword', ''))

    start_index = size * (page - 1) + 1
    end_index = start_index + size

    communities = Community.query.all()
    community_list = []
    cnt = 0
    for community in communities:
        if keyword in community.community_name:
            cnt += 1
            users = db.session.query(User).join(CommunityUser).filter(
                CommunityUser.community_id == community.community_id).all()
            community_info = {
                'community_id': community.community_id,
                'community_name': community.community_name,
                'description': community.description,
                'users': [{'user_id': user.user_id, 'user_name': user.user_name} for user in users]
            }
            community_list.append(community_info)
    if end_index > cnt:
        end_index = cnt
    community_list = community_list[start_index - 1:end_index]
    return jsonify({'data': community_list, 'total_num': cnt, 'code': 1000})
