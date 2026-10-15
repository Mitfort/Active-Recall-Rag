import type {
    WeakConcept,
} from "../../types/api";

type Props = {
    concepts: WeakConcept[];
}

export function WeakConcepts({
    concepts,
}: Props)
{
    return (
        <section
            className="
                rounded-2xl
                border border-zinc-800
                bg-zinc-900/70
                p-6
            ">
            <div className="mb-6">
                <h2
                className="
                    text-lg
                    font-semibold
                    text-zinc-100
                ">
                    Weakest Concepts
                </h2>

                <p
                className="
                    mt-1
                    text-sm
                    text-zinc-500
                ">
                    These are the concepts that you struggle with the most.
                </p>
            </div>

            {concepts.length === 0 ? (
                <p className="text-sm text-zinc-500">
                    No reviewed concepts yet.
                </p>
            ) : (
                <div className="space-y-5">
                    {concepts.map((concept) => {
                        const mastery = Math.round(
                            concept.mastery * 100
                        );

                        const memory = Math.round(
                            concept.retrievability * 100
                        );

                        return (
                            <div key={concept.id}>
                                <div className="
                                    flex
                                    items-start
                                    justify-between
                                    gap-4
                                ">
                                    <div>
                                        <p className="
                                            font-medium
                                            text-zinc-200
                                        ">
                                            {concept.heading}
                                        </p>

                                        <p className="
                                            text-xs
                                            text-zinc-500
                                        ">
                                            {concept.note}
                                        </p>
                                    </div>

                                    <div className="
                                        text-right
                                        text-sm                                    
                                    "> 
                                        <p className="text-zinc-300">
                                            Mastery: {mastery}%
                                        </p>
                                        <p className="text-zinc-500">
                                            Memory: {memory}%
                                        </p>
                                    </div>
                                </div>

                                <div className="
                                    mt-3
                                    h-2
                                    overflow-hidden
                                    rounded-full
                                    bg-zinc-800
                                ">
                                    <div className="
                                        h-full
                                        rounded-full
                                        bg-zinc-300
                                    "
                                    style={{
                                        width: `${mastery}%`
                                    }} />
                                </div>

                            </div>
                        )
                    })}

                </div>
            )
                }

        </section>
    )
}