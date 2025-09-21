import postcss from 'postcss';
import tailwindcss from '@tailwindcss/postcss';
import autoprefixer from 'autoprefixer';
import fs from 'fs';

const inputCSS = fs.readFileSync('./static/src/tailwind.css', 'utf8');

postcss([tailwindcss, autoprefixer])
  .process(inputCSS, { from: './static/src/tailwind.css', to: './static/css/main.css' })
  .then(result => {
    fs.writeFileSync('./static/css/main.css', result.css);
    console.log('✅ Tailwind CSS built successfully!');
  })
  .catch(err => {
    console.error('❌ Build failed:', err);
  });