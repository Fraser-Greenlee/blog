---
aliases:
- /Large prior-free models/ML/Transformer-VAE/code/2020/08/25/Transformer-VAE-for-Program-Synthesis
categories:
- ML
- Large prior-free models
- code
- Transformer-VAE
date: '2020-08-25'
description: Find the right program in a latent space.
layout: post
title: Transformer-VAE-for-Program-Synthesis
toc: true

---

## Motivation

Since releasing a [Transformer Variational Autoencoder (T5-VAE)](https://fraser-greenlee.github.io/2020/08/13/Transformers-as-Variational-Autoencoders.html) I have been looking into using it as a tool for reasoning.

I think learning compressed latent spaces is the only form of abstraction deep learning systems are capable of. I think reasoning using these latent codes will be key for future systems.

{% include info.html text="T5-VAE reproduces sequences while compressing them into latent vectors with values between -1 and 1. Continuity between latent vectors is ensured, resulting in a semanticly organised space of sequences with each training sample corresponding to a position." type="primary" %}

Program synthesis involves creating a program to satisfy some input and output examples.
To search efficiently intermediate programs need to be evaluated so only relevent areas are searched.
This often involves scoring intermediate programs based on how close the output is to the correct one.
The search space is then constrained to programs that increase said score.

If the programs were represented by positions in latent space and a deep learning model predicted the output state, we would have a loss (against the target output) to evaluate the program effectiveness and use [Bayesian Optimisation](https://nbviewer.jupyter.org/github/krasserm/bayesian-machine-learning/blob/master/variational_autoencoder_opt.ipynb) to search the space.

To do this I'm developing a Python interpreter which uses T5-VAE's to represent code and state named "Latent Executor". Its currently in development but I'm excited to share what I've learnt so far.

## Architecture

The idea is to learn a semanticly organised map of code and state just by looking at tokens. This means the model should learn to organise programing concepts making the resulting space easier to search!

To do This T5-VAEs are trained to represent code and state. Their resulting encodings are concatenated and given to what I'm calling an executor which is a T5-encoder which maps the (state + code) encoding into the resulting state. This is then passed to the state autoencoder again to be decoded into the resulting state.

![![.](latent_executor.png "The Latent Executor")

## Initial Tests

The first test for this model was to learn to find the missing value in simple sums.
These were in the form `12+?=23` or `10+?=5`.

Here "state" represents the first value in the sum and the result (both being 2-digit positive integers) while "code" is the summed value (a 2-digit integer).

A small Latent Executor was made with T5-base encoders and decoders and a just 2 dimensional latent space.
By only using 2 latent dimensions the space of "programs" was easy to visualise.

Here are the resulting state and code latent spaces.

![![.](joint_latent_pos.png "Here darker values represent higher values from -99 to 99.")

Even though the model just sees abstract tokens it has still grouped numbers with similar values.
The code space looks better organised than the state space.
This is caused by a bug resulting from passing the executor's "Encoder Hidden" output back into the state autoencoder.
T5-VAE is an MMD-VAE meaning it computes its regularisation loss using the maximal mean divergence between its latent codes in a given batch and a sample of latent codes from a normal distribution. I forgot to combine the latent codes produced by the executor and those produced by the autoencoder leading to 2 seperate distributions of latent codes trying to ocupy the same space, hence the hole when sampling from state strings.

A varient with a 10-dimensional latent space was also trained and by using t-SNE with multiple perplexities we can see a similar orginisation of state and code.
Lower perplexities show local structure while high perplexities show global structure.

![![.](code_tsne.png "Code, note the similar split between small and large values.")

![![.](state_tsne.png "State, note the similar hole shape only visible at 100 perplexity.")

Since a continuous space of well organised code was found, it was time to try measuring the loss for different "programs" and check its accuracy.
The loss used was state-decoder cross entropy which gave the most reliable signal.

![![.](dec_ce_71m53eq18.png "Loss for the sum 71+?=18, the correct answer is -53.")

Looking at the loss, the lowest values (coloured white) are at or near -53.
You can also see that the space is not perfectly organised, -50 and -51 are at oposite ends of the y-axis.
If we were yo use gradient based optimisation (akin to rolling a ball down a hill) it would get stuck in one of the blue patches and likely not find the white patch at -53.
This means gradient-based optimisation won't be effective.

Another optimisation method seen in papers such as [SD-VAE](https://arxiv.org/abs/1802.08786) is bayesian optimisation with Gaussian Processes.
Using it reliably finds solutions using latent codes with 2, 10 and 100 dimensions.

## Next Steps

Although I'm excited to see it working here I want to extend this to handle multiple lines of code.
This means using the executors output with another code encoding to send to the executor and produce a new state.
That combined with a greater range of values should make a more interesting program synthesiser.
