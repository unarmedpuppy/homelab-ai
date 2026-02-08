import { Link } from 'react-router-dom';

interface Service {
  name: string;
  app: string;
  description: string;
  url: string;
  internal?: boolean;
}

interface Category {
  title: string;
  services: Service[];
}

const categories: Category[] = [
  {
    title: 'Media & Entertainment',
    services: [
      { name: 'Movies & TV', app: 'Plex', description: 'Watch movies and TV shows', url: 'https://plex.server.unarmedpuppy.com' },
      { name: 'Request Media', app: 'Overseerr', description: 'Request new movies and shows', url: 'https://overseerr.server.unarmedpuppy.com' },
    ],
  },
  {
    title: 'Home & Kitchen',
    services: [
      { name: 'Recipes', app: 'Mealie', description: 'Meal planning and recipes', url: 'https://recipes.server.unarmedpuppy.com' },
      { name: 'Smart Home', app: 'Home Assistant', description: 'Lights, automations, and more', url: 'https://homeassistant.server.unarmedpuppy.com' },
      { name: 'Security Cameras', app: 'Frigate', description: 'Live feeds and motion detection', url: 'https://frigate.server.unarmedpuppy.com' },
    ],
  },
  {
    title: 'Documents & Photos',
    services: [
      { name: 'Photos', app: 'Immich', description: 'Photo backup and browsing', url: 'https://photos.server.unarmedpuppy.com' },
      { name: 'Documents', app: 'Paperless', description: 'Scanned document management', url: 'https://paperless.server.unarmedpuppy.com' },
    ],
  },
  {
    title: 'Productivity & Security',
    services: [
      { name: 'Project Board', app: 'Planka', description: 'Kanban-style project management', url: 'https://planka.server.unarmedpuppy.com' },
      { name: 'Passwords', app: 'Vaultwarden', description: 'Password manager', url: 'https://vaultwarden.server.unarmedpuppy.com' },
    ],
  },
  {
    title: 'AI & Tools',
    services: [
      { name: 'AI Chat', app: 'homelab-ai', description: 'Chat with AI models', url: '/chat', internal: true },
    ],
  },
];

function ServiceCard({ service }: { service: Service }) {
  if (service.internal) {
    return (
      <Link to={service.url} className="clean-card">
        <div className="clean-card-name">{service.name}</div>
        <div className="clean-card-description">{service.description}</div>
        <div className="clean-card-app">{service.app}</div>
      </Link>
    );
  }

  return (
    <a href={service.url} target="_blank" rel="noopener noreferrer" className="clean-card">
      <div className="clean-card-name">{service.name}</div>
      <div className="clean-card-description">{service.description}</div>
      <div className="clean-card-app">{service.app}</div>
    </a>
  );
}

export default function HomePage() {
  return (
    <>
      <div className="clean-page-header">
        <h1 className="clean-page-title">Home</h1>
        <p className="clean-page-subtitle">All your home services in one place</p>
      </div>

      {categories.map((category) => (
        <div key={category.title} className="clean-category">
          <h2 className="clean-category-title">{category.title}</h2>
          <div className="clean-grid">
            {category.services.map((service) => (
              <ServiceCard key={service.app} service={service} />
            ))}
          </div>
        </div>
      ))}
    </>
  );
}
