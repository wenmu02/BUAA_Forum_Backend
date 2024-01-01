from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from model import *
from app import app, jwt
from datetime import datetime


@app.route('/post_comment', methods=['POST'])
@jwt_required()
def post_comment():
    data = request.get_json()
    content = data['content']
    from_user_id = get_jwt_identity()
    user = User.query.get(from_user_id)
    to_post_id = data['to_post_id']
    post = Post.query.get(to_post_id)
    comment_time = datetime.utcnow()

    if user and post:
        # Insert new comment into the 'comments' table
        new_comment = Comment(content=content, from_id=from_user_id, to_id=to_post_id,
                              comment_time=comment_time)
        db.session.add(new_comment)
        db.session.commit()

        return jsonify({'message': '评论发布成功', 'code': 1000})
    else:
        return jsonify({'message': '用户或帖子不存在', 'code': 409})


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
    data = request.json
    post_id = data['post_id']

    if post_id is None:
        return jsonify({'error': 'Missing post_id parameter', 'code': 400})

    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': 'Post not found', 'code': 404})
    comments = Comment.query.filter_by(to_id=post_id).all()

    comments_data = []
    for comment in comments:
        replies = SecondaryComment.query.filter_by(to_id=comment.comment_id).all()

        replies_data = []
        for reply in replies:
            reply_data = {
                'secondary_comment_id': reply.secondary_comment_id,
                'content': reply.content,
                'author_id': reply.user.user_id,
                'author': reply.user.user_name,
                'timestamp': reply.comment_time,
                'avatar': 'http://i9.photobucket.com/albums/a88/creaticode/avatar_2_zps7de12f8b.jpg'
            }
            replies_data.append(reply_data)
        comment_data = {
            'comment_id': comment.comment_id,
            'content': comment.content,
            'author_id': comment.user.user_id,
            'author': comment.user.user_name,
            'timestamp': comment.comment_time,
            'avatar': 'http://i9.photobucket.com/albums/a88/creaticode/avatar_1_zps8e1c80cd.jpg',
            'replies': replies_data,
            'showReplyInput': False,
            'input': ''
        }
        comments_data.append(comment_data)

    return jsonify({'comments': comments_data, 'code': 1000})


@app.route('/get_replies', methods=['POST'])
def get_replies():
    data = request.get_json()

    primary_comment_id = data['primary_comment_id']
    if primary_comment_id is None:
        return jsonify({'error': 'Missing primary_comment_id parameter', 'code': 400})

    primary_comment = Comment.query.get(primary_comment_id)
    if not primary_comment:
        return jsonify({'error': 'Primary comment not found', 'code': 404})

    # Fetch all secondary comments (replies) for the primary comment
    replies = SecondaryComment.query.filter_by(to_id=primary_comment_id).all()

    replies_data = []
    for reply in replies:
        reply_data = {
            'secondary_comment_id': reply.secondary_comment_id,
            'content': reply.content,
            'author_id': reply.user.user_id,
            'author': reply.user.username,
            'timestamp': reply.comment_time,
        }
        replies_data.append(reply_data)

    return jsonify({'replies': replies_data, 'code': 1000})


@app.route('/send_secondary_comment', methods=['POST'])
@jwt_required()
def send_secondary_comment():
    data = request.get_json()

    content = data['content']
    from_id = get_jwt_identity()
    to_id = data.get('to_id')

    if not all([content, from_id, to_id]):
        return jsonify({'error': 'Missing data', 'code': 400})

    new_secondary_comment = SecondaryComment(
        content=content,
        from_id=from_id,
        to_id=to_id,
        comment_time=datetime.utcnow()
    )

    db.session.add(new_secondary_comment)
    db.session.commit()

    return jsonify({'message': 'Secondary comment sent successfully', 'code': 1000})
