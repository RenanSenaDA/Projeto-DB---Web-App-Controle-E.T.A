/**
 * Propriedades do componente PageHeader.
 */
interface PageHeaderProps {
  /** Título principal da página */
  title: string;
  /** Subtítulo ou descrição curta */
  subtitle: string;
  /** Elementos opcionais para renderizar à direita do cabeçalho (ex: botões de ação) */
  children?: React.ReactNode;
}

/**
 * Cabeçalho padrão para páginas da aplicação.
 * Exibe título, subtítulo e ações opcionais com layout responsivo.
 * 
 * @component
 */
export default function PageHeader({
  title,
  subtitle,
  children,
}: PageHeaderProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          {title}
        </h1>
        <p className="text-slate-500 mt-1">{subtitle}</p>
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  );
}
