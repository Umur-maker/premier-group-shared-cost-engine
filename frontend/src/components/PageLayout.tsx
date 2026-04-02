interface PageLayoutProps {
  title: string;
  children: React.ReactNode;
}

export function PageLayout({ title, children }: PageLayoutProps) {
  return (
    <div className="max-w-6xl">
      <h2 className="text-2xl font-bold text-navy dark:text-white mb-1 tracking-tight">{title}</h2>
      <div className="h-0.5 w-12 bg-accent rounded-full mb-6" />
      <div className="space-y-5">{children}</div>
    </div>
  );
}
