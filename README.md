# Medium Archive Viewer

This is a personal backup viewer for my Medium articles, ensuring my content is preserved and accessible in two places:
1. [Medium.com](https://medium.com) - Primary platform
2. This self-hosted archive - Secondary backup

The application automatically syncs with my Medium profile to maintain an up-to-date archive of all published articles. Built with Next.js, it provides a clean, modern interface for browsing and reading my articles.

## Features

- Complete backup of Medium articles
- Clean, responsive article viewer
- Tag-based navigation
- Search functionality
- Markdown content support

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Technology Stack

- **Framework**: [Next.js](https://nextjs.org)
- **Styling**: Tailwind CSS
- **Content**: Markdown with Medium API integration
- **Deployment**: Vercel

## Sync Process

The application includes a sync script (`syncMediumArchive.js`) that:
1. Fetches articles from Medium's API
2. Converts them to Markdown format
3. Stores them locally with metadata

## Updates

The archive is automatically updated whenever new content is published on Medium, ensuring this backup stays current.

## Deployment

This project is deployed on [Vercel](https://vercel.com), providing a fast and reliable browsing experience.
# medium-archive-viewer
