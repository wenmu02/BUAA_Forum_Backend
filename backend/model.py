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


# 定义帖子表模型
class Post(db.Model):
    __tablename__ = 'posts'
    post_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.String(1000), nullable=False)
    u_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('posts', cascade='all, delete-orphan'))


# 定义评论表模型
class Comment(db.Model):
    __tablename__ = 'comments'
    comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.String(1000), nullable=False)
    from_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey('posts.post_id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', cascade='all, delete-orphan'))
    post = db.relationship('Post', backref=db.backref('comments', cascade='all, delete-orphan'))
