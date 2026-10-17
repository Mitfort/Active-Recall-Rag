"use client";

import { useState, useEffect } from 'react';

import { NoteDetails } from '@/app/types/api';

import { getNoteDetails } from '@/app/lib/api';

type Props = {
    noteId: number | null;

    onClose: () => void;
}

export function NoteDetailsPanel({
    noteId,
    onClose,
}: Props) {

    const [note,setNote] = useState<NoteDetails | null>(null);

    const [loading,setLoading] = useState(false);

    useEffect(() => {
        if (noteId === null) {
            setNote(null);
            return;
        }

        let cancelled = false;

        async function load() {
            setLoading(true);

            try {
                const data = await getNoteDetails(
                    noteId as number 
                );

                if (!cancelled) {
                    setNote(data);
                }
            } finally  {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        load();

        return () => {
            cancelled = true;
        }
    }, [noteId]);


    if (noteId === null) {
        return null;
    }

    return (
        <aside className="
            absolute
            right-4
            top-4
            z-20
            w-[340px]
            max-h-[calc(100%-2rem)]
            overflow-y-auto
            rounded-2xl
            border
            border-zinc-800
            bg-zinc-950/95
            p-5
            shadow-2xl
            backdrop-blur
        ">
            <div className="
                flex
                items-start
                justify-between
                gap-4
            ">
                <div>
                    <p className="
                        text-xs
                        text-zinc-500
                    ">
                        Note
                    </p>

                    <h2 className="
                        mt-1
                        text-lg
                        font-semibold
                    ">
                        {
                            loading ? "Loading..." : note?.title
                        }
                    </h2>

                </div>

                <button
                    onClick={onClose}
                    className="
                        rounded-lg
                        px-2
                        py-1
                        text-zinc-500
                        hover:bg-zinc-900
                        hover:text-zinc-200
                    "
                >
                    X
                </button>
            </div>

            {note && (
                <>
                    <p className="
                        mt-2
                        text-sm
                        text-zinc-500
                    ">
                        {note.subject}
                    </p>

                    {note.tags.length > 0 && (
                        <div className="mt-6">
                            <p className='
                                text-xs
                                uppercase
                                tracking-wide
                                text-zinc-600
                            '>
                                Tags
                            </p>

                            <div className='
                                mt-2
                                flex
                                flex-wrap
                                gap-2
                            '>
                                {note.tags.map((tag) => (
                                    <span
                                        key={tag}
                                        className='
                                            rounded-full
                                            bg-zinc-900
                                            px-3
                                            py-1
                                            text-xs
                                            text-zinc-400
                                        '
                                    >
                                        #{tag}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {note.links.length > 0 && (
                        <div className="mt-6">
                            <p className='
                                text-xs
                                uppercase
                                tracking-wide
                                text-zinc-600
                            '>
                                Links
                            </p>
                            
                            <div className='
                                mt-2
                                space-y-2
                            '>
                                {note.links.map((link,index) => (
                                    <div key={`${link.target}-${index}`} className='
                                        rounded-lg
                                        bg-zinc-900
                                        px-3
                                        py-2
                                        text-sm
                                        text-zinc-300
                                    '>
                                        {link.target}

                                        {link.heading && (
                                            <span className='
                                                text-zinc-600
                                            '>
                                                {" -> "}
                                                {link.heading}
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div> 
                        </div>
                    )}
                </>
            )}
    </aside>
    )
}