require('dotenv').config();
const axios = require('axios');
const fs = require('fs');
const path = require('path');

if (!process.env.MEDIUM_API_KEY) {
  console.error('Error: MEDIUM_API_KEY is not set in .env file');
  process.exit(1);
}

if (!process.env.MEDIUM_USERNAME) {
  console.error('Error: MEDIUM_USERNAME is not set in .env file');
  process.exit(1);
}

// API call tracking
const apiStats = {
  getUserId: 0,
  getArticleList: 0,
  getArticleInfo: 0,
  getArticleMarkdown: 0,
  get total() {
    return this.getUserId + this.getArticleList + this.getArticleInfo + this.getArticleMarkdown;
  }
};

const HEADERS = {
  'x-rapidapi-key': process.env.MEDIUM_API_KEY,
  'x-rapidapi-host': 'medium2.p.rapidapi.com'
};

const baseURL = 'https://medium2.p.rapidapi.com';
const MAX_FILES_PER_FOLDER = 900;

// Find or create the appropriate archive folder
function getArchiveFolder() {
  let folderNum = 1;
  while (true) {
    const folderName = `medium_archive_${folderNum}`;
    const folderPath = path.join(__dirname, folderName);

    if (!fs.existsSync(folderPath)) {
      fs.mkdirSync(folderPath);
      return folderPath;
    }

    const files = fs.readdirSync(folderPath).filter(f => f.endsWith('.json'));
    if (files.length < MAX_FILES_PER_FOLDER) {
      return folderPath;
    }

    folderNum++;
  }
}

// Check if article exists in any archive folder
function articleExists(articleId) {
  let folderNum = 1;
  while (true) {
    const folderName = `medium_archive_${folderNum}`;
    const folderPath = path.join(__dirname, folderName);

    if (!fs.existsSync(folderPath)) {
      return false;
    }

    const filePath = path.join(folderPath, `${articleId}.json`);
    if (fs.existsSync(filePath)) {
      return true;
    }

    folderNum++;
  }
}

async function getUserId(username) {
  try {
    console.log(`Fetching user ID for: ${username}`);
    const url = `${baseURL}/user/id_for/${username}`;
    apiStats.getUserId++;
    const res = await axios.get(url, { headers: HEADERS });
    console.log('User ID response:', res.data);
    if (!res.data.id) {
      throw new Error('No user ID found in response');
    }
    return res.data.id;
  } catch (error) {
    console.error('Error fetching user ID:', error.response?.data || error.message);
    throw error;
  }
}

async function getAllArticles(userId) {
  try {
    console.log(`Fetching all articles for user ID: ${userId}`);
    let url = `${baseURL}/user/${userId}/articles`;
    let allIds = new Set();
    let retryCount = 0;
    const maxRetries = 3;

    while (url && retryCount < maxRetries) {
      try {
        apiStats.getArticleList++;
        const res = await axios.get(url, { headers: HEADERS });
        const articleIds = res.data.associated_articles || [];
        console.log(`Got batch of ${articleIds.length} articles (API calls so far: ${apiStats.total})`);
        
        // Add new articles to set to avoid duplicates
        articleIds.forEach(id => allIds.add(id));
        
        // If we have the next token, continue fetching
        if (res.data.next) {
          url = `${baseURL}/user/${userId}/articles?next=${res.data.next}`;
          // Add delay between requests
          await new Promise(resolve => setTimeout(resolve, 2000));
        } else {
          url = null;
        }
      } catch (error) {
        console.error('Error in pagination:', error.message);
        retryCount++;
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }
    
    console.log(`Total unique articles found: ${allIds.size}`);
    return Array.from(allIds);
  } catch (error) {
    console.error('Error fetching all articles:', error.response?.data || error.message);
    return [];
  }
}

async function getArticleData(articleId) {
  try {
    console.log(`Fetching data for article: ${articleId}`);
    const infoUrl = `${baseURL}/article/${articleId}`;
    const contentUrl = `${baseURL}/article/${articleId}/markdown`;

    apiStats.getArticleInfo++;
    apiStats.getArticleMarkdown++;
    const [infoRes, contentRes] = await Promise.all([
      axios.get(infoUrl, { headers: HEADERS }),
      axios.get(contentUrl, { headers: HEADERS }),
    ]);

    return {
      id: articleId,
      title: infoRes.data.title,
      createdAt: infoRes.data.published_at || infoRes.data.createdAt,
      tags: infoRes.data.tags || [],
      url: infoRes.data.url,
      content: contentRes.data.markdown,
      wordCount: infoRes.data.word_count,
      readingTime: infoRes.data.reading_time,
      claps: infoRes.data.claps,
      voters: infoRes.data.voters
    };
  } catch (error) {
    console.error(`Error fetching article data for ${articleId}:`, error.response?.data || error.message);
    throw error;
  }
}

async function archiveMediumPosts() {
  try {
    console.log('Starting Medium archive process...');
    const userId = await getUserId(process.env.MEDIUM_USERNAME);
    console.log('Got user ID:', userId);

    // Get all articles
    const articleIds = await getAllArticles(userId);

    if (articleIds.length === 0) {
      throw new Error('No articles found for this user');
    }

    console.log(`Found ${articleIds.length} articles to process`);
    let savedCount = 0;
    let skippedCount = 0;

    for (let id of articleIds) {
      // Check if article already exists in any folder
      if (articleExists(id)) {
        console.log(`Skipping existing article ${id}`);
        skippedCount++;
        continue;
      }

      try {
        const article = await getArticleData(id);
        // Get the appropriate folder (auto-creates new one if current is full)
        const dataDir = getArchiveFolder();
        const filepath = path.join(dataDir, `${id}.json`);
        fs.writeFileSync(filepath, JSON.stringify(article, null, 2));
        console.log(`Saved article: ${article.title} -> ${path.basename(dataDir)}`);
        savedCount++;

        // Add a longer delay between requests to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 2000));
      } catch (error) {
        console.error(`Failed to save article ${id}:`, error.message);
        // Add retry delay if we hit an error
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }

    console.log('\n=== Archive Summary ===');
    console.log(`Articles saved: ${savedCount}`);
    console.log(`Articles skipped (already exist): ${skippedCount}`);
    console.log('\n=== API Call Summary ===');
    console.log(`Total API calls: ${apiStats.total}`);
    console.log(`  - getUserId: ${apiStats.getUserId}`);
    console.log(`  - getArticleList: ${apiStats.getArticleList}`);
    console.log(`  - getArticleInfo: ${apiStats.getArticleInfo}`);
    console.log(`  - getArticleMarkdown: ${apiStats.getArticleMarkdown}`);
  } catch (error) {
    console.error('Archive process failed:', error.message);
    console.log('\n=== API Call Summary (on error) ===');
    console.log(`Total API calls: ${apiStats.total}`);
  }
}

archiveMediumPosts().catch(console.error);
