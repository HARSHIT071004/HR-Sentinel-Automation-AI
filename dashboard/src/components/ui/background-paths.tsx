"use client";

import { motion } from "framer-motion";

function FloatingPaths({ position }: { position: number }) {
    const paths = Array.from({ length: 20 }, (_, i) => ({
        id: i,
        d: `M ${-200 + i * 20 * position} ${-100 + i * 10} Q ${0 + i * 10 * position} ${-50 + i * 5} ${200 - i * 20 * position} ${100 - i * 10}`,
        width: 0.5 + i * 0.05,
    }));
    return (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <svg className="w-full h-full" viewBox="-300 -200 600 400" fill="none">
                {paths.map((path) => (
                    <motion.path
                        key={path.id}
                        d={path.d}
                        stroke="var(--primary)"
                        strokeWidth={path.width}
                        strokeOpacity={0.15}
                        initial={{ pathLength: 0.3, opacity: 0.3 }}
                        animate={{
                            pathLength: 1,
                            opacity: [0.1, 0.3, 0.1],
                        }}
                        transition={{
                            duration: 15 + path.id * 2,
                            repeat: Number.POSITIVE_INFINITY,
                            ease: "linear",
                        }}
                    />
                ))}
            </svg>
        </div>
    );
}

export function BackgroundPaths() {
    return (
        <div className="absolute inset-0 pointer-events-none">
            <FloatingPaths position={1} />
            <FloatingPaths position={-1} />
        </div>
    );
}
