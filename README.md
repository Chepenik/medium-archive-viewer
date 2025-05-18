# 📰 Medium Archive: Personal Blog Backup

Welcome to the local archive of my [Medium](https://medium.com/@chepenikconor) writings — a personal initiative to preserve my work outside of any platform's control.

## 🧠 Why This Exists

As someone who's written consistently on Medium, I began to realize the risk of having all my content in one place. Platforms come and go. Servers crash. Policies change.

This archive ensures that even if Medium goes offline tomorrow, my thoughts, reflections, and essays will live on both here in github, as well as on my personal machine in a format I control.

## 🗃️ What's Included

- ✅ **Full archive** of my Medium articles in a clean, browsable format  
- 🔎 **Search functionality** to quickly find specific posts or keywords  
- 📅 **Metadata** like publish date, estimated read time, and claps  
- 📄 **Raw content** stored in its original form (Markdown / JSON)  

## 🧰 The Tech Behind It

This site is powered by a custom script and lightweight frontend. Here's what's happening under the hood:

- **Node.js script** pulls my articles using the [Unofficial Medium API](https://mediumapi.com)
- **Fetches my Medium user ID** based on my profile handle
- **Retrieves all article IDs**, paginating through my full history
- **Downloads metadata and full content** for each post
- **Stores everything in structured JSON files** in the `/public/archive/` folder
- **Renders articles** in a simple Next.js interface

All of this was developed with the help of AI tools and a love for open information.

## 🔁 Keeping It Updated

The script is designed to be re-run periodically, fetching any new articles I publish and appending them to the archive.

- Manual sync: `node syncMediumArchive.js`
- (Optional) I could add a cron job or GitHub Action to automate daily or weekly syncs and maybe I will one day.

## 🤝 Special Thanks

Big thanks to the developers behind the [Unofficial Medium API](https://mediumapi.com/documentation.html) for making this project possible.

---

> ⚠️ Note: This project is personal, but it's also a signal — you don't need permission to own your words.

---

## 📬 Contact

If you want to reach out, DM me on X: [x.com/conorchepenik](https://x.com/conorchepenik)
