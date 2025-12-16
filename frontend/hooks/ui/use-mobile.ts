import * as React from "react"

const MOBILE_BREAKPOINT = 768

/**
 * Hook para detecção de dispositivos móveis.
 * Retorna true se a largura da janela for menor que o breakpoint definido (768px).
 * Usa matchMedia para melhor performance e event listeners.
 */
export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined)

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    mql.addEventListener("change", onChange)
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return !!isMobile
}
