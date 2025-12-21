/** @type {import('tailwindcss').Config} */
module.exports = {
  // Specify the files Tailwind should scan for utility classes
  // This ensures that only used classes are included in the final CSS bundle,
  // leading to smaller file sizes.
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  // Configure dark mode strategy if needed. 'media' (default) or 'class'.
  darkMode: 'media', // or 'class' for manual dark mode toggling
  theme: {
    // Extend Tailwind's default theme with your custom values.
    // This allows you to add new design tokens without overriding defaults.
    extend: {
      colors: {
        // Define your brand-specific color palette
        primary: {
          50: '#e0f2fe',
          100: '#bfdbfe',
          200: '#93c5fd',
          300: '#60a5fa',
          400: '#3b82f6',
          500: '#2563eb', // Main brand blue
          600: '#1d4ed8',
          700: '#1e40af',
          800: '#1e3a8a',
          900: '#1e306a',
        },
        success: {
          50: '#F0FDF4', // Example very light green
          100: '#DCFCE7',
          200: '#BBF7D0',
          300: '#86EFAC',
          400: '#4ADE80',
          500: '#22C55E', // Standard green
          600: '#16A34A', // Slightly darker green, used for bg-success-600
          700: '#15803D',
          800: '#166534',
          900: '#14532D', // Example very dark green
          950: '#0F3C21',
        },
        danger: { // Add this new color definition
          50: '#FEF2F2',
          100: '#FEE2E2',
          200: '#FECACA',
          300: '#FCA5A5',
          400: '#F87171',
          500: '#EF4444',
          600: '#DC2626', // This is the color you need for bg-danger-600
          700: '#B91C1C',
          800: '#991B1B',
          900: '#7F1D1D',
          950: '#450A0A',
        },
        secondary: {
          50: '#fef3c7',
          100: '#fde68a',
          200: '#fcd34d',
          300: '#fbbf24',
          400: '#f59e0b',
          500: '#d97706', // Accent orange/yellow
          600: '#b45309',
          700: '#92400e',
          800: '#78350f',
          900: '#652d00',
        },
        // Add more custom colors as needed
        neutral: {
          50: '#f8f8f8',
          100: '#f0f0f0',
          200: '#e0e0e0',
          300: '#c0c0c0',
          400: '#a0a0a0',
          500: '#808080',
          600: '#606060',
          700: '#404040',
          800: '#202020',
          900: '#101010',
        },
      },
      // Extend typography settings, e.g., custom font families
      fontFamily: {
        sans: ['Inter', 'sans-serif'], // Example with 'Inter' font
        // You can add more custom fonts here
      },
      // Extend spacing, border radius, etc.
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      // Custom animations (if any)
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        }
      },
      animation: {
        fadeIn: 'fadeIn 0.5s ease-out forwards',
      },
    },
  },
  // Add Tailwind plugins here.
  // Tailwind Typography is highly recommended for markdown rendering
  // (e.g., in the AIChat component's AI responses).
  plugins: [
    require('@tailwindcss/forms'),      // Adds a basic reset for form styles
    require('@tailwindcss/typography'), // For styling prose content (e.g., markdown)
    // require('@tailwindcss/aspect-ratio'), // For maintaining aspect ratios
    // require('@tailwindcss/line-clamp'),  // For truncating text after a fixed number of lines
  ],
}