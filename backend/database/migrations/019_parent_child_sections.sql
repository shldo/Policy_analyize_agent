-- Additive transition: existing children deliberately retain NULL section_id.
BEGIN;
CREATE TABLE IF NOT EXISTS document_sections (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parent_section_id uuid,
    section_level integer NOT NULL,
    section_number text,
    section_title text NOT NULL,
    section_path jsonb NOT NULL DEFAULT '[]',
    text text NOT NULL,
    page_start integer NOT NULL,
    page_end integer NOT NULL,
    token_count integer NOT NULL,
    sequence_index integer NOT NULL,
    metadata_json jsonb NOT NULL DEFAULT '{}',
    UNIQUE(document_id, id),
    UNIQUE(document_id, sequence_index),
    FOREIGN KEY(document_id, parent_section_id)
        REFERENCES document_sections(document_id, id) DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX IF NOT EXISTS idx_document_sections_parent ON document_sections(parent_section_id);
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS section_id uuid;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS child_index integer;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_chunk_section_document') THEN
        ALTER TABLE document_chunks ADD CONSTRAINT fk_chunk_section_document
            FOREIGN KEY(document_id, section_id) REFERENCES document_sections(document_id, id);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_document_chunks_section ON document_chunks(section_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_chunks_child_index
    ON document_chunks(section_id, child_index) WHERE section_id IS NOT NULL;
COMMIT;
