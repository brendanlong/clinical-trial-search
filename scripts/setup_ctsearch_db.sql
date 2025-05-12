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

-- Create indexes for efficient searching
CREATE INDEX idx_trial_conditions_nct_id ON ctsearch.trial_conditions(nct_id);
