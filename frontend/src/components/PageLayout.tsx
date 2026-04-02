interface PageLayoutProps {
  title: string;
  children: React.ReactNode;
}

export function PageLayout({ title, children }: PageLayoutProps) {
  return (
    <div className="max-w-6xl">
      <h2 className="text-xl font-bold mb-6">{title}</h2>
      <div className="space-y-6">{children}</div>
    </div>
  );
}
