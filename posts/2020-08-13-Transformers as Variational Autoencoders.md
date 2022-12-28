---
aliases:
- /Large prior-free models/ML/Transformer-VAE/2020/08/13/Transformers as Variational
  Autoencoders
categories:
- ML
- Large prior-free models
- Transformer-VAE
date: '2020-08-13'
description: Avoid posterior collapse even with a huge model.
layout: post
title: Transformers as Variational Autoencoders

---

Image generators based on Variational Autoencoders have had huge success.
Unfortunately the same cannot be said for sequence generation.
There seems to be little interest in this space but with Transformers it is now possible to learn smooth latent spaces of large structured sequences.

To show this I'm releasing [T5-VAE](https://github.com/Fraser-Greenlee/T5-VAE) a mod of Google's [Text-to-Text Transformer](https://ai.googleblog.com/2020/02/exploring-transfer-learning-with-t5.html) to learn smooth latent spaces of sequences.

[Try using it in Google Colab.](https://colab.research.google.com/drive/126LRvBzTt4c5jqwn2PMq6NQ1sqiVsI_2?usp=sharing)

[See Weights & Biasis training runs.](https://app.wandb.ai/fraser/T5-VAE?workspace=user-fraser)

[Check out the source code on GitHub.](https://github.com/Fraser-Greenlee/T5-VAE)

1. TOC
{:toc}

## From Autoencoders to MMD-VAE

To understand how this works and the ways it differs from previous systems, it is important to know how an autoencoder works, specifically a Maximum Mean Discrepancy Variational Autoencoder.

[![.]({{ site.baseurl }}/images/prog_synth/autoencoder.png)]({{ site.baseurl }}/images/prog_synth/autoencoder.png)

An Autoencoder learns to recreate its training data by compressing the data into a compressed representation called a "latent code" and decompressing it back into the original data.
Each latent code is just a vector of numbers with each number constrained within some bounds (between -1, 1 in this case by a [Tanh function](https://pytorch.org/docs/stable/generated/torch.nn.Tanh.html#torch.nn.Tanh)).
You can think of each latent vector as a position on a latent map of input data.
In each direction on the map our input data changes in semantic ways.

The problem with an Autoencoder is that our latent map has holes.
These holes are where latent codes have no set meaning and so result in garbage output from the decoder.
To resolve this we use a Variational Autoencoder (VAE).
It has a regularising loss function which encourages a smooth distribution of latent codes.
This regularising loss encourages our latent codes to match a target probability distribution, usually a bell curve.
Now intermediate points on our map are also valid points meaning we can traverse it smoothly.

Unfortunately, when applying this model to sequences it doesn't work.
The issue comes from our extra loss function and how we decode sequences.

Our regularising loss encourages the latent space to be smoother but if the loss is brought to near zero the space becomes meaningless.
This is tempered by the reconstruction loss which encourages the latent space to be informative.
If the decoder is generating a sequence, it has access to the previous tokens in its current sequence which during training are always correct.
When the decoder has the option of a slightly random latent code or a nonrandom previous output it ignores the latent code & just looks at its previous tokens.

This is known as "posterior collapse" since the posterior is the probability of an event (the next token) given relevant information (the latent code).
The resulting model ignores the latent code and so just models a prior distribution of tokens.

To solve this the Maximum Mean Discrepancy Variational Autoencoder was made.
It is similar to a VAE but instead of the reconstruction loss, it uses an MMD (mean-maximum-discrepancy) loss.
The MMD loss measures the similarity between latent codes, between samples from the target distribution and between both latent codes & samples.
It optimises the similarity between latent codes & target samples separately to match the similarity between mixed samples.

This loss is much softer on the latest codes and solved posterior collapse for my use case.
If your keen to learn more about MMD-VAE you should check out [this post](https://ermongroup.github.io/blog/a-tutorial-on-mmd-variational-autoencoders/).

## A Transformer as an MMD-VAE

Lets put this model to use to generate some structured sequences.
The [T5 model](https://huggingface.co/transformers/model_doc/t5.html) provided by Huggingface will create the Encoder & Decoder for the sequences. To get a compressed encoding of the inputs, the inputs are first padded to ensure each the sequence is 12 tokens long. Finally, some fully-connected layers compress and then decompress the fixed length encodings. I've named this model “T5-VAE”.

[![.]({{ site.baseurl }}/images/prog_synth/t5-vae.png)]({{ site.baseurl }}/images/prog_synth/t5-vae.png)

This model is then trained to recreate its input tokens with the MMD loss on its latent code. Once training is complete it is possible to start generating some sequences!

I tried out recreating single lines of code from my dataset of [9 million Python state changes](https://www.kaggle.com/frasergreenlee/python-state-changes).
This code comes from real coding solutions so the model will learn more useful snippets of code than if the data was random.
However, this also means the code snippets could be more varied.

Here I step through the latent space between 2 sample code snippets.

```bash
# Intermediate Samples
0.0 x = a - 1; # Starting latent space
0.1 x = a - 1;
0.2 x = a - 1;
0.3 x = a - 1;
0.4 x = a + 1;
0.5 x = a + 2;
0.6 x = a + 2;
0.7 x = a + 2 * 2;
0.8 x = a + 10 * 2;
0.9 x = a + 10 * 2;
1.0 x = a + 10 * 2; # Ending latent space
```

Here I randomly generate latent codes to see how common syntax errors are.

```bash
# Randomly Sampled Sequences
er = int(h[3] * 0);
l.append([False[j] * d); # Invalid Code
y = '[0 '] = 1; # Invalid Code
x = int(h[-1] * 0);
l.append( = 0 + str(x[0 / 1]); # Invalid Code
x.append(a[da] * 0);
x =''[0 - 1:0];
x.append(x.pop(  + 1) ** 0);
f = int(h[i].pop() + 1);
x = int(h[-1 - 1]);
```

Though the intermediate values are good, just randomly sampling from the latent space occasionally produces invalid outputs.

## Use cases

Now that we can learn smooth latent spaces of sequences a lot is possible:

* **Learn a position in latent space**

  * Train another model take T5-VAE encodings (e.g. representing a tweet) and predict some property (e.g. the number of likes).
Now you can get a loss based on your target number of likes and backpropagate that loss to change the latent position of a given tweet.
The result should be a tweet optimizer! I've got a demo of this coming soon.

* **Discover semantic changes in latent space**

  * Change a sequence in one way (e.g. change the tone) and find the difference in latent space.
You may be able to apply that change in latent space to other sequences to get a tone changer.
