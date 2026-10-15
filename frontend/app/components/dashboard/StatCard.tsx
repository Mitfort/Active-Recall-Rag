type StatCardProps = {
    label: string;
    value: number | string;

    description?: string;
};

export function StatCard({
    label,
    value,
    description
}: StatCardProps) {
    return (
        <div className="
            rounded-2xl
            border border-zinc-800
            bg-zinc-900/70
            p-5
        ">
            <p
            className="
                    text-sm
                    text-zinc-400
            ">
                {label}
            </p>

            <p
            className="
                mt-2
                text-3xl
                font-semibold
                tracking-tight
                text-zinc-100
            ">
                {value}
            </p>

            {description && (
                <p 
                className="
                    mt-2
                    text-sm
                    text-zinc-500
                ">
                    {description}
                </p>
            )}  
        </div>
    )
}