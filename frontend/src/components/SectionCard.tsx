interface SectionCardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function SectionCard({ title, children, className = "" }: SectionCardProps) {
  return (
    <div className={`bg-card dark:bg-card-dark border border-gray-200 dark:border-gray-700
      rounded-lg p-5 shadow-sm ${className}`}>
      {title && (
        <h3 className="text-xs font-semibold text-navy dark:text-blue-300 uppercase tracking-wide mb-3">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
