"""empty message

Revision ID: ebb293f66e75
Revises: 93c39ffa175c
Create Date: 2024-05-24 16:52:16.724878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebb293f66e75'
down_revision = '93c39ffa175c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('empresa')
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=250), nullable=False))
        batch_op.drop_column('nombre')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nombre', sa.VARCHAR(length=250), autoincrement=False, nullable=False))
        batch_op.drop_column('name')

    op.create_table('empresa',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=250), autoincrement=False, nullable=False),
    sa.Column('ciudad', sa.VARCHAR(length=250), autoincrement=False, nullable=False),
    sa.Column('slogan', sa.VARCHAR(length=250), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='empresa_pkey')
    )
    # ### end Alembic commands ###
