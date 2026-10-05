"""
Migration script for Canonical Skill Mapping schema in PostgreSQL.

Ensures that canonical_skills, skill_aliases, data_sources, skills,
and career_skills tables align with SQLAlchemy models without breaking
existing data or making foreign keys mandatory.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import create_app
from extensions import db
from sqlalchemy import text


def run_migration():
    app = create_app()

    with app.app_context():
        print("Starting PostgreSQL schema migration for canonical skill mapping...")

        with db.engine.connect() as conn:
            # 1. Update data_sources table
            print("Migrating data_sources table...")
            conn.execute(text("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='data_sources' AND column_name='name'
                    ) THEN
                        ALTER TABLE data_sources RENAME COLUMN name TO source_name;
                    END IF;
                    
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='data_sources' AND column_name='source_version'
                    ) THEN
                        ALTER TABLE data_sources ADD COLUMN source_version VARCHAR(50);
                    END IF;
                END $$;
            """))

            conn.execute(text("""
                UPDATE data_sources SET source_version = '31.0' WHERE source_name = 'O*NET' AND source_version IS NULL;
                UPDATE data_sources SET source_version = '1.2.1' WHERE source_name = 'ESCO' AND source_version IS NULL;
                UPDATE data_sources SET source_version = '1.0' WHERE source_name = 'NSDC' AND source_version IS NULL;
            """))

            conn.execute(text("""
                INSERT INTO data_sources (source_name, source_version, source_type, description)
                VALUES ('PROTOTYPE', '1.0', 'In-house Catalog', 'Curated IT benchmark skills for initial career tracks')
                ON CONFLICT (source_name) DO NOTHING;
            """))

            # 2. Update canonical_skills table
            print("Migrating canonical_skills table...")
            conn.execute(text("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='canonical_skills' AND column_name='name'
                    ) THEN
                        ALTER TABLE canonical_skills RENAME COLUMN name TO canonical_name;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='canonical_skills' AND column_name='category'
                    ) THEN
                        ALTER TABLE canonical_skills RENAME COLUMN category TO skill_type;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='canonical_skills' AND column_name='updated_at'
                    ) THEN
                        ALTER TABLE canonical_skills ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    END IF;
                END $$;
            """))

            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'canonical_skills_canonical_name_key'
                    ) THEN
                        ALTER TABLE canonical_skills ADD CONSTRAINT canonical_skills_canonical_name_key UNIQUE (canonical_name);
                    END IF;
                END $$;
            """))

            # 3. Update skill_aliases table
            print("Migrating skill_aliases table...")
            conn.execute(text("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='skill_aliases' AND column_name='skill_id'
                    ) THEN
                        ALTER TABLE skill_aliases RENAME COLUMN skill_id TO canonical_skill_id;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='skill_aliases' AND column_name='alias'
                    ) THEN
                        ALTER TABLE skill_aliases RENAME COLUMN alias TO alias_name;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='skill_aliases' AND column_name='normalized_alias'
                    ) THEN
                        ALTER TABLE skill_aliases ADD COLUMN normalized_alias VARCHAR(200);
                    END IF;
                END $$;
            """))

            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes WHERE indexname = 'ix_skill_aliases_normalized_alias'
                    ) THEN
                        CREATE INDEX ix_skill_aliases_normalized_alias ON skill_aliases (normalized_alias);
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'uq_canonical_skill_normalized_alias'
                    ) THEN
                        IF EXISTS (
                            SELECT 1 FROM pg_constraint WHERE conname = 'skill_aliases_unique'
                        ) THEN
                            ALTER TABLE skill_aliases DROP CONSTRAINT skill_aliases_unique;
                        END IF;
                        ALTER TABLE skill_aliases ADD CONSTRAINT uq_canonical_skill_normalized_alias UNIQUE (canonical_skill_id, normalized_alias);
                    END IF;
                END $$;
            """))

            # 4. Update skills table (nullable canonical_skill_id)
            print("Migrating skills table (adding nullable canonical_skill_id)...")
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='skills' AND column_name='canonical_skill_id'
                    ) THEN
                        ALTER TABLE skills ADD COLUMN canonical_skill_id INTEGER NULL;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'fk_skills_canonical_skill'
                    ) THEN
                        ALTER TABLE skills ADD CONSTRAINT fk_skills_canonical_skill 
                        FOREIGN KEY (canonical_skill_id) REFERENCES canonical_skills(id) ON DELETE SET NULL;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes WHERE indexname = 'ix_skills_canonical_skill_id'
                    ) THEN
                        CREATE INDEX ix_skills_canonical_skill_id ON skills (canonical_skill_id);
                    END IF;
                END $$;
            """))

            # 5. Update career_skills table (nullable canonical_skill_id)
            print("Migrating career_skills table (adding nullable canonical_skill_id)...")
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='career_skills' AND column_name='canonical_skill_id'
                    ) THEN
                        ALTER TABLE career_skills ADD COLUMN canonical_skill_id INTEGER NULL;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'fk_career_skills_canonical_skill'
                    ) THEN
                        ALTER TABLE career_skills ADD CONSTRAINT fk_career_skills_canonical_skill 
                        FOREIGN KEY (canonical_skill_id) REFERENCES canonical_skills(id) ON DELETE SET NULL;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes WHERE indexname = 'ix_career_skills_canonical_skill_id'
                    ) THEN
                        CREATE INDEX ix_career_skills_canonical_skill_id ON career_skills (canonical_skill_id);
                    END IF;
                END $$;
            """))

            conn.commit()
            print("PostgreSQL schema migration completed successfully!")


if __name__ == "__main__":
    run_migration()
