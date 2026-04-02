interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
  children: React.ReactNode;
}

const STYLES = {
  primary: "bg-navy text-white hover:bg-navy-dark shadow-sm hover:shadow",
  secondary: "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 border border-gray-200 dark:border-gray-600",
  danger: "bg-accent text-white hover:bg-accent-dark shadow-sm hover:shadow",
};

export function Button({ variant = "primary", children, className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50
        transition-all duration-150 ${STYLES[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
