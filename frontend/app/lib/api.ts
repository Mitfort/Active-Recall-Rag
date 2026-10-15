import type {
    DashboardData
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