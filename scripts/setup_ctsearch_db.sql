-- Clinical Trial Search Database Schema Setup
-- This script creates the ctsearch schema and all required tables for the enhanced clinical trial search functionality

-- Create schema for our enhanced search functionality
CREATE SCHEMA IF NOT EXISTS ctsearch;

-- Processing metadata table to track when trials were processed
CREATE TABLE ctsearch.processed_trials (
    nct_id VARCHAR(16) PRIMARY KEY REFERENCES ctgov.studies(nct_id),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_version INTEGER DEFAULT 1,
    successfully_processed BOOLEAN DEFAULT TRUE
);

-- Conditions - many-to-many relationship with comprehensive tagging
CREATE TABLE ctsearch.condition_tags (
    id SERIAL PRIMARY KEY,
    condition_name VARCHAR(255) NOT NULL,
    UNIQUE(condition_name)
);

CREATE TABLE ctsearch.trial_conditions (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(16) REFERENCES ctgov.studies(nct_id),
    condition_id INTEGER REFERENCES ctsearch.condition_tags(id),
    relevance_score INTEGER CHECK (relevance_score BETWEEN 1 AND 5),
    UNIQUE(nct_id, condition_id)
);

-- Treatment mechanisms
CREATE TABLE ctsearch.mechanism_categories (
    id SERIAL PRIMARY KEY,
    mechanism_name VARCHAR(255) NOT NULL,
    UNIQUE(mechanism_name)
);

CREATE TABLE ctsearch.trial_mechanisms (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(16) REFERENCES ctgov.studies(nct_id),
    mechanism_id INTEGER REFERENCES ctsearch.mechanism_categories(id),
    relevance_score INTEGER CHECK (relevance_score BETWEEN 1 AND 5),
    UNIQUE(nct_id, mechanism_id)
);

-- Treatment targets (genes, proteins, etc.)
CREATE TABLE ctsearch.treatment_targets (
    id SERIAL PRIMARY KEY,
    target_name VARCHAR(255) NOT NULL,
    target_type VARCHAR(50), -- "gene", "protein", "pathway", etc.
    UNIQUE(target_name)
);

CREATE TABLE ctsearch.trial_targets (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(16) REFERENCES ctgov.studies(nct_id),
    target_id INTEGER REFERENCES ctsearch.treatment_targets(id),
    UNIQUE(nct_id, target_id)
);

-- Disease stage relevance
CREATE TABLE ctsearch.disease_stages (
    id SERIAL PRIMARY KEY,
    stage_name VARCHAR(100) NOT NULL,
    UNIQUE(stage_name)
);

CREATE TABLE ctsearch.trial_stage_relevance (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(16) REFERENCES ctgov.studies(nct_id),
    stage_id INTEGER REFERENCES ctsearch.disease_stages(id),
    relevance_score INTEGER CHECK (relevance_score BETWEEN 1 AND 5),
    UNIQUE(nct_id, stage_id)
);

-- Simplified eligibility criteria
CREATE TABLE ctsearch.simplified_eligibility (
    nct_id VARCHAR(16) PRIMARY KEY REFERENCES ctgov.studies(nct_id),
    summary TEXT
);

-- Inclusion/exclusion criteria tags
CREATE TABLE ctsearch.criteria_tags (
    id SERIAL PRIMARY KEY,
    criteria_name VARCHAR(255) NOT NULL,
    criteria_type VARCHAR(20) CHECK (criteria_type IN ('inclusion', 'exclusion')),
    UNIQUE(criteria_name, criteria_type)
);

CREATE TABLE ctsearch.trial_criteria (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(16) REFERENCES ctgov.studies(nct_id),
    criteria_id INTEGER REFERENCES ctsearch.criteria_tags(id),
    UNIQUE(nct_id, criteria_id)
);

-- Location information
CREATE TABLE ctsearch.countries (
    id SERIAL PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL,
    region_name VARCHAR(100),
    UNIQUE(country_name)
);

CREATE TABLE ctsearch.trial_countries (
    id SERIAL PRIMARY KEY,
    nct_id VARCHAR(16) REFERENCES ctgov.studies(nct_id),
    country_id INTEGER REFERENCES ctsearch.countries(id),
    has_remote_option BOOLEAN DEFAULT FALSE,
    UNIQUE(nct_id, country_id)
);

-- Create indexes for efficient searching
CREATE INDEX idx_trial_conditions_nct_id ON ctsearch.trial_conditions(nct_id);
CREATE INDEX idx_trial_mechanisms_nct_id ON ctsearch.trial_mechanisms(nct_id);
CREATE INDEX idx_trial_targets_nct_id ON ctsearch.trial_targets(nct_id);
CREATE INDEX idx_trial_stage_relevance_nct_id ON ctsearch.trial_stage_relevance(nct_id);
CREATE INDEX idx_trial_criteria_nct_id ON ctsearch.trial_criteria(nct_id);
CREATE INDEX idx_trial_countries_nct_id ON ctsearch.trial_countries(nct_id);

-- Insert default disease stages
INSERT INTO ctsearch.disease_stages (stage_name) VALUES
('Early'), ('Locally Advanced'), ('Metastatic/Recurrent');
