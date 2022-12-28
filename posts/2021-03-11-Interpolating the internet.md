---
aliases:
- /ML/2021/03/11/Interpolating the internet
categories:
- ML
date: '2021-03-11'
description: What happens when every plausible idea is an inference away.
hide: false
layout: post
title: Interpolating the internet
toc: false

---

Large scale Deep Learning models can combine abstract concepts in new ways.
[GPT-3](https://openai.com/blog/openai-api/) can write stories while [DALL·E](https://openai.com/blog/DALL·E/) makes images.
These models are improving fast so I want to explore what improved versions will do and how they will change the internet.

## The best content generation today

The best AI content generators use large models trained on huge datasets.

These models work by storing all their training data in a "latent space"[^1].
Think of this as a map where content is arranged by its properties (e.g. going left words get angrier, pictures become more cat like as you move up, etc).
To create new content we can simply adjust our positions to get new combinations of properties.

![.]({{ site.baseurl }}/images/face_interpolation.jpg "Moving between 2 real faces in latent space.")

Unlike Google Search which stores links and searches for results, a deep learning model combines aspects of existing content to make new results.
A great example of this is DALL·E which works like Google image search on steroids, interpolating between relevent results rather than indexing them.

Both are results for the prompt "a road sign with an image of a blue strawberry":

![![.]({{ site.baseurl }}/images/Google a road sign with an image of a blue strawberry.png)]({{ site.baseurl }}/images/Google a road sign with an image of a blue strawberry.png "Google")

![![.]({{ site.baseurl }}/images/DALL-E a road sign with an image of a blue strawberry.png)]({{ site.baseurl }}/images/DALL-E a road sign with an image of a blue strawberry.png "DALL·E")

Notice that Google's results are not relevent.
It is perfectly plausible for their to be "a road sign with an image of a blue strawberry" but there aren't many on the internet.

Meanwhile every one of DALL·E's generations are relevent.
Of course producing these outputs currently takes a long time and is expensive but this tech is [scaling fast](https://arxiv.org/abs/2001.08361).

A similar phenomenon is playing out with text.

GPT-3 is trained to complete text prompts.
Here ideas and concepts can be merged to reason & write stories like in this hilarious example:

{% twitter https://twitter.com/jonathanfly/status/1284082774325039105 %}

Already people are [generating articles](https://liamp.substack.com/p/my-gpt-3-blog-got-26-thousand-visitors) using GPT-3 by giving manual prompts.

It is important to keep in mind that GPT-3 and DALL·E are almost the same model.
They both use a large transformer with DALL·E using a VQ-VAE to compress images into token-like sequences.
You can think of this as a learned compiler for images with GPT-3 acting as the programmer.

This means we can apply the DALL·E format `{content search query} {VQ-VAE tokens}` to any form of data.
Expect VQ-VAEs to allow a future GPT model to generate any form of content letting it generate full rendered web pages rather then just text.

## How will these models improve?

The large datasets training these models are the same ones used by search engines.

When we search today we hope someone has made something just like what we're looking fo.
With a large scale deep learning model that won't be the case.

Instead a search could query a large model thats interpolates between the best results to find that image, article, video, etc that exactly matches your query.

Once these "Generators" become mainstream we're going to have to change our perspective on what the internet is.

We will no longer think of something being on or off the internet.
The idea that someone has their "nudes posted online" will be a meaningless phrase as you will inevitably generate nudes as you search for them.

The only value in "making" images will be in finding the right one, to search latent space to best fulfil someones needs.

Most content will be generated on demand to a users needs but some will be automated, expect Spotify & YouTube to take full advantage of their huge datasets to create content.

Having these generators will feel imensly powerful, finaly I'll get to make a [water bending VR game](/fastpages/games/simulation/2020/07/08/An-Avatar-game-with-realistic-physics.html), the amount of content posted online will tenfold!

Eventually a new internet will emerge.
One where rather than searching for a peice of content hand-made by a person, all content is generated to suit our individual needs.
This will feel like we each have our own internet.
One where all content matches just what we want.

## What you can do now.

If we are on the cusp of a new Google how can you take advantage of this?
The best thing to do is get involved on early AI content generation tools.
Some of these are completely autonomous and some require a human in the loop.
Here are some ideas I've been considering.

### Transformer-VAEs as a search engine

To make a new Google your probably going to need a [Transformer-VAE](https://github.com/Fraser-Greenlee/transformer-vae).

I've just released a project that allows using the transformer to interpolate over text and small images.
Hopefully once I try training at scale I'll be able to interpolate over entire documents.

Once it can interpolate over entire documents why not use it with a search engine to interpolate between the top results to best match a query?

### Auto ArtBreeder

[ArtBreeder](https://www.artbreeder.com) uses a mix of VAE's & GAN's to generate images by combining latent variables of existing images to interpolate between them.
Images are interpolated several times over to generate novel and strickingly different images.

This is different to most content generators in that you can't see an output image and easily know how to find it in latent space.
In the future algorithms will be needed to discover new images in these spaces ([see Kenith Stanley's interview for more info](https://youtu.be/lhYGXYeMq_E)).
Perhaps processing interpolated images with OpenAI's new CLIP model will allow discovering new images?

The final result would allow for fully automanus brainstorming.
Use this to prompt a larger model and you could get some compelling & creative outputs.

### Other Ideas

These ideas work great for very flexible mediums like images and text where slight mstakes can go unnoticed.

Could some clever fixes allow applying them to strict domains like program synthesis?
Maybe you could use latent variables to add/remove concepts in a Python function?

## Footnotes

[^1]: Since these models are trained with gradient descent they approximate non-parametric models (a.k.a. models that reason from their dataset rather than learning programs) [see more here](https://arxiv.org/abs/2012.00152).
