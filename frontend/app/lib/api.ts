import type {
    DashboardData,
    DailyReviewData,
    ReviewQuestion,
    AnswerResult,
    KnowledgeData
 } from '../types/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function getDashboard(): Promise<DashboardData> {
    const response = await fetch(
        `${API_URL}/dashboard`,
        {
            cache: 'no-store'
        }
    )

    if (!response.ok) {
        throw new Error(`Failed to fetch dashboard data: ${response.statusText}`);
    }

    return response.json();
}

export async function getTodayReview():
    Promise<DailyReviewData> {
    
    const response = await fetch(
        `${API_URL}/review/today`,
        {
            cache: 'no-store'
        }
    )

    if (!response.ok) {
        throw new Error(`Failed to fetch today's review data: ${response.statusText}`);
    }

    return response.json();
}

export async function createQuestion(
    conceptId: number,
): Promise<ReviewQuestion> {

    const response = await fetch(
        `${API_URL}/review/${conceptId}/question`,
        {
            method: 'POST'
        }
    );

    if (!response.ok) {
        throw new Error("Failed to generate question")
    }

    return response.json();
}

export async function submitAnswer(
    attemptId: number,
    answer: string,
    confidence: number
): Promise<AnswerResult> {

    const response = await fetch(
        `${API_URL}/review/${attemptId}/answer`,
        {
            method: 'POST',
            headers: {
                "Content-Type": 'application/json'
            },

            body: JSON.stringify({
                answer,
                confidence
            })
        })

    if (!response.ok) {
        throw new Error("Failed to submit answer")
    }

    return response.json();
}

export async function getKnowledge(): Promise<KnowledgeData> {

    const response = await fetch(
        `${API_URL}/knowledge`,
        {
            cache: 'no-store'
        }
    );

    if (!response.ok) {
        throw new Error("Failed to fetch knowledge data")
    }

    return response.json();
}
