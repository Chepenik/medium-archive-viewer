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

const HEADERS = {
  'x-rapidapi-key': process.env.MEDIUM_API_KEY,
  'x-rapidapi-host': 'medium2.p.rapidapi.com'
};

const baseURL = 'https://medium2.p.rapidapi.com';
const dataDir = path.join(__dirname, 'medium_archive');
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir);

async function getUserId(username) {
  try {
    console.log(`Fetching user ID for: ${username}`);
    const url = `${baseURL}/user/id_for/${username}`;
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
        const res = await axios.get(url, { headers: HEADERS });
        const articleIds = res.data.associated_articles || [];
        console.log(`Got batch of ${articleIds.length} articles`);
        
        // Add new articles to set to avoid duplicates
        articleIds.forEach(id => allIds.add(id));
        
        // If we have the next token and haven't reached our target, continue
        if (res.data.next && allIds.size < 50) {
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
    
    for (let id of articleIds) {
      const filepath = path.join(dataDir, `${id}.json`);
      if (fs.existsSync(filepath)) {
        console.log(`Skipping existing article ${id}`);
        continue;
      }
      
      try {
        const article = await getArticleData(id);
        fs.writeFileSync(filepath, JSON.stringify(article, null, 2));
        console.log(`Saved article: ${article.title}`);
        
        // Add a longer delay between requests to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 2000));
      } catch (error) {
        console.error(`Failed to save article ${id}:`, error.message);
        // Add retry delay if we hit an error
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }
    
    console.log('Archive process complete!');
  } catch (error) {
    console.error('Archive process failed:', error.message);
  }
}

archiveMediumPosts().catch(console.error);
