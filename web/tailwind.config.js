/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        // Institutional navy. Darker and less saturated than the indigo it
        // replaces: a state publication should read as printed ink, not as a
        // product launch.
        primary: {
          50: '#F1F4F9',
          100: '#DCE4EF',
          200: '#BCCADD',
          300: '#8FA6C4',
          400: '#5B79A3',
          500: '#365780',
          600: '#1F3F66',
          700: '#163254',
          800: '#0F2440',
          900: '#0A1930',
        },
        // Sri Lankan flag maroon, used for emphasis and the national rule.
        // Not a status colour -- the risk ramp owns red.
        state: {
          50: '#FCF2F5',
          100: '#F7DFE7',
          600: '#8D153A',
          700: '#73102F',
        },
        // Flag gold. Hairline rules and the masthead accent only.
        gold: {
          400: '#FFBE29',
          500: '#E9A400',
          600: '#B87F00',
        },
        // Risk bands. Sequential, not a rainbow: the ramp survives greyscale
        // printing and a red/green deficiency because lightness falls
        // monotonically as risk rises.
        risk: {
          low: '#0F766E',
          moderate: '#CA8A04',
          high: '#EA580C',
          severe: '#B91C1C',
        },
        text: {
          400: '#8A94A6',
          500: '#5F6A7D',
          600: '#465264',
          700: '#2E3949',
          900: '#111A27',
        },
        bg: {
          100: '#F6F7F9',
          200: '#EDEFF3',
          300: '#DFE3EA',
        },
        border: '#D3D9E3',
        rule: '#B9C2D0',
      },
      fontFamily: {
        // Source Serif for headings: an institutional text face with the
        // gravitas of a printed circular. Public Sans for everything else --
        // it is the US Web Design System's UI face, drawn for government
        // interfaces and legible at small sizes on poor screens.
        // The Sinhala and Tamil faces sit after the Latin ones: each declares its
        // own unicode-range, so the browser reaches for them only on codepoints
        // the Latin face cannot render.
        heading: [
          'var(--font-heading)',
          'var(--font-sinhala)',
          'var(--font-tamil)',
          'Georgia',
          'serif',
        ],
        body: [
          'var(--font-body)',
          'var(--font-sinhala)',
          'var(--font-tamil)',
          'system-ui',
          'sans-serif',
        ],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        display: ['3rem', { lineHeight: '1.1', fontWeight: '600', letterSpacing: '-0.015em' }],
        h1: ['2.125rem', { lineHeight: '1.2', fontWeight: '600', letterSpacing: '-0.01em' }],
        h2: ['1.625rem', { lineHeight: '1.25', fontWeight: '600' }],
        h3: ['1.125rem', { lineHeight: '1.35', fontWeight: '600' }],
        eyebrow: ['0.6875rem', { lineHeight: '1.4', fontWeight: '700', letterSpacing: '0.12em' }],
      },
      borderRadius: {
        // Deliberately shallow. Rounded corners read as consumer software;
        // official forms and notices are rectilinear.
        DEFAULT: '2px',
        sm: '2px',
        md: '3px',
        lg: '4px',
        xl: '4px',
        '2xl': '6px',
      },
      boxShadow: {
        card: '0 1px 2px 0 rgba(11, 26, 48, 0.06)',
        lift: '0 6px 20px -6px rgba(11, 26, 48, 0.22)',
        rule: 'inset 0 -1px 0 0 #D3D9E3',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.9)', opacity: '0.7' },
          '70%': { transform: 'scale(1.7)', opacity: '0' },
          '100%': { transform: 'scale(1.7)', opacity: '0' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.4s ease-out both',
        'pulse-ring': 'pulse-ring 2.4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};
