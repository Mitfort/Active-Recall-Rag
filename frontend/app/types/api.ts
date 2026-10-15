export interface WeakConcept {
    id: number;
    heading: string;
    note: string;

    mastery: number;
    retrievability: number;
}

export interface ActivityDay {
    date: string;

    reviews: number;

    average_correctness: number; 
}

export interface DashboardData {
    due_today: number;

    total_concepts: number;
    new_concepts: number;

    average_mastery: number;
    average_retrievability: number;

    recent_accuracy: number | null;

    reviews_last_7_days: number;

    weakest: WeakConcept[];

    activity: ActivityDay[];
}

export interface ReviewConcept {
    id: number;
    heading: string;
    note: string;

    mastery: number;
    retrievability: number;
}

export interface DailyReviewData {
    due_count: number;
    concepts: ReviewConcept[];
}

export interface ReviewSource {
    type: string;

    concept_id?: number;

    name: string;
    note?: string;

    provider?: string;
    url?: string;
}

export interface ReviewQuestion {
    attempt_id: number;
    concept_id: number;

    question:string;

    difficulty: number;
    question_type: string;

    target_concept: string;
    sources: ReviewSource[];
}

export interface AnswerResult {
    correctness: number;
    verdict: string;

    feedback: string;

    expected_answer: string;

    missing_points: string[];
    missconceptions: string[];

    combine_score: number;
    scheduler_rating: number;

    mastery_before: number;
    mastery_after: number;
    
    stability_before: number;
    stability_after: number;

    next_review:string;
}