import { useState, useEffect } from 'react'

export const useDarkMode = () => {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('texlify-theme')
    if (saved) return saved === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    const root = document.documentElement
    if (isDark) {
      root.setAttribute('data-theme', 'dark')
      localStorage.setItem('texlify-theme', 'dark')
    } else {
      root.removeAttribute('data-theme')
      localStorage.setItem('texlify-theme', 'light')
    }
  }, [isDark])

  return { isDark, toggle: () => setIsDark(p => !p) }
}