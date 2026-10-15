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