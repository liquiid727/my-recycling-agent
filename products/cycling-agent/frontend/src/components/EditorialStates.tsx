export function LoadingCard({ title, body }: { title: string; body: string }) {
  return (
    <section className="paper-section">
      <p className="eyebrow">Loading</p>
      <h2 className="section-title">{title}</h2>
      <p className="body-copy mt-4">{body}</p>
    </section>
  );
}

export function ErrorCard({ title, body }: { title: string; body: string }) {
  return (
    <section className="paper-section border-amber/40 bg-white/90">
      <p className="eyebrow">Unavailable</p>
      <h2 className="section-title">{title}</h2>
      <p className="body-copy mt-4">{body}</p>
    </section>
  );
}
