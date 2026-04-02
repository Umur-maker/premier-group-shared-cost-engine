interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
  children: React.ReactNode;
}

const STYLES = {
  primary: "bg-blue-600 text-white hover:bg-blue-700",
  secondary: "bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300",
  danger: "bg-red-600 text-white hover:bg-red-700",
};

export function Button({ variant = "primary", children, className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`px-4 py-2 rounded text-sm font-medium disabled:opacity-50
        transition-colors ${STYLES[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
