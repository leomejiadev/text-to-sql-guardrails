"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
${imports if imports else ""}

# Identificadores que Alembic usa para construir el grafo de migraciones.
# No tocar a mano: `alembic revision` los genera.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Cambios a aplicar cuando se avanza el schema (`alembic upgrade`)."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Cambios que revierten `upgrade` (`alembic downgrade`)."""
    ${downgrades if downgrades else "pass"}
