# AACT Database Structure

This document provides an overview of the AACT (Aggregate Analysis of ClinicalTrials.gov) database structure and identifies the tables and columns most relevant to our clinical trial search project.

## Overview

AACT is a PostgreSQL relational database containing data from ClinicalTrials.gov. The database follows a relational structure where:

- All clinical trials are stored in the central `studies` table
- Each trial has a unique identifier (`nct_id`)
- Related information is stored in separate tables linked via the `nct_id` foreign key
- The database is updated daily with new and modified trials from ClinicalTrials.gov

## Key Tables for Clinical Trial Search

### Core Tables

1. **ctgov.studies**
   - Central table containing core information about each clinical trial
   - Key columns:
     - `nct_id`: Primary identifier for each trial
     - `brief_title`: Short title of the study
     - `official_title`: Full official title
     - `phase`: Trial phase (PHASE1, PHASE2, etc.)
     - `overall_status`: Current status (RECRUITING, COMPLETED, etc.)
     - `study_type`: Type of study (e.g., INTERVENTIONAL, OBSERVATIONAL)
     - `enrollment`: Number of participants
     - `start_date`: When the trial began
     - `completion_date`: When the trial ended/will end

2. **ctgov.brief_summaries**
   - Contains concise descriptions of each trial
   - Key columns:
     - `nct_id`: Links to studies table
     - `description`: Brief summary text

3. **ctgov.detailed_descriptions**
   - Contains more detailed descriptions of each trial
   - Key columns:
     - `nct_id`: Links to studies table
     - `description`: Detailed description text

### Condition and Disease Information

4. **ctgov.conditions**
   - Lists conditions being studied in each trial
   - Key columns:
     - `nct_id`: Links to studies table
     - `name`: Name of the condition
     - `downcase_name`: Lowercase version for easier searching

5. **ctgov.browse_conditions**
   - Standardized MeSH terms for conditions
   - Key columns:
     - `nct_id`: Links to studies table
     - `mesh_term`: MeSH terminology for condition
     - `downcase_mesh_term`: Lowercase version for searching

### Eligibility and Criteria

6. **ctgov.eligibilities**
   - Contains eligibility criteria for trial participation
   - Key columns:
     - `nct_id`: Links to studies table
     - `criteria`: Full eligibility criteria text (inclusion/exclusion)
     - `gender`: Gender eligibility
     - `minimum_age`/`maximum_age`: Age range
     - `healthy_volunteers`: Whether healthy volunteers are accepted

### Intervention Information

7. **ctgov.interventions**
   - Details about interventions being tested
   - Key columns:
     - `nct_id`: Links to studies table
     - `intervention_type`: Type of intervention (drug, device, etc.)
     - `name`: Name of the intervention
     - `description`: Description of the intervention

8. **ctgov.design_groups**
   - Information about participant groups in the study
   - Useful for understanding trial structure

### Keywords and Categorization

9. **ctgov.keywords**
   - Keywords associated with each trial
   - Key columns:
     - `nct_id`: Links to studies table
     - `name`: Keyword
     - `downcase_name`: Lowercase version for searching

10. **ctgov.design_outcomes**
    - Information about trial outcomes being measured
    - Key columns:
      - `nct_id`: Links to studies table
      - `outcome_type`: Type of outcome (primary, secondary, etc.)
      - `measure`: What's being measured
      - `time_frame`: When it's measured

### Location and Sponsor Information

11. **ctgov.facilities**
    - Information about facilities where trials are conducted
    - Useful for location-based searching

12. **ctgov.sponsors**
    - Information about trial sponsors
    - Key columns:
      - `nct_id`: Links to studies table
      - `name`: Sponsor name
      - `agency_class`: Type of sponsor (industry, NIH, etc.)

13. **ctgov.countries**
    - Countries where trials are being conducted
    - Useful for geographic filtering

### Calculated and Derived Information

14. **ctgov.calculated_values**
    - Contains derived values that may be useful for analysis
    - Key columns:
      - `nct_id`: Links to studies table
      - `has_us_facility`: Whether the trial has US locations
      - `number_of_facilities`: Number of facilities involved
      - `were_results_reported`: Whether results were reported

## Using the Database for Clinical Trial Search

For our clinical trial search project, we should focus on:

1. **Basic Trial Information**:
   - `studies.nct_id`, `brief_title`, `official_title`, `phase`, `overall_status`

2. **Descriptions**:
   - `brief_summaries.description`, `detailed_descriptions.description`

3. **Conditions and Interventions**:
   - `conditions.name`, `browse_conditions.mesh_term`, `interventions.name`, `interventions.intervention_type`

4. **Eligibility**:
   - `eligibilities.criteria`, `eligibilities.gender`, `eligibilities.minimum_age`, `eligibilities.maximum_age`

5. **Keywords and Categorization**:
   - `keywords.name`, `design_outcomes.measure`

These tables and columns will provide the core data needed for our LLM tagging system to process and categorize trials effectively.

## Query Example

Here's an example query to retrieve basic information for trials related to a specific condition:

```sql
SELECT
  s.nct_id,
  s.brief_title,
  s.overall_status,
  s.phase,
  b.description as brief_summary,
  string_agg(DISTINCT c.name, ', ') as conditions,
  string_agg(DISTINCT i.name, ', ') as interventions
FROM
  ctgov.studies s
JOIN
  ctgov.brief_summaries b ON s.nct_id = b.nct_id
JOIN
  ctgov.conditions c ON s.nct_id = c.nct_id
LEFT JOIN
  ctgov.interventions i ON s.nct_id = i.nct_id
WHERE
  c.downcase_name LIKE '%diabetes%'
GROUP BY
  s.nct_id, s.brief_title, s.overall_status, s.phase, b.description
LIMIT 10;
```

This will provide a foundation for further development of our clinical trial search system.
