"""
Example usage of the SHL Assessment Recommendation Engine

This script demonstrates various use cases of the recommendation engine.
"""

from recommendation_engine import AssessmentRecommendationEngine, create_recommendation_criteria


def example_1_basic_recommendation():
    """Example 1: Basic recommendation for a manager role"""
    print("=" * 80)
    print("Example 1: Finding assessments for a Manager role")
    print("=" * 80)
    
    engine = AssessmentRecommendationEngine()
    criteria = create_recommendation_criteria(target_role="manager")
    recommendations = engine.recommend(criteria, top_n=3)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['name']} (Score: {rec['match_score']}%)")
        print(f"   Type: {rec['type']} | Duration: {rec['duration_minutes']} min")
    print()


def example_2_hiring_assessment():
    """Example 2: Finding assessments for hiring a sales person"""
    print("=" * 80)
    print("Example 2: Finding assessments for hiring a Sales role")
    print("=" * 80)
    
    engine = AssessmentRecommendationEngine()
    criteria = create_recommendation_criteria(
        target_role="sales",
        use_case="hiring",
        competencies=["sales_drive", "customer_focus"]
    )
    recommendations = engine.recommend(criteria, top_n=3)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['name']} (Score: {rec['match_score']}%)")
        print(f"   Competencies: {', '.join(rec['competencies'][:3])}...")
    print()


def example_3_quick_assessments():
    """Example 3: Finding quick assessments under 30 minutes"""
    print("=" * 80)
    print("Example 3: Finding quick assessments (under 30 minutes)")
    print("=" * 80)
    
    engine = AssessmentRecommendationEngine()
    criteria = create_recommendation_criteria(max_duration_minutes=30)
    recommendations = engine.recommend(criteria, top_n=5)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['name']}")
        print(f"   Duration: {rec['duration_minutes']} min | Score: {rec['match_score']}%")
    print()


def example_4_development_focus():
    """Example 4: Finding assessments for leadership development"""
    print("=" * 80)
    print("Example 4: Finding assessments for Leadership Development")
    print("=" * 80)
    
    engine = AssessmentRecommendationEngine()
    criteria = create_recommendation_criteria(
        use_case="development",
        competencies=["leadership", "strategic_thinking"],
        difficulty_level="intermediate"
    )
    recommendations = engine.recommend(criteria, top_n=3)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['name']} (Score: {rec['match_score']}%)")
        print(f"   Use Cases: {', '.join(rec['use_cases'])}")
    print()


def example_5_cognitive_assessments():
    """Example 5: Finding cognitive assessments for technical roles"""
    print("=" * 80)
    print("Example 5: Finding cognitive assessments for Technical roles")
    print("=" * 80)
    
    engine = AssessmentRecommendationEngine()
    criteria = create_recommendation_criteria(
        target_role="engineer",
        assessment_type="cognitive",
        use_case="hiring"
    )
    recommendations = engine.recommend(criteria, top_n=3)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['name']} (Score: {rec['match_score']}%)")
        print(f"   Description: {rec['description']}")
    print()


def example_6_search():
    """Example 6: Searching assessments by name"""
    print("=" * 80)
    print("Example 6: Searching for 'personality' assessments")
    print("=" * 80)
    
    engine = AssessmentRecommendationEngine()
    results = engine.search_by_name("personality")
    
    for i, assessment in enumerate(results, 1):
        print(f"\n{i}. {assessment['name']} ({assessment['id']})")
        print(f"   Type: {assessment['type']}")
    print()


if __name__ == "__main__":
    print("\nSHL Assessment Recommendation Engine - Usage Examples\n")
    
    example_1_basic_recommendation()
    example_2_hiring_assessment()
    example_3_quick_assessments()
    example_4_development_focus()
    example_5_cognitive_assessments()
    example_6_search()
    
    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)

