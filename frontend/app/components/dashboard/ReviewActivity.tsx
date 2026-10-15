import type {
    ActivityDay,
} from "../../types/api";

type Props = {
    activity: ActivityDay[];
}

export function ReviewActivity({
    activity,
}: Props) {

    const maxReviews = Math.max(...activity.map(
        (day) => day.reviews
    ), 1); 

    return (
        <section
            className="
                rounded-2xl
                border border-zinc-800
                bg-zinc-900/70
                p-6
            ">
                <h2 className="
                    text-lg
                    font-semibold
                    text-zinc-100
                ">
                    Review Activity
                </h2>

                <p className="
                    mt-1
                    text-sm
                    text-zinc-500
                ">
                    Reviews completed over the last 7 days.
                </p>

                <div className="
                    mt-8
                    flex
                    h-48
                    items-end
                    gap-3
                ">
                    {activity.map((day) => {
                        const height = (day.reviews / maxReviews) * 100;
                        
                        const formattedDate = new Date(
                            `${day.date}T12:00:00`
                        ).toLocaleDateString(
                            undefined,
                            {
                                weekday: 'short',
                            }
                        )
                        
                        return (
                            <div
                                key={day.date}
                                className="
                                    flex
                                    h-full
                                    flex-1
                                    flex-col
                                    justify-end
                                "
                            >
                                <div
                                    className="
                                        flex
                                        flex-1
                                        items-end
                                    ">

                                    <div
                                        title={`${day.reviews} reviews`}
                                        className="
                                            w-full
                                            rounded-t-lg
                                            bg-zinc-300
                                            transition-all
                                        "
                                        style={{
                                            height: `${height}%`,
                                            minHeight:
                                                day.reviews > 0
                                                    ? "6px"
                                                    : "0px"
                                        }}
                                    />
                                </div>
                                <p className="
                                    mt-3
                                    text-center
                                    text-xs
                                    text-zinc-500
                                ">
                                    {formattedDate}
                                </p>

                                <p className="
                                    text-center
                                    text-xs
                                    text-zinc-400
                                ">
                                    {day.reviews}
                                </p>
                            </div>
                        )
                    },
                    )}
                </div>
            </section>
    )
}