interface FormRowProps {
  label: string;
  children: React.ReactNode;
  className?: string;
}

export function FormRow({ label, children, className = "" }: FormRowProps) {
  return (
    <div className={className}>
      <label className="block text-xs text-gray-600 mb-1">{label}</label>
      {children}
    </div>
  );
}
