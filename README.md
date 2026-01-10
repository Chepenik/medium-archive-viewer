# Chep's Blog - Medium Archive

A personal archive of 1,400+ articles from my [Medium](https://medium.com/@chepenikconor) writing journey.

**Live site:** [chepsblog.com](https://chepsblog.com)

## Why This Exists

I made a commitment to write every day for the rest of my life, or until Medium goes out of business. After years of keeping that promise, I built this archive as a backup and a digital legacy.

Platforms come and go. Servers crash. Policies change. This archive ensures my thoughts live on in a format I control.

## About the Live Site

Due to the large number of articles (1,400+), the live site loads **20 articles at a time** for performance. Click "Load More" to see additional articles.

**Want to browse all articles?** Clone this repo and run it locally:

```bash
git clone https://github.com/Chepenik/medium-archive-viewer.git
cd medium-archive-viewer
npm install
npm run dev
```

Then visit `http://localhost:3000`

## What's Included

- Full archive of 1,400+ Medium articles
- Search functionality to find specific posts
- Metadata: publish date, reading time, tags
- Raw content stored in JSON format

## Tech Stack

- **Next.js 16** - React framework
- **Tailwind CSS** - Styling
- **Node.js sync script** - Pulls articles via [Unofficial Medium API](https://mediumapi.com)

## Keeping It Updated

The sync script fetches new articles I publish:

```bash
node syncMediumArchive.js
```

## Folder Structure

Articles are organized in `medium_archive_1/` and `medium_archive_2/` folders (max 900 files per folder for GitHub compatibility).

## Contact

- X/Twitter: [@ConorChepenik](https://x.com/ConorChepenik)
- LinkedIn: [conorchepenik](https://www.linkedin.com/in/conorchepenik/)

---

> You don't need permission to own your words.
