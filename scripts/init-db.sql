-- CoCo Database Initialization Script
-- Creates schema for healthcare AI platform

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS coco;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS mlflow;

-- Set search path
SET search_path TO coco, public;

-- ============================================================================
-- PATIENT DATA TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS coco.patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(64) UNIQUE NOT NULL,
    demographics JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_patients_external_id ON coco.patients(external_id);
CREATE INDEX idx_patients_demographics ON coco.patients USING GIN(demographics);

CREATE TABLE IF NOT EXISTS coco.conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES coco.patients(id) ON DELETE CASCADE,
    icd10_code VARCHAR(16) NOT NULL,
    description TEXT,
    onset_date DATE,
    status VARCHAR(32) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conditions_patient ON coco.conditions(patient_id);
CREATE INDEX idx_conditions_code ON coco.conditions(icd10_code);

CREATE TABLE IF NOT EXISTS coco.observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES coco.patients(id) ON DELETE CASCADE,
    loinc_code VARCHAR(16) NOT NULL,
    value DECIMAL(12,4),
    unit VARCHAR(32),
    effective_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_observations_patient ON coco.observations(patient_id);
CREATE INDEX idx_observations_code ON coco.observations(loinc_code);
CREATE INDEX idx_observations_date ON coco.observations(effective_date);

-- ============================================================================
-- CARE GAP TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS coco.care_gaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES coco.patients(id) ON DELETE CASCADE,
    gap_type VARCHAR(32) NOT NULL,
    gap_name VARCHAR(256) NOT NULL,
    guideline_source VARCHAR(64),
    due_date DATE,
    priority VARCHAR(16) DEFAULT 'medium',
    status VARCHAR(32) DEFAULT 'open',
    closed_date DATE,
    closed_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_care_gaps_patient ON coco.care_gaps(patient_id);
CREATE INDEX idx_care_gaps_status ON coco.care_gaps(status);
CREATE INDEX idx_care_gaps_priority ON coco.care_gaps(priority);

-- ============================================================================
-- READMISSION PREDICTION TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS coco.readmission_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES coco.patients(id) ON DELETE CASCADE,
    encounter_id VARCHAR(64),
    risk_score DECIMAL(5,4) NOT NULL,
    risk_tier VARCHAR(16) NOT NULL,
    confidence_lower DECIMAL(5,4),
    confidence_upper DECIMAL(5,4),
    contributing_factors JSONB DEFAULT '[]',
    model_version VARCHAR(32) NOT NULL,
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_predictions_patient ON coco.readmission_predictions(patient_id);
CREATE INDEX idx_predictions_risk ON coco.readmission_predictions(risk_tier);
CREATE INDEX idx_predictions_date ON coco.readmission_predictions(predicted_at);

-- ============================================================================
-- CLINICAL SUMMARIZATION TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS coco.clinical_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES coco.patients(id) ON DELETE CASCADE,
    summary_type VARCHAR(32) NOT NULL,
    time_range VARCHAR(32) NOT NULL,
    summary_text TEXT NOT NULL,
    key_findings JSONB DEFAULT '[]',
    citations JSONB DEFAULT '[]',
    phi_audit JSONB DEFAULT '{}',
    rag_metrics JSONB DEFAULT '{}',
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_summaries_patient ON coco.clinical_summaries(patient_id);
CREATE INDEX idx_summaries_type ON coco.clinical_summaries(summary_type);

