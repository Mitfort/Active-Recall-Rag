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

export interface KnowledgeConcept {
    id: number;
    heading: string;

    mastery: number;
    retrievability: number;

    review_count: number;
}

export interface KnowledgeNote {
    id: number;
    title: string;

    average_mastery: number;
    average_retrievability: number;

    concepts: KnowledgeConcept[];

}

export interface KnowledgeSubject {
    name: string;

    concepts_count: number;
    review_count: number;

    average_mastery: number;
    average_retrievability: number;

    notes: KnowledgeNote[];
}

export interface KnowledgeData {
    total_subjects: number;

    subjects: KnowledgeSubject[];
}

// NOTE DETAILS
export interface NoteWikiLink {
    target: string;
    heading: string | null;
    alias: string | null;
}

export interface NoteDetails {
    id: number;
    title: string;
    subject: string;

    file_path: string;
    metadata: Record<string, string>;

    tags: string[];
    links: NoteWikiLink[];
}

// KNOWLEDGE GRAPH

export interface KnowledgeGraphNode {
    id: number;
    label: string;
    subject: string;
    type: "note";
    mastery: number;
    retrievability: number;
    concept_count: number;
    reviewed_count: number;
}

export interface KnowledgeGraphEdge {
    source: number;
    target: number;
    type: "wikilink" | "semantic";

    score: number | null;
}

export interface UnresolvedKnowledgeLink {
    source: number;
    target_title: string;
}

export interface KnowledgeGraphData {
    nodes: KnowledgeGraphNode[];
    edges: KnowledgeGraphEdge[];

    unresolved_links: UnresolvedKnowledgeLink[];
}