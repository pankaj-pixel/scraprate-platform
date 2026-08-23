export function setSeo({ title, description, canonical, schema }) {
  document.title = title;
  const upsert = (selector, attrs) => {
    let node = document.head.querySelector(selector);
    if (!node) { node = document.createElement('meta'); document.head.appendChild(node); }
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
  };
  upsert('meta[name="description"]', { name: 'description', content: description });
  upsert('meta[property="og:title"]', { property: 'og:title', content: title });
  upsert('meta[property="og:description"]', { property: 'og:description', content: description });
  upsert('meta[property="og:type"]', { property: 'og:type', content: 'website' });
  let link = document.head.querySelector('link[rel="canonical"]');
  if (!link) { link = document.createElement('link'); link.rel = 'canonical'; document.head.appendChild(link); }
  link.href = canonical;
  document.getElementById('page-schema')?.remove();
  if (schema) { const script = document.createElement('script'); script.id = 'page-schema'; script.type = 'application/ld+json'; script.textContent = JSON.stringify(schema); document.head.appendChild(script); }
}
