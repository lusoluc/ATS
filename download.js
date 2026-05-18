const https = require('https');
const fs = require('fs');
const path = require('path');

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const imagesToDownload = [
  { url: 'https://Enterprise.de/fileadmin/media/Header/Enterprise-Header-Startseite-Slider-04-Desktop.jpg', dest: 'hero_team.png' },
  { url: 'https://Enterprise.de/fileadmin/_processed_/9/c/csm_Enterprise-Website-Startseite-Teaser-Pflege_4bf729064b.jpg', dest: 'nursing_care.png' },
  { url: 'https://Enterprise.de/fileadmin/_processed_/8/4/csm_Enterprise-Website-Startseite-Teaser-Karriere_cceb17c74c.jpg', dest: 'apprenticeship.png' }
];

imagesToDownload.forEach(img => {
  const destPath = path.join(__dirname, 'frontend', 'public', img.dest);
  const file = fs.createWriteStream(destPath);
  https.get(img.url, (res) => {
    res.pipe(file);
    file.on('finish', () => {
      file.close();
      console.log(`Downloaded ${img.url} to ${destPath}`);
    });
  }).on('error', (err) => {
    fs.unlink(destPath, () => {});
    console.error(`Error downloading ${img.url}: ${err.message}`);
  });
});
