---
aliases:
- /Large prior-free models/ML/Transformer-VAE/2021/02/23/An-Improved-Transformer-VAE
categories:
- ML
- Large prior-free models
- Transformer-VAE
date: '2021-02-23'
description: An easy to use repo with SOTA performance.
layout: post
title: An-Improved-Transformer-VAE

---

![](0-6.png "Tranformer-VAE on MNIST pixels.")

I have made an improved Transformer-VAE that gives much more compelling interpolations on a wider range of tasks than my previous work [T5-VAE](https://fraser-greenlee.github.io/2020/08/13/Transformers-as-Variational-Autoencoders.html).
You can try out training in [Colab](https://colab.research.google.com/drive/1S8sUSkc_7ON00HDnse1MUXTTflo59VxA?usp=sharing) or check out the [source code](https://github.com/Fraser-Greenlee/transformer-vae).

In this post I'll describe the changes I made and what this has taught me about independent ML research.

1. TOC
{:toc}

## Motivation

As outlined in a [previous post](https://fraser-greenlee.github.io/2020/08/13/Transformers-as-Variational-Autoencoders.html) I think large transformer VAEs have a lot of potential.

They let you interpolate between pieces of data (text, images, etc) to find new and plausible combinations.
By interpolating between data points we can make machines creative.

Transformers are the most general type of neural network, able to get top results in images & text with few priors on the data.
This means a large scale Transformer-VAE will be able to create better interpolations than any other architecture.

With this in mind I set out to improve on my initial Transformer VAE.

## Baselines

To test performance I opted to judge the model on interpolation quality and how semantically organised the latent codes are.

To check the semantic organisation of the latent codes I used a [news headlines dataset](https://huggingface.co/datasets/Fraser/news-category-dataset) and trained an SVM on the latent codes to predict the news headline category.

For interpolation quality I looked at syntactic & semantic correctness.
Here I define syntax as a strict set of rules that all samples must follow (like those of a compiler), for semantics I mean that samples qualitatively appear to be a mix between one sample and the other.

The syntax test used this [python lines dataset](https://huggingface.co/datasets/Fraser/python-lines) and interpolations were tested for syntax errors.
For semantics I trained the model to recreate MNIST characters using [this dataset](https://huggingface.co/datasets/Fraser/mnist-text-small) and looked to see if the character mixes were credible.

## Improvements

Firstly I've swapped out the T5-encoder for the [Funnel transformer](https://arxiv.org/pdf/2006.03236.pdf) encoder (though still using the shared T5 embeddings).
The Funnel transformer is trained to compress sequence data so it doesn't have to use as many parameters to produce encodings.

Then I treat each funnel token as its own seperate latent code, this gives me more latent codes to use in the MMD loss.
This gives me more tokens to regularise which is important when the total batch size is low.

When creating the reconstructed encoding I use LayerNorm on the reconstructed tokens to match the Funnel encoder.

For handling large sequences I added gradient checkpointing and a basic window attention mechanism.

Gradient checkpointing simply ignores the gradients for most layers and recalculates then when backpropagating.
This can greatly help save memory and approximates the reversible layers of the Reformer which doesn’t have cross-attention.

Window attention only handles operates on subsequences of the data of length widow size.
Here I just feed each decoder layer subsequences of the data that overlap between layers.
In the future I could replace the self-attention layers with a Longformer self-attention followed by T5 cross attention on subsequences.

## Changes that didn't work out.

The key idea with Transformer-VAE is that by using a large transformer we can get a consistently valid output regardless of the latent code.
Currently interpolation performance doesn't clearly improve as the model gets more accurate.
I measure this by learning lines of Python code and measuring how often interpolations have syntax errors.

Here are some samples from my best traininig run (note that auto-encoding accuracy is 89% [all logs](https://wandb.ai/fraser/transformer-vae-tests/runs/e1r7vvru?workspace=user-fraser)):

```python
# ratio         sequence                                                valid

0             start_timeperiod = prev_timeperiod                        T
0.1           start_timeperiod = prev_timeperiod                        T
0.2           start_timeperiod = prev_timeperiod                        T
0.3           start_timeperiod = prev_timeperiod                        T
0.4           start_timeperios = prev_Infood                            T
0.5           return_qualos = min(vlabo)                                T
0.6           return summary_stats = min(balance))                      False
0.7           return summary_stats(balance))                            False
0.8           return summary_stats(balance))                            False
0.9           return summary_stats(balance))                            False
1             return summary_stats(balance))                            False

0             raise ValueError('Infinite observation encountered.')     T
0.1           raise ValueError('Infinite observation encountered.')     T
0.2           raise ValueError('Infinite observation encountered.')     T
0.3           raise ValueError('Infinite observation encountered.')     T
0.4           raise outError(' prefinite observation_type'.')           False
0.5           raise out('lert_typeREN_type'.)                           False
0.6           global outdir_type_type._type                             False
0.7           global outdir_type_type                                   T
0.8           global outdir_type_type                                   T
0.9           global outdir_type_type                                   T
1             global outdir_type_                                       T
```

Overall ~65% of interpolation points were valid.
Note that I did not use a Python specific tokenizer which means that some tokens will make syntax errors more likely.
One potential way to improve this is to optimize the interpolations directly.

I tried 3 methods of doing this, none substantially changed performance.

Critic loss had another funnel encoder operate on the final decoder hidden state to predict the interpolation ratio (inspired by the [adviserial interpolations paper](https://arxiv.org/pdf/1807.07543.pdf)).
The critic was accurate but it didn't improve the model.

Cycle loss put a cosine embedding loss on `latent VS Encoder(Decoder( latent ))`.
This is to encourage the latent space to become a bijective mapping.

Lastly I tried adding a smoothness loss where the gradient of the logits w.r.t the interpolation ratio was minimized.

Both of the above methods were inspired by [this paper](https://arxiv.org/pdf/2008.01487.pdf).

Unfortunately I didn't learn a great deal from these methods, they just didn't update the model that much or lowered performance.
This is likely because these methods were original applied to image models where the data is less discrete.
Current SOTA for training text transformers with an adversary is by using reinforcement learning which I wanted to stay away from as it would necessitate longer training times.

## Conculsion

Overall this project took wayyy longer than I expected.
In the future I'm going to try to work more incrementally, making small, test-able experiments at a time.

**Tips for your own research side project:**
- Remember that choosing the right thing to work on is more important than running experiments and writing code.
- Start by setting up a small test of your hypothesis, this should be a baseline with a performance metric.
- Stay small, reuse open-source code & data where possible and do fast runs on Google Colab.
- Lean on the side of caution when trying out a new method. Read related papers where possible so you can skip on less promising ideas.

If you want to see even more results you can check out this [Weights and Biasis report](https://wandb.ai/fraser/transformer-vae-tests/reports/-WIP-Transformer-VAE-Performance-overview---Vmlldzo0MTQ1OTc).
I hope to release some cool demos using this project soon!
If you want to help out feel free to reach out to [@FraserGreenlee](https://twitter.com/FraserGreenlee).

There is a ton of ideas yet to be explored using this project!
* What would an [ArtBreeder](https://www.artbreeder.com) of sequences be like? Could it create compelling writing prompts via interpolation?
* Can semantic directions in latent space be found so you can edit texts at a high level?
* Does part of the latent codes encode style? If so can that style be applied to other sequences?
* The model has a prior on the distribution of latent codes, could that be replaced by a more general loss?
* I was keen on smooth latent codes as I hoped to take advantage of their differentiability. Now discrete VQ-VAEs are shown to achieve great results why not look into converting this project into one?
