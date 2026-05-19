import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "var(--background)",
          secondary: "var(--background-secondary)",
          tertiary: "var(--background-tertiary)",
        },
        surface: {
          DEFAULT: "var(--surface)",
          elevated: "var(--surface-elevated)",
          glass: "var(--surface-glass)",
          card: "var(--surface)",
          sidebar: "var(--background-secondary)",
          "sidebar-hover": "var(--surface-elevated)",
          border: "var(--border)",
          muted: "var(--background-tertiary)",
        },
        border: {
          DEFAULT: "var(--border)",
          secondary: "var(--border-secondary)",
          accent: "var(--border-accent)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
          accent: "var(--text-accent)",
        },
        primary: {
          DEFAULT: "var(--primary)",
          300: "var(--primary-300)",
          500: "var(--primary-500)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          500: "var(--secondary-500)",
        },
        accent: {
          blue: "var(--accent-blue)",
          purple: "var(--accent-purple)",
          orange: "var(--accent-orange)",
          red: "var(--accent-red)",
        },
        flag: {
          success: {
            DEFAULT: "var(--flag-success)",
            300: "var(--flag-success-300)",
          },
          warning: {
            DEFAULT: "var(--flag-warning)",
            300: "var(--flag-warning-300)",
          },
          danger: {
            DEFAULT: "var(--flag-danger)",
            300: "var(--flag-danger-300)",
          },
          info: {
            DEFAULT: "var(--flag-info)",
            300: "var(--flag-info-300)",
          },
          neutral: "var(--flag-neutral)",
        },
        brand: {
          50: "rgba(163, 230, 53, 0.1)",
          100: "rgba(163, 230, 53, 0.15)",
          500: "var(--primary)",
          600: "var(--primary)",
          700: "var(--primary)",
          800: "var(--primary)",
          900: "var(--background-secondary)",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.2)",
        "card-hover": "0 0 24px rgba(163, 230, 53, 0.15)",
        nav: "4px 0 24px rgb(0 0 0 / 0.25)",
        glow: "0 0 24px rgba(163, 230, 53, 0.25)",
        "glow-secondary": "0 0 24px rgba(163, 230, 53, 0.25)",
        "glow-blue": "0 0 24px rgba(163, 230, 53, 0.25)",
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out forwards",
        "fade-in-up": "fadeInUp 0.45s ease-out forwards",
        "slide-in": "slideIn 0.35s ease-out forwards",
        shimmer: "shimmer 1.5s ease-in-out infinite",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateX(-6px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
