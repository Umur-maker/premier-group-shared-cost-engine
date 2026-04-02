interface SectionCardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function SectionCard({ title, children, className = "" }: SectionCardProps) {
  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-5 ${className}`}>
      {title && (
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
