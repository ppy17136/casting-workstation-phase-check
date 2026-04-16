PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    project_type TEXT,
    customer_or_course TEXT,
    casting_method TEXT,
    material_code TEXT,
    status TEXT,
    owner TEXT,
    start_date TEXT,
    due_date TEXT,
    root_dir TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT
);

CREATE TABLE IF NOT EXISTS parts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    part_no TEXT,
    part_name TEXT NOT NULL,
    drawing_no TEXT,
    material_name TEXT,
    net_weight REAL,
    blank_weight REAL,
    length_mm REAL,
    width_mm REAL,
    height_mm REAL,
    max_wall_thickness REAL,
    min_wall_thickness REAL,
    production_qty INTEGER,
    quality_grade TEXT,
    heat_treatment TEXT,
    surface_requirement TEXT,
    internal_quality_requirement TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS materials (
    id TEXT PRIMARY KEY,
    material_code TEXT NOT NULL UNIQUE,
    material_name TEXT NOT NULL,
    category TEXT,
    density REAL,
    liquidus_temp REAL,
    solidus_temp REAL,
    pouring_temp_min REAL,
    pouring_temp_max REAL,
    shrinkage_ratio REAL,
    standard_ref TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT
);

CREATE TABLE IF NOT EXISTS process_schemes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    part_id TEXT NOT NULL,
    scheme_code TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    version_no TEXT NOT NULL,
    parent_scheme_id TEXT,
    scheme_status TEXT,
    mold_type TEXT,
    parting_method TEXT,
    pouring_position TEXT,
    gating_type TEXT,
    notes TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (part_id) REFERENCES parts(id),
    FOREIGN KEY (parent_scheme_id) REFERENCES process_schemes(id)
);

CREATE TABLE IF NOT EXISTS process_parameters (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    param_group TEXT NOT NULL,
    param_code TEXT NOT NULL,
    param_name TEXT NOT NULL,
    param_value TEXT,
    param_unit TEXT,
    value_type TEXT,
    source_type TEXT,
    source_ref TEXT,
    calc_formula TEXT,
    is_key_param INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (scheme_id) REFERENCES process_schemes(id)
);

CREATE TABLE IF NOT EXISTS casting_checks (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    check_item TEXT NOT NULL,
    check_result TEXT,
    risk_level TEXT,
    basis TEXT,
    suggestion TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (scheme_id) REFERENCES process_schemes(id)
);

CREATE TABLE IF NOT EXISTS cad_models (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    cad_system TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT,
    config_name TEXT,
    custom_props_json TEXT,
    last_sync_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (scheme_id) REFERENCES process_schemes(id)
);

CREATE TABLE IF NOT EXISTS cad_exports (
    id TEXT PRIMARY KEY,
    cad_model_id TEXT NOT NULL,
    export_type TEXT NOT NULL,
    export_path TEXT NOT NULL,
    export_status TEXT,
    snapshot_path TEXT,
    bridge_version TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (cad_model_id) REFERENCES cad_models(id)
);

CREATE TABLE IF NOT EXISTS simulation_jobs (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    job_code TEXT NOT NULL,
    job_name TEXT NOT NULL,
    solver TEXT,
    template_name TEXT,
    input_dir TEXT,
    output_dir TEXT,
    submit_time TEXT,
    finish_time TEXT,
    job_status TEXT,
    run_mode TEXT,
    operator TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (scheme_id) REFERENCES process_schemes(id)
);

CREATE TABLE IF NOT EXISTS simulation_parameters (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    param_code TEXT NOT NULL,
    param_name TEXT NOT NULL,
    param_value TEXT,
    param_unit TEXT,
    source_ref TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (job_id) REFERENCES simulation_jobs(id)
);

CREATE TABLE IF NOT EXISTS simulation_results (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    result_type TEXT NOT NULL,
    result_name TEXT NOT NULL,
    file_path TEXT,
    image_path TEXT,
    view_angle TEXT,
    legend_range TEXT,
    summary TEXT,
    is_baseline INTEGER DEFAULT 0,
    compare_group TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (job_id) REFERENCES simulation_jobs(id)
);