-- ============================================================================
-- AUDIT TABLES (HIPAA Compliance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(64) NOT NULL,
    component VARCHAR(64) NOT NULL,
    operation VARCHAR(128) NOT NULL,
    user_id VARCHAR(128),
    patient_id UUID,
    details JSONB DEFAULT '{}',
    previous_hash VARCHAR(64),
    hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_type ON audit.events(event_type);
CREATE INDEX idx_audit_patient ON audit.events(patient_id);
CREATE INDEX idx_audit_date ON audit.events(created_at);
CREATE INDEX idx_audit_component ON audit.events(component);

-- Audit events are immutable - prevent updates and deletes
CREATE OR REPLACE FUNCTION audit.prevent_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit events are immutable and cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_audit_update
    BEFORE UPDATE ON audit.events
    FOR EACH ROW
    EXECUTE FUNCTION audit.prevent_modification();

CREATE TRIGGER prevent_audit_delete
    BEFORE DELETE ON audit.events
    FOR EACH ROW
    EXECUTE FUNCTION audit.prevent_modification();

-- ============================================================================
-- GOVERNANCE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS coco.phase_gates (
    id SERIAL PRIMARY KEY,
    phase_number INTEGER UNIQUE NOT NULL,
    phase_name VARCHAR(64) NOT NULL,
    quarter VARCHAR(4) NOT NULL,
    status VARCHAR(32) DEFAULT 'not_started',
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by VARCHAR(128),
    evidence_pack_id VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS coco.cost_telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(64) NOT NULL,
    metric_value DECIMAL(12,6) NOT NULL,
    threshold DECIMAL(12,6),
    owner VARCHAR(128),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_telemetry_metric ON coco.cost_telemetry(metric_name);
CREATE INDEX idx_telemetry_date ON coco.cost_telemetry(recorded_at);

CREATE TABLE IF NOT EXISTS coco.kill_criteria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    criteria_name VARCHAR(128) NOT NULL,
    description TEXT,
    threshold_expression TEXT NOT NULL,
    is_triggered BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMP WITH TIME ZONE,
    owner VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- FEATURE STORE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS coco.feature_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_name VARCHAR(128) UNIQUE NOT NULL,
    feature_group VARCHAR(64) NOT NULL,
    data_type VARCHAR(32) NOT NULL,
    description TEXT,
    importance DECIMAL(5,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS coco.feature_values (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES coco.patients(id) ON DELETE CASCADE,
    feature_name VARCHAR(128) REFERENCES coco.feature_definitions(feature_name),
    value_numeric DECIMAL(12,6),
    value_text TEXT,
    effective_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_features_patient ON coco.feature_values(patient_id);
CREATE INDEX idx_features_name ON coco.feature_values(feature_name);
CREATE INDEX idx_features_timestamp ON coco.feature_values(effective_timestamp);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_patients_timestamp
    BEFORE UPDATE ON coco.patients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_care_gaps_timestamp
    BEFORE UPDATE ON coco.care_gaps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_phase_gates_timestamp
    BEFORE UPDATE ON coco.phase_gates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert phase gates
INSERT INTO coco.phase_gates (phase_number, phase_name, quarter, status) VALUES
(1, 'Ontology', 'Q1', 'approved'),
(2, 'Problem Space', 'Q1', 'approved'),
(3, 'Discovery', 'Q1', 'approved'),
(4, 'Alignment & Design', 'Q2', 'approved'),
(5, 'Integration', 'Q2', 'approved'),
(6, 'Build', 'Q2', 'approved'),
(7, 'Validation', 'Q3', 'approved'),
(8, 'Pre-Production', 'Q3', 'approved'),
(9, 'Hypercare', 'Q3', 'approved'),
(10, 'Production', 'Q4', 'approved'),
(11, 'Reliability', 'Q4', 'in_progress'),
(12, 'Continuous Improvement', 'Q4', 'not_started')
ON CONFLICT (phase_number) DO NOTHING;

-- Insert feature definitions
INSERT INTO coco.feature_definitions (feature_name, feature_group, data_type, description, importance) VALUES
('prior_admissions_12m', 'utilization', 'integer', 'Hospital admissions in past 12 months', 0.142),
('length_of_stay', 'clinical', 'integer', 'Current stay length in days', 0.098),
('charlson_comorbidity_index', 'clinical', 'integer', 'Charlson Comorbidity Index', 0.087),
('ed_visits_6m', 'utilization', 'integer', 'ED visits in past 6 months', 0.076),
('polypharmacy_count', 'clinical', 'integer', 'Number of active medications', 0.065),
('social_support_score', 'social', 'decimal', 'Social determinants score', 0.048),
('age', 'demographic', 'integer', 'Patient age in years', 0.042)
ON CONFLICT (feature_name) DO NOTHING;

-- Insert kill criteria
INSERT INTO coco.kill_criteria (criteria_name, description, threshold_expression, owner) VALUES
('ROI Collapse', 'Cost per inference exceeds value for 2 months', 'cost_value_ratio > 1.0 for 60 days', 'CTO + CFO'),
('Error Cost Spike', 'Weighted error cost exceeds $50K/month', 'error_cost_monthly > 50000', 'CTO'),
('Compliance Gap', 'Any material compliance gap detected', 'compliance_gap = true', 'General Counsel'),
('Model Decay', 'Accuracy drift exceeds 15%', 'accuracy_decay > 0.15', 'ML Lead'),
('PHI Exposure', 'Any confirmed PHI exposure', 'phi_exposure = true', 'CISO')
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT USAGE ON SCHEMA coco TO PUBLIC;
GRANT USAGE ON SCHEMA audit TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA coco TO PUBLIC;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA audit TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA coco TO PUBLIC;

-- Summary
DO $$
BEGIN
    RAISE NOTICE 'CoCo database initialization complete!';
    RAISE NOTICE 'Created schemas: coco, audit, mlflow';
    RAISE NOTICE 'Created tables for patients, care gaps, predictions, summaries, audit, governance, features';
END $$;
