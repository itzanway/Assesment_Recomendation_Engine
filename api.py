
from flask import Flask, request, jsonify, render_template
from recommendation_engine import AssessmentRecommendationEngine, RecommendationCriteria, create_recommendation_criteria
import os
import webbrowser
from typing import Optional

import requests
from bs4 import BeautifulSoup

from gemini_helper import generate_explanation

app = Flask(__name__, static_folder="static", template_folder="templates")

# Initialize the recommendation engine
engine = AssessmentRecommendationEngine()


@app.route('/', methods=['GET'])
def index():
    """API root endpoint with documentation"""
    return jsonify({
        'service': 'SHL Assessment Recommendation Engine API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'GET /': 'API documentation (this endpoint)',
            'GET /ui': 'Web UI for trying the engine',
            'GET /health': 'Health check endpoint',
            'GET /assessments': 'List all assessments in the catalogue',
            'GET /assessments/<id>': 'Get a specific assessment by ID',
            'GET /assessments/search?q=<term>': 'Search assessments by name or description',
            'GET /recommendations': 'Get recommendations via query parameters (structured filters)',
            'POST /recommendations': 'Get recommendations via JSON body (structured filters)',
            'POST /text_recommendations': 'Get recommendations using natural language or job description text',
            'POST /explanations': 'Get Gemini-generated explanation for text-based recommendations'
        },
        'examples': {
            'ui': '/ui',
            'list_all_assessments': '/assessments',
            'get_assessment': '/assessments/OPQ32',
            'search': '/assessments/search?q=personality',
            'recommendations_get': '/recommendations?target_role=manager&use_case=hiring&top_n=5',
            'recommendations_post': {
                'url': '/recommendations',
                'method': 'POST',
                'body': {
                    'target_role': 'manager',
                    'competencies': ['leadership', 'communication'],
                    'use_case': 'hiring',
                    'top_n': 5
                }
            }
        },
        'parameters': {
            'target_role': 'Job role (e.g., manager, sales, engineer)',
            'competencies': 'List of required competencies',
            'use_case': 'hiring, development, promotion, coaching, succession_planning, team_building',
            'assessment_type': 'cognitive, personality, situational, motivation, development, feedback',
            'max_duration_minutes': 'Maximum assessment duration in minutes',
            'difficulty_level': 'beginner, intermediate, advanced',
            'language': 'Language code (e.g., en, es, fr)',
            'exclude_ids': 'List of assessment IDs to exclude',
            'top_n': 'Number of recommendations to return (default: 5 for structured, 5–10 for text-based)'
        }
    }), 200


@app.route('/ui', methods=['GET'])
def ui():
    """Serve the interactive UI"""
    return render_template('ui.html')


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'SHL Assessment Recommendation Engine'}), 200


@app.route('/assessments', methods=['GET'])
def list_assessments():
    """Get all assessments in the catalogue"""
    assessments = engine.get_all_assessments()
    return jsonify({
        'count': len(assessments),
        'assessments': assessments
    }), 200


@app.route('/assessments/<assessment_id>', methods=['GET'])
def get_assessment(assessment_id):
    """Get a specific assessment by ID"""
    assessment = engine.get_assessment_by_id(assessment_id)
    if assessment:
        return jsonify(assessment), 200
    return jsonify({'error': f'Assessment {assessment_id} not found'}), 404


@app.route('/assessments/search', methods=['GET'])
def search_assessments():
    """Search assessments by name or description"""
    search_term = request.args.get('q', '')
    if not search_term:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    results = engine.search_by_name(search_term)
    return jsonify({
        'count': len(results),
        'assessments': results
    }), 200


