create table communities
(
    community_id   int auto_increment
        primary key,
    community_name varchar(50) not null,
    description    text        null,
    constraint community_name
        unique (community_name)
);

create table tags
(
    tag_id   int auto_increment
        primary key,
    tag_name varchar(50) not null
);

create table users
(
    user_id   int auto_increment
        primary key,
    user_name varchar(20) not null,
    user_key  text        not null,
    gender    varchar(20) not null,
    academy   text        null,
    email     text        null,
    constraint user_name
        unique (user_name)
);

create table community_users
(
    community_user_id int auto_increment
        primary key,
    user_id           int not null,
    community_id      int not null,
    constraint community_users_ibfk_1
        foreign key (user_id) references users (user_id)
            on delete cascade,
    constraint community_users_ibfk_2
        foreign key (community_id) references communities (community_id)
            on delete cascade
);

create index community_id
    on community_users (community_id);

create index user_id
    on community_users (user_id);

create table friendships
(
    friendship_id int auto_increment
        primary key,
    user1_id      int not null,
    user2_id      int not null,
    constraint friendships_ibfk_1
        foreign key (user1_id) references users (user_id)
            on delete cascade,
    constraint friendships_ibfk_2
        foreign key (user2_id) references users (user_id)
            on delete cascade
);

create index user1_id
    on friendships (user1_id);

create index user2_id
    on friendships (user2_id);

create table posts
(
    post_id   int auto_increment
        primary key,
    content   varchar(1000) not null,
    u_id      int           not null,
    post_time datetime      null,
    title     varchar(255)  not null,
    constraint posts_ibfk_1
        foreign key (u_id) references users (user_id)
            on delete cascade
);

create table comments
(
    comment_id   int auto_increment
        primary key,
    content      varchar(1000) not null,
    from_id      int           not null,
    to_id        int           not null,
    comment_time datetime      null,
    constraint comments_ibfk_1
        foreign key (from_id) references users (user_id)
            on delete cascade,
    constraint comments_ibfk_2
        foreign key (to_id) references posts (post_id)
            on delete cascade
);

create index from_id
    on comments (from_id);

create index to_id
    on comments (to_id);

create table post_likes
(
    like_id int auto_increment
        primary key,
    post_id int not null,
    user_id int not null,
    constraint post_likes_ibfk_1
        foreign key (post_id) references posts (post_id)
            on delete cascade,
    constraint post_likes_ibfk_2
        foreign key (user_id) references users (user_id)
            on delete cascade
);

create index post_id
    on post_likes (post_id);

create index user_id
    on post_likes (user_id);

create table post_tags
(
    post_tag_id int auto_increment
        primary key,
    post_id     int null,
    tag_id      int null,
    constraint post_tags_ibfk_1
        foreign key (post_id) references posts (post_id)
            on delete cascade,
    constraint post_tags_ibfk_2
        foreign key (tag_id) references tags (tag_id)
            on delete cascade
);

create index post_id
    on post_tags (post_id);

create index tag_id
    on post_tags (tag_id);

create index u_id
    on posts (u_id);

create table private_messages
(
    message_id   int auto_increment
        primary key,
    content      varchar(1000) not null,
    from_user_id int           not null,
    to_user_id   int           not null,
    constraint private_messages_ibfk_1
        foreign key (from_user_id) references users (user_id)
            on delete cascade,
    constraint private_messages_ibfk_2
        foreign key (to_user_id) references users (user_id)
            on delete cascade
);

create index from_user_id
    on private_messages (from_user_id);

create index to_user_id
    on private_messages (to_user_id);

