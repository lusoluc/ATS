const fs = require('fs');

const files = [
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\cms\\categories\\route.ts',
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\cms\\files\\route.ts',
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\cms\\images\\route.ts',
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\cms\\jobs\\route.ts',
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\cms\\locations\\route.ts',
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\cms\\pages\\route.ts',
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\cms\\settings\\route.ts',
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\public\\job-alerts\\options\\route.ts',
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\public\\jobs\\route.ts',
  'c:\\Users\\Admin\\Desktop\\lv\\frontend\\src\\app\\api\\public\\nav\\route.ts'
];

for (const f of files) {
  if (fs.existsSync(f)) {
    let content = fs.readFileSync(f, 'utf8');
    if (!content.includes('force-dynamic')) {
      content = "export const dynamic = 'force-dynamic';\n" + content;
      fs.writeFileSync(f, content);
      console.log('Fixed', f);
    }
  }
}
