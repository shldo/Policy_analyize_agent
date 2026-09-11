-- Additive chat status contract.  Nullable columns preserve old history:
-- missing values mean unknown/not_assessed, never complete.
ALTER TABLE public.chat_messages
    ADD COLUMN IF NOT EXISTS generation_allowed boolean,
    ADD COLUMN IF NOT EXISTS coverage_status text,
    ADD COLUMN IF NOT EXISTS answer_status text;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chat_messages_coverage_status_check'
    ) THEN
        ALTER TABLE public.chat_messages
            ADD CONSTRAINT chat_messages_coverage_status_check
            CHECK (coverage_status IS NULL OR coverage_status IN
                ('not_assessed', 'partial', 'complete', 'no_context'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chat_messages_answer_status_check'
    ) THEN
        ALTER TABLE public.chat_messages
            ADD CONSTRAINT chat_messages_answer_status_check
            CHECK (answer_status IS NULL OR answer_status IN
                ('pending', 'streaming', 'generated', 'withheld', 'error', 'unknown'));
    END IF;
END $$;
