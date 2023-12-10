

CREATE TABLE users
(
    user_id   INT PRIMARY KEY AUTO_INCREMENT,
    user_name VARCHAR(20) NOT NULL UNIQUE,
    user_key  TEXT NOT NULL
);

CREATE TABLE posts
(
    post_id INT PRIMARY KEY AUTO_INCREMENT,
    content VARCHAR(1000) NOT NULL,
    u_id INT NOT NULL,
    FOREIGN KEY (u_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE comments
(
    comment_id INT PRIMARY KEY AUTO_INCREMENT,
    content VARCHAR(1000) NOT NULL,
    from_id INT NOT NULL,
    to_id INT NOT NULL,
    FOREIGN KEY (from_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (to_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

CREATE TABLE post_likes
(
    like_id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE friendships
(
    friendship_id INT PRIMARY KEY AUTO_INCREMENT,
    user1_id INT NOT NULL,
    user2_id INT NOT NULL,
    FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE private_messages
(
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    content VARCHAR(1000) NOT NULL,
    from_user_id INT NOT NULL,
    to_user_id INT NOT NULL,
    FOREIGN KEY (from_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (to_user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE communities
(
    community_id INT PRIMARY KEY AUTO_INCREMENT,
    community_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE community_users
(
    community_user_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    community_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (community_id) REFERENCES communities(community_id) ON DELETE CASCADE
);


