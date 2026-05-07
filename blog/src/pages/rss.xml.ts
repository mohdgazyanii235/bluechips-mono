import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  return rss({
    title: 'Bluechips London Blog',
    description: "Insights, safety guidance, and editorial from London's premium companion directory.",
    site: context.site!,
    items: posts
      .sort((a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf())
      .map((post) => ({
        title: post.data.title,
        description: post.data.description,
        pubDate: post.data.publishDate,
        link: `/${post.slug}/`,
        author: post.data.author,
        categories: post.data.tags,
      })),
    customData: '<language>en-GB</language>',
    stylesheet: false,
  });
}
