-- Initialize database with required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create indexes for better performance
-- These will be created by Alembic migrations, but including here for reference

-- Tasks table indexes
-- CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
-- CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
-- CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
-- CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_at ON tasks(scheduled_at);

-- Workers table indexes
-- CREATE INDEX IF NOT EXISTS idx_workers_status ON workers(status);
-- CREATE INDEX IF NOT EXISTS idx_workers_last_heartbeat ON workers(last_heartbeat);
-- CREATE INDEX IF NOT EXISTS idx_workers_current_task_id ON workers(current_task_id);

-- Task results table indexes
-- CREATE INDEX IF NOT EXISTS idx_task_results_task_id ON task_results(task_id);
-- CREATE INDEX IF NOT EXISTS idx_task_results_worker_id ON task_results(worker_id);
-- CREATE INDEX IF NOT EXISTS idx_task_results_status ON task_results(status);
-- CREATE INDEX IF NOT EXISTS idx_task_results_completed_at ON task_results(completed_at);