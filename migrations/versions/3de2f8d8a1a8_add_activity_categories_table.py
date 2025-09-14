"""add activity categories table and migrate activities

Revision ID: 3de2f8d8a1a8
Revises: 509404444b3a
Create Date: 2025-09-12 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, text


# revision identifiers, used by Alembic.
revision = '3de2f8d8a1a8'
down_revision = '509404444b3a'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Create lookup table
    op.create_table(
        'activity_categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True, index=True),
    )

    # 2) Seed initial categories
    categories_tbl = table(
        'activity_categories',
        column('id', Integer),
        column('name', String(50)),
    )
    op.bulk_insert(
        categories_tbl,
        [
            {"name": "Run"},
            {"name": "Bike"},
            {"name": "Swim"},
            {"name": "Weight Training"},
            {"name": "Yoga"},
        ],
    )

    # 3) Add nullable category_id to activities
    op.add_column('activities', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_index('ix_activities_category_id', 'activities', ['category_id'])
    op.create_foreign_key(
        'fk_activities_category_id', 'activities', 'activity_categories', ['category_id'], ['id']
    )

    conn = op.get_bind()

    # 4) Backfill missing categories based on existing free-text entries
    # Insert any distinct categories from activities that don't exist yet
    conn.execute(text(
        """
        INSERT INTO activity_categories (name)
        SELECT DISTINCT a.category
        FROM activities a
        WHERE a.category IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM activity_categories c
              WHERE LOWER(c.name) = LOWER(a.category)
          )
        """
    ))

    # 5) Populate category_id on activities by matching names (case-insensitive)
    conn.execute(text(
        """
        UPDATE activities a
        SET category_id = c.id
        FROM activity_categories c
        WHERE LOWER(a.category) = LOWER(c.name)
        """
    ))

    # 6) Make category_id non-nullable now that it is filled
    op.alter_column('activities', 'category_id', nullable=False)

    # 7) Drop old free-text category column
    op.drop_column('activities', 'category')


def downgrade():
    # 1) Re-add old text category column as nullable
    op.add_column('activities', sa.Column('category', sa.String(length=20), nullable=True))

    conn = op.get_bind()

    # 2) Backfill text category from lookup
    conn.execute(text(
        """
        UPDATE activities a
        SET category = c.name
        FROM activity_categories c
        WHERE a.category_id = c.id
        """
    ))

    # 3) Make category non-nullable
    op.alter_column('activities', 'category', nullable=False)

    # 4) Drop FK and column
    op.drop_constraint('fk_activities_category_id', 'activities', type_='foreignkey')
    op.drop_index('ix_activities_category_id', table_name='activities')
    op.drop_column('activities', 'category_id')

    # 5) Drop lookup table
    op.drop_table('activity_categories')

