import type {
    KnowledgeNote
} from '@/app/types/api';

export function NoteCard({note} : {note: KnowledgeNote}) {
    const mastery = Math.round(note.average_mastery * 100);
    
    return (
        <div
        className="
            rounded-xl
            border border-zinc-800
            bg-zinc-950
            p-5
        "
        >

        <div
            className="
            flex
            items-center
            justify-between
            "
        >

            <div>

            <h3
                className="
                font-medium
                text-zinc-200
                "
            >
                {note.title}
            </h3>

            <p
                className="
                mt-1
                text-xs
                text-zinc-500
                "
            >
                {note.concepts.length}
                {" concepts"}
            </p>

            </div>


            <span
            className="
                text-sm
                text-zinc-400
            "
            >
            {mastery}%
            </span>

        </div>


        <div
            className="
            mt-5
            space-y-2
            "
        >

            {note.concepts.map(
            (concept) => {

                const conceptMastery =
                Math.round(
                    concept.mastery
                    * 100
                );

                const memory =
                Math.round(
                    concept.retrievability
                    * 100
                );


                return (
                <div
                    key={concept.id}

                    className="
                    flex
                    items-center
                    justify-between
                    rounded-lg
                    px-3
                    py-2
                    hover:bg-zinc-900
                    "
                >

                    <span
                    className="
                        text-sm
                        text-zinc-300
                    "
                    >
                    {concept.heading}
                    </span>


                    <div
                    className="
                        flex
                        gap-4
                        text-xs
                        text-zinc-500
                    "
                    >

                    <span>
                        {conceptMastery}%
                        {" mastery"}
                    </span>

                    <span>
                        {memory}%
                        {" memory"}
                    </span>

                    </div>

                </div>
                );
            }
            )}

        </div>

        </div>
    );
}