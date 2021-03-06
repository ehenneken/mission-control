"""empty message

Revision ID: 531f091961cd
Revises: None
Create Date: 2015-08-25 15:01:31.723880

"""

# revision identifiers, used by Alembic.
revision = '531f091961cd'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('commit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('commit_hash', sa.String(), nullable=True),
    sa.Column('message', sa.String(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('author', sa.String(), nullable=True),
    sa.Column('repository', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('commit_hash')
    )
    op.create_table('build',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('commit_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('built', sa.Boolean(), nullable=True),
    sa.Column('pushed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['commit_id'], ['commit.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('build')
    op.drop_table('commit')
    ### end Alembic commands ###
