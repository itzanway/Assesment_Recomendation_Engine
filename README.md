# SHL Assessment Recommendation Engine

An intelligent recommendation engine for SHL's assessment product catalogue. This system helps users find the most suitable assessments based on job roles, required competencies, use cases, and other criteria.

## Features

- **Smart Recommendations**: Content-based filtering algorithm that scores assessments based on multiple criteria
- **Flexible Search**: Search by role, competencies, use case, assessment type, duration, difficulty, and language
- **Multiple Interfaces**: Both CLI and REST API interfaces available
- **Comprehensive Catalogue**: Includes 12+ SHL assessment products with detailed metadata

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

#### Basic Examples

```bash
# Find assessments for a manager role
python app.py --role manager

# Find cognitive assessments for hiring
python app.py --type cognitive --use-case hiring

# Find assessments with specific competencies
python app.py --competencies leadership communication --role manager

# Find quick assessments (under 30 minutes)
python app.py --max-duration 30

# Get detailed output
python app.py --role sales --verbose

# List all available assessments
python app.py --list-all

# Search assessments by name
python app.py --search "personality"

# Show details for a specific assessment
python app.py --show OPQ32
```

#### Advanced Examples

```bash
# Find intermediate difficulty assessments for development use case
python app.py --use-case development --difficulty intermediate --top-n 10

# Find assessments in Spanish
python app.py --language es --role manager

# Exclude specific assessments
python app.py --role manager --exclude OPQ32 G+
```

### REST API + Web UI

Start the API server:

```bash
python api.py
```

The API will be available at `http://localhost:5000`.

- Web UI: `http://localhost:5000/ui` (opens automatically when the server starts)
- API Docs (JSON): `http://localhost:5000/`

#### API Endpoints

**Health Check**
```bash
GET /health
```

**List All Assessments**
```bash
GET /assessments
```

**Get Specific Assessment**
```bash
GET /assessments/{assessment_id}
```

**Search Assessments**
```bash
GET /assessments/search?q=personality
```

**Get Recommendations (POST)**
```bash
POST /recommendations
Content-Type: application/json

{
  "target_role": "manager",
  "competencies": ["leadership", "communication"],
  "use_case": "hiring",
  "top_n": 5
}
```

**Get Recommendations (GET)**
```bash
GET /recommendations?target_role=manager&competencies=leadership&competencies=communication&use_case=hiring&top_n=5
```

#### Example API Usage

```bash
# Using curl
curl -X POST http://localhost:5000/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "target_role": "sales",
    "use_case": "hiring",
    "top_n": 3
  }'

# Using GET request
curl "http://localhost:5000/recommendations?target_role=sales&use_case=hiring&top_n=3"
```

## Recommendation Algorithm

The recommendation engine uses a weighted scoring system:

- **Target Role Matching** (30%): Matches assessments to specific job roles
- **Competencies Matching** (25%): Scores based on overlap with required competencies
- **Use Case Matching** (20%): Prioritizes assessments suitable for the intended use case
- **Assessment Type** (10%): Filters by assessment type (cognitive, personality, etc.)
- **Duration** (5%): Considers time constraints
- **Difficulty Level** (5%): Matches difficulty requirements
- **Language** (5%): Ensures language availability

## Product Catalogue

The catalogue includes assessments such as:

- **OPQ32**: Occupational Personality Questionnaire
- **G+**: General Ability Test
- **SJT-Manager**: Situational Judgment Test for Management
- **Verify-IT**: Quick cognitive test for entry-level
- **MQsales**: Motivational Questionnaire for Sales
- **DOP-i**: Development Outlook Profile
- And more...

Each assessment includes metadata about:
- Type and category
- Duration
- Target roles
- Competencies measured
- Use cases
- Difficulty level
- Available languages

## Project Structure

```
.
├── product_catalogue.json    # SHL assessment product catalogue
├── recommendation_engine.py  # Core recommendation engine logic
├── app.py                    # CLI application
├── api.py                    # REST API server
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Customization

### Adding New Assessments

Edit `product_catalogue.json` to add new assessments. Each assessment should include:

```json
{
  "id": "ASSESSMENT_ID",
  "name": "Assessment Name",
  "type": "cognitive|personality|situational|motivation|development|feedback",
  "category": "ability|behavioral",
  "duration_minutes": 30,
  "target_roles": ["role1", "role2"],
  "competencies": ["competency1", "competency2"],
  "use_cases": ["hiring", "development"],
  "difficulty_level": "beginner|intermediate|advanced",
  "languages": ["en", "es"],
  "description": "Assessment description"
}
```

### Modifying Scoring Weights

Edit the `_calculate_match_score` method in `recommendation_engine.py` to adjust scoring weights.

## License

This project is provided as-is for demonstration purposes.

## Support

For questions or issues, please refer to the code documentation or contact your SHL representative.