CREATE TABLE IF NOT EXISTS process_cards (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    card_no TEXT NOT NULL,
    template_name TEXT,
    docx_path TEXT,
    pdf_path TEXT,
    card_status TEXT,
    generated_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (scheme_id) REFERENCES process_schemes(id)
);

CREATE TABLE IF NOT EXISTS inspection_items (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    item_name TEXT NOT NULL,
    control_stage TEXT,
    control_method TEXT,
    acceptance_rule TEXT,
    risk_reason TEXT,
    linked_result_id TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (scheme_id) REFERENCES process_schemes(id),
    FOREIGN KEY (linked_result_id) REFERENCES simulation_results(id)
);

CREATE TABLE IF NOT EXISTS ai_suggestion_cards (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    job_id TEXT,
    title TEXT NOT NULL,
    suggestion_text TEXT NOT NULL,
    target_params_json TEXT,
    preconditions TEXT,
    risk_notice TEXT,
    confidence_score REAL,
    validation_status TEXT,
    human_review_status TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (scheme_id) REFERENCES process_schemes(id),
    FOREIGN KEY (job_id) REFERENCES simulation_jobs(id)
);

CREATE TABLE IF NOT EXISTS evidence_sources (
    id TEXT PRIMARY KEY,
    evidence_code TEXT NOT NULL UNIQUE,
    evidence_type TEXT NOT NULL,
    title TEXT NOT NULL,
    source_path TEXT NOT NULL,
    page_no TEXT,
    section_name TEXT,
    excerpt TEXT,
    hash_value TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT
);

CREATE TABLE IF NOT EXISTS suggestion_evidence_links (
    id TEXT PRIMARY KEY,
    suggestion_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    link_role TEXT,
    match_status TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT,
    FOREIGN KEY (suggestion_id) REFERENCES ai_suggestion_cards(id),
    FOREIGN KEY (evidence_id) REFERENCES evidence_sources(id)
);

CREATE TABLE IF NOT EXISTS approval_records (
    id TEXT PRIMARY KEY,
    biz_type TEXT NOT NULL,
    biz_id TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL,
    comment TEXT,
    reviewed_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id TEXT PRIMARY KEY,
    module_name TEXT NOT NULL,
    action_name TEXT NOT NULL,
    biz_type TEXT,
    biz_id TEXT,
    operator TEXT,
    before_json TEXT,
    after_json TEXT,
    result_status TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (
    id TEXT PRIMARY KEY,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    setting_group TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT
);

CREATE TABLE IF NOT EXISTS environment_checks (
    id TEXT PRIMARY KEY,
    machine_name TEXT,
    os_version TEXT,
    solidworks_found INTEGER,
    solidworks_version TEXT,
    procast_found INTEGER,
    procast_version TEXT,
    llm_mode TEXT,
    last_checked_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    updated_by TEXT,
    is_deleted INTEGER DEFAULT 0,
    remark TEXT
);

CREATE INDEX IF NOT EXISTS idx_projects_project_code
ON projects(project_code);

CREATE INDEX IF NOT EXISTS idx_process_schemes_project_part_version
ON process_schemes(project_id, part_id, version_no);

CREATE INDEX IF NOT EXISTS idx_process_parameters_scheme_param
ON process_parameters(scheme_id, param_code);

CREATE INDEX IF NOT EXISTS idx_simulation_jobs_scheme_status
ON simulation_jobs(scheme_id, job_status);

CREATE INDEX IF NOT EXISTS idx_simulation_results_job_type
ON simulation_results(job_id, result_type);

CREATE INDEX IF NOT EXISTS idx_ai_suggestion_cards_scheme_status
ON ai_suggestion_cards(scheme_id, validation_status, human_review_status);

CREATE INDEX IF NOT EXISTS idx_operation_logs_biz
ON operation_logs(biz_type, biz_id);
