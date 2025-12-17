"""
SHL Assessment Recommendation Engine - CLI Application

Command-line interface for the assessment recommendation engine.
"""

import argparse
import json
from recommendation_engine import AssessmentRecommendationEngine, RecommendationCriteria, create_recommendation_criteria


def print_recommendations(recommendations: list, verbose: bool = False):
    """Print recommendations in a formatted way"""
    if not recommendations:
        print("\nNo assessments found matching your criteria.")
        return
    
    print(f"\n{'='*80}")
    print(f"Found {len(recommendations)} recommendation(s):")
    print(f"{'='*80}\n")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['name']} ({rec['id']})")
        print(f"   Match Score: {rec['match_score']}%")
        print(f"   Type: {rec['type']} | Category: {rec['category']}")
        print(f"   Duration: {rec['duration_minutes']} minutes")
        print(f"   Difficulty: {rec['difficulty_level']}")
        
        if verbose:
            print(f"   Description: {rec.get('description', 'N/A')}")
            print(f"   Target Roles: {', '.join(rec.get('target_roles', []))}")
            print(f"   Competencies: {', '.join(rec.get('competencies', []))}")
            print(f"   Use Cases: {', '.join(rec.get('use_cases', []))}")
            print(f"   Languages: {', '.join(rec.get('languages', []))}")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description='SHL Assessment Recommendation Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
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
        """
    )
    
    parser.add_argument('--role', type=str, help='Target job role (e.g., manager, sales, engineer)')
    parser.add_argument('--competencies', nargs='+', help='Required competencies (e.g., leadership communication)')
    parser.add_argument('--use-case', type=str, choices=['hiring', 'development', 'promotion', 'coaching', 'succession_planning', 'team_building'],
                       help='Use case for the assessment')
    parser.add_argument('--type', type=str, choices=['cognitive', 'personality', 'situational', 'motivation', 'development', 'feedback'],
                       help='Assessment type')
    parser.add_argument('--max-duration', type=int, help='Maximum duration in minutes')
    parser.add_argument('--difficulty', type=str, choices=['beginner', 'intermediate', 'advanced'],
                       help='Difficulty level')
    parser.add_argument('--language', type=str, help='Language code (e.g., en, es, fr)')
    parser.add_argument('--exclude', nargs='+', help='Assessment IDs to exclude')
    parser.add_argument('--top-n', type=int, default=5, help='Number of recommendations to return (default: 5)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    parser.add_argument('--catalogue', type=str, default='product_catalogue.json',
                       help='Path to product catalogue JSON file')
    parser.add_argument('--list-all', action='store_true', help='List all available assessments')
    parser.add_argument('--search', type=str, help='Search assessments by name or description')
    parser.add_argument('--show', type=str, help='Show details for a specific assessment ID')
    
    args = parser.parse_args()
    
    try:
        engine = AssessmentRecommendationEngine(args.catalogue)
        
        # Handle special commands
        if args.list_all:
            assessments = engine.get_all_assessments()
            print(f"\nAll Available Assessments ({len(assessments)}):")
            print("="*80)
            for assessment in assessments:
                print(f"\n{assessment['id']}: {assessment['name']}")
                print(f"  Type: {assessment['type']} | Duration: {assessment['duration_minutes']} min")
            return
        
        if args.search:
            results = engine.search_by_name(args.search)
            print(f"\nSearch Results for '{args.search}':")
            print_recommendations(results, args.verbose)
            return
        
        if args.show:
            assessment = engine.get_assessment_by_id(args.show)
            if assessment:
                print(f"\nAssessment Details: {assessment['name']}")
                print("="*80)
                print(json.dumps(assessment, indent=2))
            else:
                print(f"\nAssessment '{args.show}' not found.")
            return
        
        # Create recommendation criteria
        criteria = create_recommendation_criteria(
            target_role=args.role,
            competencies=args.competencies,
            use_case=args.use_case,
            assessment_type=args.type,
            max_duration_minutes=args.max_duration,
            difficulty_level=args.difficulty,
            language=args.language,
            exclude_ids=args.exclude
        )
        
        # Get recommendations
        recommendations = engine.recommend(criteria, top_n=args.top_n)
        
        # Print results
        print_recommendations(recommendations, args.verbose)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

