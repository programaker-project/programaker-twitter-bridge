from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)

metadata = MetaData()

TwitterUserRegistration = Table(
    "TWITTER_USER_REGISTRATION",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("twitter_token", String(256), unique=True),
    Column("twitter_token_secret", String(256), unique=True),
)

PlazaUsers = Table(
    "PLAZA_USERS",
    metadata,
    Column("id", String(36), unique=True),  # The ID straight from PrograMaker
)

PlazaUsersInTwitter = Table(
    "PLAZA_USERS_IN_TWITTER",
    metadata,
    Column("plaza_id", String(36), ForeignKey("PLAZA_USERS.id"), primary_key=True),
    Column(
        "twitter_id",
        Integer,
        ForeignKey("TWITTER_USER_REGISTRATION.id"),
        primary_key=True,
    ),
    __table_args__=(UniqueConstraint("plaza_id", "twitter_id")),
)

TwitterFollows = Table(
    "TWITTER_FOLLOWS",
    metadata,
    Column(
        "followed_id",
        Integer,
        ForeignKey("TWITTER_USER_REGISTRATION.id"),
        primary_key=True,
    ),
    Column("follower_id", BigInteger, primary_key=True),
)

LastTweetByUser = Table(
    "LAST_TWEET_BY_USER",
    metadata,
    Column("listener_id", String(36), ForeignKey("PLAZA_USERS.id"), primary_key=True),
    Column("listened_id", String(256), primary_key=True),  # Twitter handle
    Column("tweet_id", BigInteger),
)

LastTweetInUserTimeline = Table(
    "LAST_TWEET_IN_USER_TIMELINE",
    metadata,
    Column("listener_id", String(36), ForeignKey("PLAZA_USERS.id"), primary_key=True),
    Column("tweet_id", BigInteger),
)
