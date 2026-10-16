import { Suspense } from "react";

import { getKnowledge } from "@/app/lib/api";
import { KnowledgeBrowser } from "@/app/components/knowledge/KnowledgeBrowser";

async function KnowledgeContent(){
    const data = await getKnowledge();

    return (
        <KnowledgeBrowser subjects={data.subjects} />
    );
}

async function LoadingKnowledge() { 
    return (
        <div className="
            h-96
            animate-pulse
            rounded-3xl
            bg-zinc-900
        ">
        </div>
    )
}


export default function KnowledgePage() {
    return (
        <main className="
            min-h-screen
            bg-zinc-950
            text-zinc-100
        ">
            <div className="
                mx-auto
                max-w-6xl
                px-6
                py-10 
            ">
                <div className="mb-10">
                    <p className="
                        text-sm
                        text-zinc-500
                    ">
                        Knowledge base
                    </p>

                    <h1 className="
                        mt-2
                        text-3xl
                        font-semibold
                    ">
                        Your knowledge
                    </h1>

                    <p className="
                        mt-3
                        max-2-2xl
                        text-zinc-400
                    ">
                        Explore subjects, notes and concepts
                        extracted from your learning materials.
                    </p>
                </div>

                <Suspense 
                    fallback={<LoadingKnowledge />}
                >
                    <KnowledgeContent />
                </Suspense>
            </div>

        </main>
    )
}