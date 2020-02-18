from sqlalchemy import Column, Integer, String, MetaData, Column, ForeignKey, UniqueConstraint, Table

metadata = MetaData()

LastTweetByUser = Table(
    'LAST_TWEET_BY_USER', metadata,
    Column('listener_id', String(256), primary_key=True),
    Column('listened_id', String(256), primary_key=True),
    Column('tweet_id', Integer))
