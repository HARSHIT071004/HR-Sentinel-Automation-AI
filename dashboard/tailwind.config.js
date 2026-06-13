/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0f",
        foreground: "#fafafa",
        card: "#0f0f17",
        "card-foreground": "#fafafa",
        popover: "#0f0f17",
        "popover-foreground": "#fafafa",
        primary: "#fafafa",
        "primary-foreground": "#0a0a0f",
        secondary: "#1a1a2e",
        "secondary-foreground": "#fafafa",
        muted: "#1a1a2e",
        "muted-foreground": "#a1a1aa",
        accent: "#1a1a2e",
        "accent-foreground": "#fafafa",
        destructive: "#dc2626",
        "destructive-foreground": "#fafafa",
        border: "#1e1e2e",
        input: "#1e1e2e",
        ring: "#6366f1",
      },
      borderRadius: {
        lg: "0.5rem",
        md: "calc(0.5rem - 2px)",
        sm: "calc(0.5rem - 4px)",
      },
    },
  },
  plugins: [],
}
