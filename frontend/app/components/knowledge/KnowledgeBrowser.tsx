"use client";

import { useState } from "react";
import type {
    KnowledgeSubject
} from "@/app/types/api"

import { NoteCard } from "@/app/components/knowledge/NoteCard";

type Props = {
    subjects: KnowledgeSubject[];
}

export function KnowledgeBrowser({ subjects }: Props){
    const [expandedSubject,setExpandedSubject] = useState<string | null>(subjects[0]?.name ?? null);

    return (
        <div className="space-y-4">
            {subjects.map((subject) => {
                const mastery = Math.round(subject.average_mastery * 100);

                const memory = Math.round(subject.average_retrievability * 100);

                const expanded = expandedSubject === subject.name;

                return (
                    <section key={subject.name} className="
                        overflow-hidden
                        rounded-2xl
                        border border-zinc-800
                        bg-zinc-900
                    ">
                        <button onClick={() => {
                            setExpandedSubject(
                                expanded ? null : subject.name
                            )
                        }} className="
                            flex
                            w-full
                            items-center
                            justify-between
                            gap-6
                            p-6
                            text-left
                        ">
                            <div>
                                <h2 className="
                                    text-xl
                                    font-semibold
                                ">
                                    {subject.name}
                                </h2>

                                <p className="
                                    mt-1
                                    text-sm
                                    text-zinc-500
                                ">
                                    {subject.concepts_count}
                                    {" concepts • "}

                                    {subject.review_count}
                                    {" reviewed"}
                                </p>

                            </div>

                            <div className="
                                flex
                                gap-8
                                text-right
                            ">
                                <div>
                                    <p className="
                                        text-xs
                                        text-zinc-500
                                    ">
                                        Mastery
                                    </p>

                                    <p className="
                                        mt-1
                                        font-medium
                                    ">
                                        {mastery}%
                                    </p>
                                </div>

                                <div>
                                    <p className="
                                        text-xs
                                        text-zinc-500
                                    ">
                                        Memory
                                    </p>

                                    <p className="
                                        mt-1
                                        font-medium
                                    ">
                                        {memory}%
                                    </p>
                                </div>
                            

                            </div>
                        </button>

                        {expanded && (
                            <div className="
                                border-t
                                border-zinc-800
                                p-6
                            ">
                                <div className="
                                    space-y-4
                                ">
                                    {subject.notes.map((note => (
                                        <NoteCard
                                            key={note.id}
                                            note={note}
                                        />
                                    )))}
                                </div>
                            </div>
                        )}    
                    </section>
                )
            })}
        </div>
    )
}