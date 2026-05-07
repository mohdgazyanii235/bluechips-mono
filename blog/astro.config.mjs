import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import tailwind from '@astrojs/tailwind';

// Blog deployed at blog.bluechips.live
export default defineConfig({
  site: 'https://blog.bluechips.live',
  output: 'static',
  integrations: [
    sitemap({
      filter: (page) => !page.includes('rss.xml'),
      changefreq: 'weekly',
      priority: 0.7,
    }),
    tailwind({
      applyBaseStyles: false,
    }),
  ],
  build: {
    inlineStylesheets: 'auto',
  },
  compressHTML: true,
});
