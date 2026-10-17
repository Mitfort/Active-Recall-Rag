import Link from "next/link";

export function AppNav() {
    return (
        <nav className="
            border-b
            border-zinc-900
            bg-zinc-950
        ">
            <div className="
                mx-auto
                flex
                max-w-7xl
                items-center
                gap-6
                px-6
                py-4
            ">
                <Link href="/" className="
                    font-semibold
                    text-zinc-100
                ">
                    Active Recall
                </Link>

                <Link href="/" className="
                    text-xm
                    text-zinc-400
                    hover:text-zinc-100
                ">
                    Dashboard
                </Link>

                <Link href="/review" className="
                    text-xm
                    text-zinc-400
                    hover:text-zinc-100
                ">
                    Review
                </Link>

                <Link href="/knowledge" className="
                    text-xm
                    text-zinc-400
                    hover:text-zinc-100
                ">
                    Knowledge
                </Link>

                <Link href="/knowledge/graph" className="
                    text-xm
                    text-zinc-400
                    hover:text-zinc-100
                ">
                    Graph 
                </Link>

            </div>

        </nav>
    );
}