import { defineCollection, z } from 'astro:content';

const blogCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.date(),
    categories: z.array(z.string()).optional(),
    image: z.string().optional(),
    heroImage: z.string().optional(),
    draft: z.boolean().optional(),
  }),
});

export const collections = {
  'blog': blogCollection,
};