@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    """Get assessment recommendations based on criteria"""
    try:
        data = request.get_json() or {}
        
        # Extract parameters
        criteria = create_recommendation_criteria(
            target_role=data.get('target_role'),
            competencies=data.get('competencies'),
            use_case=data.get('use_case'),
            assessment_type=data.get('assessment_type'),
            max_duration_minutes=data.get('max_duration_minutes'),
            difficulty_level=data.get('difficulty_level'),
            language=data.get('language'),
            exclude_ids=data.get('exclude_ids')
        )
        
        top_n = data.get('top_n', 5)
        
        # Get recommendations
        recommendations = engine.recommend(criteria, top_n=top_n)
        
        return jsonify({
            'count': len(recommendations),
            'recommendations': recommendations,
            'criteria': {
                'target_role': criteria.target_role,
                'competencies': criteria.competencies,
                'use_case': criteria.use_case,
                'assessment_type': criteria.assessment_type,
                'max_duration_minutes': criteria.max_duration_minutes,
                'difficulty_level': criteria.difficulty_level,
                'language': criteria.language
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/recommendations', methods=['GET'])
def get_recommendations_get():
    """Get recommendations via GET request (query parameters)"""
    try:
        criteria = create_recommendation_criteria(
            target_role=request.args.get('target_role'),
            competencies=request.args.getlist('competencies'),
            use_case=request.args.get('use_case'),
            assessment_type=request.args.get('assessment_type'),
            max_duration_minutes=int(request.args.get('max_duration_minutes')) if request.args.get('max_duration_minutes') else None,
            difficulty_level=request.args.get('difficulty_level'),
            language=request.args.get('language'),
            exclude_ids=request.args.getlist('exclude_ids')
        )
        
        top_n = int(request.args.get('top_n', 5))
        
        recommendations = engine.recommend(criteria, top_n=top_n)
        
        return jsonify({
            'count': len(recommendations),
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


def _fetch_text_from_url(url: str) -> Optional[str]:
    """Fetch and extract visible text from a JD URL."""
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        main = soup.find("main")
        if main:
            return main.get_text(" ", strip=True)
        return soup.get_text(" ", strip=True)
    except Exception:
        return None


@app.route('/text_recommendations', methods=['POST'])
def get_text_recommendations():
    """
    Get assessment recommendations from natural language / JD text.

    JSON body:
    {
      "query": "free text or JD",
      "jd_url": "https://job.example.com/posting",  # optional
      "top_n": 10
    }
    """
    try:
        data = request.get_json() or {}
        query_text = data.get("query", "") or ""
        jd_url = data.get("jd_url")
        top_n = int(data.get("top_n", 10))

        text_parts = []
        if query_text.strip():
            text_parts.append(query_text.strip())

        if jd_url:
            jd_text = _fetch_text_from_url(jd_url)
            if jd_text:
                text_parts.append(jd_text)

        if not text_parts:
            return jsonify({'error': 'Provide at least "query" or "jd_url" with readable text.'}), 400

        combined_text = "\n\n".join(text_parts)

        recommendations = engine.recommend_from_text(combined_text, top_n=top_n)

        # Ensure each recommendation has the fields required by the assignment
        simplified = []
        for r in recommendations:
            simplified.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "url": r.get("url"),
                "similarity": r.get("similarity", 0.0),
            })

        return jsonify({
            "count": len(simplified),
            "recommendations": simplified
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/explanations', methods=['POST'])
def get_explanations():
    """
    Get Gemini-generated explanation for text-based recommendations.

    JSON body:
    {
      "query": "free text or JD",
      "jd_url": "https://job.example.com/posting",  # optional
      "top_n": 5-10  # optional, defaults to 5–10 window like text_recommendations
    }

    This endpoint first obtains recommendations via the same logic as
    /text_recommendations, then calls Gemini to explain why they fit.
    """
    try:
        data = request.get_json() or {}
        query_text = data.get("query", "") or ""
        jd_url = data.get("jd_url")
        top_n = int(data.get("top_n", 10))

        # Clamp to 5–10
        if top_n < 5:
            top_n = 5
        if top_n > 10:
            top_n = 10

        text_parts = []
        if query_text.strip():
            text_parts.append(query_text.strip())

        if jd_url:
            jd_text = _fetch_text_from_url(jd_url)
            if jd_text:
                text_parts.append(jd_text)

        if not text_parts:
            return jsonify({'error': 'Provide at least "query" or "jd_url" with readable text.'}), 400

        combined_text = "\n\n".join(text_parts)

        # Get recommendations from text
        recommendations_full = engine.recommend_from_text(combined_text, top_n=top_n)
        recommendations = [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "url": r.get("url"),
                "similarity": r.get("similarity", 0.0),
                "description": r.get("description", ""),
            }
            for r in recommendations_full
        ]

        # Ask Gemini for an explanation
        explanation = generate_explanation(combined_text, recommendations)

        return jsonify({
            "count": len(recommendations),
            "recommendations": recommendations,
            "explanation": explanation,
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'Please check the API documentation at /',
        'available_endpoints': [
            '/',
            '/health',
            '/assessments',
            '/assessments/<id>',
            '/assessments/search',
            '/recommendations'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': str(error) if app.debug else 'An error occurred processing your request'
    }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    base_url = f"http://127.0.0.1:{port}"
    print(f"\n{'='*80}")
    print("SHL Assessment Recommendation Engine API")
    print(f"{'='*80}")
    print(f"API Documentation: {base_url}/")
    print(f"Web UI: {base_url}/ui")
    print(f"Health Check: {base_url}/health")
    print(f"All Assessments: {base_url}/assessments")
    print(f"{'='*80}\n")
    # Open browser only on the reloader main process to avoid double launches
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        try:
            webbrowser.open(f"{base_url}/ui")
        except Exception:
            pass
    app.run(host='0.0.0.0', port=port, debug=True)

