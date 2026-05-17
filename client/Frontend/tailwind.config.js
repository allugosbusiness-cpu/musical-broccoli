/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
    "./src/**/*.{html}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        heading: ['Segoe UI', 'sans-serif'],
      },
      colors: {
        // Dark theme matching mobile app
        'slate': {
          '50': '#f8fafc',
          '100': '#f1f5f9',
          '200': '#e2e8f0',
          '300': '#cbd5e1',
          '400': '#94a3b8',
          '500': '#64748b',
          '600': '#475569',
          '700': '#334155',
          '800': '#1e293b',
          '900': '#0f172a',
        },
        // Brand colors
        'primary': '#3b82f6',
        'primary-light': '#60a5fa',
        'primary-dark': '#1e40af',
        // Semantic colors
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'info': '#3b82f6',
        // Status colors
        'moving': '#10b981',
        'stopped': '#ef4444',
        'idle': '#f59e0b',
        'offline': '#6b7280',
        // Legacy colors for backward compatibility
        bg: '#0f172a',
        bg2: '#1e293b',
        bg3: '#334155',
        border: '#475569',
        border2: '#64748b',
        text: '#f1f5f9',
        text2: '#cbd5e1',
        text3: '#94a3b8',
        accent: '#3b82f6',
        accent2: '#60a5fa',
        warn: '#f59e0b',
        danger: '#ef4444',
        green: '#10b981',
        blue: '#3b82f6',
        amber: '#f59e0b',
        red: '#ef4444',
        teal: '#06b6d4',
        purple: '#8b5cf6',
      },
      backgroundColor: {
        'dark': '#0f172a',
        'dark-secondary': '#1e293b',
        'dark-tertiary': '#334155',
      },
      textColor: {
        'dark': '#f1f5f9',
        'dark-secondary': '#cbd5e1',
        'dark-tertiary': '#94a3b8',
      },
      borderColor: {
        'dark': '#475569',
      },
      animation: {
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.3s ease-out',
      },
      keyframes: {
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-5px)' },
        },
        slideIn: {
          'from': { transform: 'translateX(-100%)', opacity: '0' },
          'to': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          'from': { opacity: '0' },
          'to': { opacity: '1' },
        },
      },
      boxShadow: {
        'dark': '0 4px 12px rgba(0, 0, 0, 0.5)',
        'dark-lg': '0 8px 24px rgba(0, 0, 0, 0.6)',
      },
    },
  },
  plugins: [],
}
