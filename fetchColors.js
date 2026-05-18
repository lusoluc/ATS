const https = require('https');

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

https.get('https://landesverein.de/', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const regex = /#[0-9a-fA-F]{6}/g;
    const matches = data.match(regex) || [];
    const counts = {};
    matches.forEach(m => {
      const upper = m.toUpperCase();
      counts[upper] = (counts[upper] || 0) + 1;
    });
    const sorted = Object.entries(counts).sort((a,b) => b[1] - a[1]).slice(0, 20);
    console.log("Top Hex Colors on landesverein.de:");
    sorted.forEach(([color, count]) => console.log(`${color}: ${count} times`));
  });
}).on('error', err => console.error(err));
