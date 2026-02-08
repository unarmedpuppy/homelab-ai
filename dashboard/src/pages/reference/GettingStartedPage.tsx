import { Link } from 'react-router-dom';

interface RefCard {
  title: string;
  body: React.ReactNode;
}

const cards: RefCard[] = [
  {
    title: 'Passwords',
    body: (
      <>
        All passwords are stored in <a href="https://vaultwarden.server.unarmedpuppy.com" target="_blank" rel="noopener noreferrer">Vaultwarden</a>.
        Install the Bitwarden browser extension and mobile app, then connect it to our server.
      </>
    ),
  },
  {
    title: 'Movies & TV',
    body: (
      <>
        Use <a href="https://plex.server.unarmedpuppy.com" target="_blank" rel="noopener noreferrer">Plex</a> to watch.
        Use <a href="https://overseerr.server.unarmedpuppy.com" target="_blank" rel="noopener noreferrer">Overseerr</a> to
        request new content — it downloads automatically.
      </>
    ),
  },
  {
    title: 'Recipes',
    body: (
      <>
        <a href="https://recipes.server.unarmedpuppy.com" target="_blank" rel="noopener noreferrer">Mealie</a> handles
        meal planning and recipe management. Save recipes from the web using the bookmarklet.
      </>
    ),
  },
  {
    title: 'Photos',
    body: (
      <>
        <a href="https://photos.server.unarmedpuppy.com" target="_blank" rel="noopener noreferrer">Immich</a> backs up
        and organizes photos. Install the mobile app for automatic backup.
      </>
    ),
  },
  {
    title: 'Documents',
    body: (
      <>
        <a href="https://paperless.server.unarmedpuppy.com" target="_blank" rel="noopener noreferrer">Paperless</a> auto-organizes
        scanned documents. Scanned mail, receipts, and important papers all go here.
      </>
    ),
  },
  {
    title: 'Smart Home',
    body: (
      <>
        <a href="https://homeassistant.server.unarmedpuppy.com" target="_blank" rel="noopener noreferrer">Home Assistant</a> controls
        lights, automations, and connected devices.
      </>
    ),
  },
  {
    title: 'Security Cameras',
    body: (
      <>
        <a href="https://frigate.server.unarmedpuppy.com" target="_blank" rel="noopener noreferrer">Frigate</a> provides
        live camera feeds with AI-powered motion and person detection.
      </>
    ),
  },
  {
    title: 'Need Help?',
    body: (
      <>
        Check the <Link to="/reference/troubleshooting">troubleshooting page</Link> for common issues, text Joshua, or text Avery with questions.
      </>
    ),
  },
];

export default function GettingStartedPage() {
  return (
    <>
      <div className="clean-page-header">
        <h1 className="clean-page-title">Quick Reference</h1>
        <p className="clean-page-subtitle">What each service does and how to access it</p>
      </div>

      {cards.map((card) => (
        <div key={card.title} className="clean-ref-card">
          <div className="clean-ref-card-title">{card.title}</div>
          <div className="clean-ref-card-body">{card.body}</div>
        </div>
      ))}
    </>
  );
}
