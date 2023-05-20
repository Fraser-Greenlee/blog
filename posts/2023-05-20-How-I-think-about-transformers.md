# How I think about transformers.

People think about Large Language Models (LLMs) in a variety of different ways.
This can lead to imaging LLMs have magical capabilities like being able to invent its own compression language.

<embed tweet>

While others think LLMs are far more limited than they actually are.

<embed chollet tweet with the riddle>

I think the industry has yet to find the correct philisophical grounding for whats going on here but I think the answer is clear.
In this post I'll describe how I think about these models and what my own philophies implications are.

## How deep learning models work

I think F'Chollet has the clearest understanding of how all deep learning methods work.
This is best described in his book Deep Learning with Python but for a shorter read I reccomend you read his post [The limitations of deep learning](https://blog.keras.io/the-limitations-of-deep-learning.html).

The TL;DR is this: Deep Learning methods work by learning a point-by-point mapping of their input data to their labels.
You can think of this as unfolding a sheet of scrumpled up paper with each layer applying a different un-folding.
This unfolding occurs until we have a flat sheet of paper and at that point are class labels are clearly seperated making our classifier work.

Understand that this mapping is point-by-point, it cannot handle examples that are far out of its training distribution.

## Transformers are databases, maps and recrodings.

Transformers work in just the same way.

They are a database of natural language knowledge and capabilities.
This database is stored in embedding space which you can plot.

<plot embedding space>

If our fine-tuning and eval datsets do not overlap we'll get worse performance there.
This is because our model has fewer nearbye examples to go on.

What is unique about LLMs is that they do not just map `input sequnce -> finished output sequence`, they sample their output one token at a time.
This makes the transformer a recording of natural language that can come to life by leveraging nearbye exampels in embedding space.

## The Chollet Domain

With this in mind we can now understand that tasks where the model must know the right answer when it samples its first token has completely different properties to tasks where the model can gradually come to a conclusion after several tokens.

I refer to tasks where the model must immediately know the right answers as being in the "Chollet Domain".
In this domain of tasks LLMs behave exactly how F'Chollet predicted they would.

These tasks include:
1. Classification
2. Arithmetic
3. Generic Question Answering
4. Extraction

In these tasks we see brittle levels of performance with models requiring fine-tuning data with each sample.

To make this concrete here's an embedding map of requests with a train and test split:

<train/test embed of Chollet domain tasks>

Now lets plot test-set performance on this embedding plot.

<test set accuracy with green = good and red = bad>

As you can see the fall off in performance here is very steep.

## The Reasoning Domain

I refer to tasks where the model gradually writes its answer as being in the "Reasoning Domain".
This domain does not behave how F'Chollet predicted.

These tasks include:
1. Copywriting
2. Summarization
3. Chain of though reasoning
4. Programming
5. Specific Question Answering
6. Agentic tasks like BabyAGI

In these tasks The model can generalize further outside of its training distribution.

To make this concrete here's an embedding map of requests with a train and test split:

<train/test embed of Reasoning domain tasks>

Now lets plot test-set performance on this embedding plot.

<test set accuracy with green = good and red = bad>

As you can see the fall off in performance is much more gradual.

So what is happening here?

### Reasoning, the final frontier

With each token, the model has to stay within its training distribution but this only has to apply for local updates.
So each sentence must be within the map of embeddings their combination can be unique.

You can think of this chain of tokens as building a bridge to other answers.

You can also think of this as a programming language.
With more training data we add more capabilities to our language.
Eventually the moddel can both write and read its own instructions.

This ability to reason allows for extreme generalization and is the most exciting thing happening in ML right now.

When the model reasons its essentially got a database of different techniques and an intuition of which technique to use when.

## The Future of Transformers

I think this reasoning capability is really exciting and under-utilized.

What if we trained a transformer to just act within this reasoning domain and leave out the Chollet domain entirely?

This transformer would generlize much further and not require as much infrastructure.
