import { BackgroundPaths } from "@/components/ui/background-paths";

export function LandingHero() {
    return (
        <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
            <BackgroundPaths />
            <div className="relative z-10 text-center">
                <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
                    HR Sentinel AI
                </h1>
                <p className="mt-4 text-lg text-muted-foreground">
                    Workforce Intelligence Platform
                </p>
            </div>
        </div>
    );
}
