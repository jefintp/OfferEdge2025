import postcss from 'postcss';
import tailwindcss from 'tailwindcss';  // ✅ Correct package
import autoprefixer from 'autoprefixer';
import fs from 'fs';

const inputCSS = fs.readFileSync('./Static/src/tailwind.css', 'utf8');

postcss([tailwindcss, autoprefixer])
  .process(inputCSS, { from: './Static/src/tailwind.css', to: './Static/css/main.css' })
  .then(result => {
    fs.writeFileSync('./Static/css/main.css', result.css);
    console.log('✅ Tailwind CSS built successfully!');
  })
  .catch(err => {
    console.error('❌ Build failed:', err);
  });