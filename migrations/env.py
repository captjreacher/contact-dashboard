from __future__ import with_statement
import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Adjust this path depending on your project layout
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# If your app folder 'src' isn't in sys.path by default, add it:
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import your Flask app factory and SQLAlchemy db instance
from src import create_app
from src.models.models import db

# This is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Create the Flask app and push application context so extensions are available
app = create_app()
app.app_context().push()

# Provide target metadata for 'autogenerate' support.
target_metadata = db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    by skipping the Engine creation we don't need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = app.config['SQLALCHEMY_DATABASE_URI']
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,  # Useful for SQLite batch mode migrations
    )

    with context.begin_transaction():
        context.run_migrations()
        
def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
        url=app.config['SQLALCHEMY_DATABASE_URI'],
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,  # Useful for SQLite batch mode migrations
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
