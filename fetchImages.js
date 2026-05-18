const https = require('https');

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

https.get('https://Enterprise.de/', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    // Finde img-Tags und background-images
    const imgRegex = /<img[^>]+src="([^">]+)"/g;
    let match;
    const urls = new Set();
    while ((match = imgRegex.exec(data)) !== null) {
      urls.add(match[1]);
    }
    
    // Finde Typo3 fileadmin/ Pfade (typisch für solche Websites)
    const fileadminRegex = /(?:fileadmin|uploads)\/[a-zA-Z0-9_\-\.\/]+(?:jpg|jpeg|png|webp)/g;
    while ((match = fileadminRegex.exec(data)) !== null) {
      urls.add('/' + match[0]);
    }

    console.log("Gefundene Bild-URLs:");
    Array.from(urls).filter(u => u.match(/\.(jpg|jpeg|png|webp)$/i)).forEach(u => console.log(u));
  });
}).on('error', err => console.error(err));
