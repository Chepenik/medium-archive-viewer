import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        body: ['var(--font-literata)', 'Georgia', 'Times New Roman', 'serif'],
        heading: ['var(--font-fraunces)', 'Georgia', 'serif'],
      },
      colors: {
        bg: {
          DEFAULT: 'rgb(var(--color-bg) / <alpha-value>)',
          secondary: 'rgb(var(--color-bg-secondary) / <alpha-value>)',
          tertiary: 'rgb(var(--color-bg-tertiary) / <alpha-value>)',
        },
        text: {
          DEFAULT: 'rgb(var(--color-text) / <alpha-value>)',
          secondary: 'rgb(var(--color-text-secondary) / <alpha-value>)',
          muted: 'rgb(var(--color-text-muted) / <alpha-value>)',
        },
        border: {
          DEFAULT: 'rgb(var(--color-border) / <alpha-value>)',
        },
        accent: {
          DEFAULT: 'rgb(var(--color-accent) / <alpha-value>)',
          hover: 'rgb(var(--color-accent-hover) / <alpha-value>)',
        },
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: '68ch',
            color: 'rgb(var(--color-text))',
            lineHeight: '1.8',
            a: {
              color: 'rgb(var(--color-accent))',
              textDecoration: 'underline',
              textUnderlineOffset: '3px',
              '&:hover': {
                color: 'rgb(var(--color-accent-hover))',
              },
            },
            strong: {
              color: 'rgb(var(--color-text))',
            },
            h1: {
              fontFamily: 'var(--font-fraunces)',
              color: 'rgb(var(--color-text))',
            },
            h2: {
              fontFamily: 'var(--font-fraunces)',
              color: 'rgb(var(--color-text))',
            },
            h3: {
              fontFamily: 'var(--font-fraunces)',
              color: 'rgb(var(--color-text))',
            },
            h4: {
              fontFamily: 'var(--font-fraunces)',
              color: 'rgb(var(--color-text))',
            },
            blockquote: {
              borderLeftColor: 'rgb(var(--color-accent))',
              color: 'rgb(var(--color-text-secondary))',
            },
            code: {
              backgroundColor: 'rgb(var(--color-bg-secondary))',
              padding: '0.2em 0.4em',
              borderRadius: '4px',
            },
            pre: {
              backgroundColor: 'rgb(var(--color-bg-secondary))',
            },
            hr: {
              borderColor: 'rgb(var(--color-border))',
            },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
export default config;
