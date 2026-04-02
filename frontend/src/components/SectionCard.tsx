interface SectionCardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function SectionCard({ title, children, className = "" }: SectionCardProps) {
  return (
    <div className={`bg-card dark:bg-card-dark border border-gray-200/80 dark:border-gray-700/60
      rounded-xl p-6 shadow-[0_1px_3px_rgba(0,0,0,0.04)] ${className}`}>
      {title && (
        <h3 className="text-[11px] font-bold text-navy/70 dark:text-blue-300/80 uppercase tracking-widest mb-4">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
