import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class RecommendationCriteria:
    target_role: Optional[str] = None
    competencies: Optional[List[str]] = None
    use_case: Optional[str] = None
    assessment_type: Optional[str] = None
    max_duration_minutes: Optional[int] = None
    difficulty_level: Optional[str] = None
    language: Optional[str] = None
    exclude_ids: Optional[List[str]] = None


class AssessmentRecommendationEngine:
    """Engine for recommending SHL assessments based on criteria"""
    
    def __init__(self, catalogue_path: str = "product_catalogue.json"):
        """Initialize the recommendation engine with product catalogue"""
        self.catalogue_path = Path(catalogue_path)
        self.assessments = self._load_catalogue()
        # Pre-compute TF-IDF matrix for text-based recommendations
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._tfidf_matrix = None
        self._build_text_index()
    
    def _load_catalogue(self) -> List[Dict]:
        """Load assessment catalogue from JSON file"""
        try:
            with open(self.catalogue_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('assessments', [])
        except FileNotFoundError:
            raise FileNotFoundError(f"Catalogue file not found: {self.catalogue_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in catalogue file: {self.catalogue_path}")

    def _build_text_index(self) -> None:
        if not self.assessments:
            return

        documents: List[str] = []
        for a in self.assessments:
            name = a.get("name", "") or ""
            desc = a.get("description", "") or ""
            # Optionally include type/category to enrich the document
            type_ = a.get("type", "") or ""
            category = a.get("category", "") or ""
            doc = " ".join([name, desc, type_, category]).strip()
            documents.append(doc)

        # Configure a reasonable TF-IDF vectorizer for short product texts
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_df=0.9,
            min_df=1,
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(documents)
    
    def _calculate_match_score(self, assessment: Dict, criteria: RecommendationCriteria) -> float:
        """Calculate match score for an assessment based on criteria"""
        score = 0.0
        max_score = 0.0
        
        # Target role matching (weight: 30%)
        if criteria.target_role:
            max_score += 30
            target_roles = assessment.get('target_roles', [])
            if 'all' in target_roles or criteria.target_role.lower() in [r.lower() for r in target_roles]:
                score += 30
            elif any(criteria.target_role.lower() in r.lower() or r.lower() in criteria.target_role.lower() 
                    for r in target_roles):
                score += 15
        
        # Competencies matching (weight: 25%)
        if criteria.competencies:
            max_score += 25
            assessment_competencies = set(c.lower() for c in assessment.get('competencies', []))
            required_competencies = set(c.lower() for c in criteria.competencies)
            if required_competencies:
                overlap = len(assessment_competencies & required_competencies)
                score += (overlap / len(required_competencies)) * 25
        
        # Use case matching (weight: 20%)
        if criteria.use_case:
            max_score += 20
            use_cases = [uc.lower() for uc in assessment.get('use_cases', [])]
            if criteria.use_case.lower() in use_cases:
                score += 20
        
        # Assessment type matching (weight: 10%)
        if criteria.assessment_type:
            max_score += 10
            if assessment.get('type', '').lower() == criteria.assessment_type.lower():
                score += 10
        
        # Duration matching (weight: 5%)
        if criteria.max_duration_minutes:
            max_score += 5
            duration = assessment.get('duration_minutes', 0)
            if duration <= criteria.max_duration_minutes:
                score += 5
            elif duration <= criteria.max_duration_minutes * 1.5:
                score += 2.5
        
        # Difficulty level matching (weight: 5%)
        if criteria.difficulty_level:
            max_score += 5
            if assessment.get('difficulty_level', '').lower() == criteria.difficulty_level.lower():
                score += 5
        
        # Language matching (weight: 5%)
        if criteria.language:
            max_score += 5
            languages = [lang.lower() for lang in assessment.get('languages', [])]
            if criteria.language.lower() in languages:
                score += 5
        
        # Normalize score to percentage
        if max_score > 0:
            return (score / max_score) * 100
        return 0.0
    
    def _filter_assessments(self, assessments: List[Dict], criteria: RecommendationCriteria) -> List[Dict]:
        """Filter assessments based on exclusion criteria"""
        filtered = assessments
        
        # Exclude specific assessment IDs
        if criteria.exclude_ids:
            exclude_set = set(criteria.exclude_ids)
            filtered = [a for a in filtered if a.get('id') not in exclude_set]
        
        return filtered
    
    def recommend(self, criteria: RecommendationCriteria, top_n: int = 5) -> List[Dict]:
        """
        Recommend assessments based on criteria
        
        Args:
            criteria: RecommendationCriteria object with search parameters
            top_n: Number of top recommendations to return
            
        Returns:
            List of recommended assessments with match scores
        """
        # Filter assessments
        candidates = self._filter_assessments(self.assessments, criteria)
        
        # Calculate scores and add to assessments
        scored_assessments = []
        for assessment in candidates:
            score = self._calculate_match_score(assessment, criteria)
            scored_assessments.append({
                **assessment,
                'match_score': round(score, 2)
            })
        
        # Sort by match score (descending) and return top N
        scored_assessments.sort(key=lambda x: x['match_score'], reverse=True)
        
        return scored_assessments[:top_n]

    # ------------------------------------------------------------------
    # Text-based recommendations (for natural language query / JD text)
    # ------------------------------------------------------------------

    def recommend_from_text(self, text: str, top_n: int = 10) -> List[Dict]:
        """
        Recommend assessments based on free-text input (query or JD).

        Args:
            text: Natural language query or job description text.
            top_n: Number of top recommendations to return.

        Returns:
            List of assessments with an added 'similarity' field (0–1).
        """
        if not text or not self.assessments or self._vectorizer is None or self._tfidf_matrix is None:
            return []

        query = text.strip()
        if not query:
            return []

        query_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self._tfidf_matrix)[0]

        # Pair each assessment with its similarity score
        indexed = list(enumerate(sims))
        indexed.sort(key=lambda x: x[1], reverse=True)

        results: List[Dict] = []
        for idx, sim in indexed[: max(top_n, 10)]:  # compute at least 10, will slice later
            a = self.assessments[idx]
            # Include similarity as a float; keep original fields intact
            result = {
                **a,
                "similarity": float(sim),
            }
            results.append(result)

        # Enforce 5–10 range by default: at least 5 if possible, at most top_n
        top_n_clamped = max(5, min(top_n, 10))
        return results[:top_n_clamped]
    
    def get_assessment_by_id(self, assessment_id: str) -> Optional[Dict]:
        """Get a specific assessment by its ID"""
        for assessment in self.assessments:
            if assessment.get('id') == assessment_id:
                return assessment
        return None
    
    def get_all_assessments(self) -> List[Dict]:
        """Get all assessments in the catalogue"""
        return self.assessments
    
    def search_by_name(self, search_term: str) -> List[Dict]:
        """Search assessments by name (case-insensitive partial match)"""
        search_term_lower = search_term.lower()
        return [
            assessment for assessment in self.assessments
            if search_term_lower in assessment.get('name', '').lower()
            or search_term_lower in assessment.get('description', '').lower()
        ]


def create_recommendation_criteria(
    target_role: Optional[str] = None,
    competencies: Optional[List[str]] = None,
    use_case: Optional[str] = None,
    assessment_type: Optional[str] = None,
    max_duration_minutes: Optional[int] = None,
    difficulty_level: Optional[str] = None,
    language: Optional[str] = None,
    exclude_ids: Optional[List[str]] = None
) -> RecommendationCriteria:
    """Helper function to create RecommendationCriteria"""
    return RecommendationCriteria(
        target_role=target_role,
        competencies=competencies,
        use_case=use_case,
        assessment_type=assessment_type,
        max_duration_minutes=max_duration_minutes,
        difficulty_level=difficulty_level,
        language=language,
        exclude_ids=exclude_ids
    )

