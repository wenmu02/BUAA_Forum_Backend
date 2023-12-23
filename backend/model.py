from flask_sqlalchemy import SQLAlchemy
from app import app

# 初始化数据库
db = SQLAlchemy(app)


# 定义用户表模型
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(20), nullable=False, unique=True)
    user_key = db.Column(db.Text, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    academy = db.Column(db.Text, nullable=True)
    email = db.Column(db.Text, nullable=True)


# 定义帖子表模型
class Post(db.Model):
    __tablename__ = 'posts'
    post_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.String(1000), nullable=False)
    u_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('posts', cascade='all, delete-orphan'))
    post_time = db.Column(db.DateTime, nullable=True)
    title = db.Column(db.String(255), nullable=False)

    def comment_count(self):
        # Return the count of comments for this post
        return Comment.query.filter_by(to_id=self.post_id).count()

    def likes_count(self):
        return PostLikes.query.filter_by(post_id=self.post_id).count()


# 定义评论表模型
class Comment(db.Model):
    __tablename__ = 'comments'
    comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.String(1000), nullable=False)
    from_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey('posts.post_id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', cascade='all, delete-orphan'))
    post = db.relationship('Post', backref=db.backref('comments', cascade='all, delete-orphan'))
    comment_time = db.Column(db.DateTime, nullable=True)


class Tag(db.Model):
    __tablename__ = 'tags'
    tag_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(db.String(50), nullable=False, unique=True)


class PostTag(db.Model):
    __tablename__ = 'post_tags'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id', ondelete='CASCADE'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id', ondelete='CASCADE'), primary_key=True)


class PostLikes(db.Model):
    __tablename__ = 'post_likes'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)


class Friendship(db.Model):
    __tablename__ = 'friendships'
    user1_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)


class Community(db.Model):
    __tablename__ = 'communities'
    community_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    community_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

class CommunityUser(db.Model):
    __tablename__ = 'community_users'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.community_id', ondelete='CASCADE'), primary_key=True)
