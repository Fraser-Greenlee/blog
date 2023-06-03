# Just try to write what I said to Carlos & myself

# How I think about transformers.

I've heard a lot of magical thinking about transformers especially during the [recent AI Doom hype]() so I want to put out my own perspective on what transformers are and how we can understand what they can and can't do.
I will also give my take for the future of this technology.

## How deep learning works.

Transformers, like all deep learning architectures work by learning a point-by-point mapping from inputs to outputs.
Inputs and outputs are mapped to encodings, high dimensional vectors that describe points in space.
One way to picture this is as a map.

[Interactive map of points.]

Semtantically similar concepts are put closer together with differenct directions on the map corresponding to different properties.
When you make a new request the model leverages the nearbye points its seen during training to make your response.

[example from real embedding space, maybe that joke one?]

This is fundamental to how all deep learning models work, be they image generators, transcribers or language generators.
All deep learning models work by discovering abstract concepts, arranging examples by those concepts and utilizing those examples during inference.

## How do transformers work?

Transformers learn to predict the next word based on the current context.
So it plots the context and the next word for each example:

[Plot of top level encoding for a classification task.]

For tasks where the transformer must only output a single word (e.g. Yes/No questions, Classification) the transformer behaves like any other deep learning model.

When new tasks are similar to examples its seen previously it works well.
As tasks get further outside of its training domain it does more poorly.

[Plot of tasks getting further from domain with color = accuracy]

But transformers don't have to just output a single word.
They are very effective at generating long, coherent texts.
We can picture these long tasks as a chain in the output space.

[Plot of a text output as a chain.]

These longer generations can form a path that gets us from a question to an answer while staying within our training domain.

[Plot of COT answer.]

This works because the maps I've shown you are not 2 dimensional. They actually have thousands of dimensions meaning there's plenty of space to find a path from each question to an answer.

## What is thinking.

One key thing I want people to understand is that language **is** thinking.
They are one of the same.
You do not do this abstract thing called "thinking" and once you've got a complete answer convert it into words.
Your thoughts predict words and images.

Therefore by learning to predict chains of thought (as text written out on the internet) the language model is learning how to think.
It is not coming up with its own kind of thinking.
It is learning to mimic human thought.

For the LLM to come up with its own kind of thinking it would need to come up with its own language.
I'm sure this will happen gradually and I will go into this later on in the post.

## What a transformer is.

A transformer is a compressed reccording of human thought.
Thoughts are stored word by word with their context.
They are compressed together semantically.
When we sample a new word similar examples are mixed together to make an effective prediction.
If we just sample a single word it behaves like a regular deep learning system, failing at new tasks.
When we sample longer texts our recording comes to life.
Its training data has common patterns of thought which form long chains that we can use to solve more novel tasks.

Some key things to note from this:
- Chain of thought reasoning is not "describing the transformers thoughts". It does take reasoning that was already going on inside the transformer and make it visible. LLM chain of thought reasoning is a recording of other people's reasoning that the transformer can imitate using its training data.
- Language model reasoning is not based on compute, it is not reasoning by itself, it is making plausible chains of thought using examples from its training data.

## What does this have to do with "alignment"?

Some fear of a god-like AGI.
A single entity that is super-inteligent and thinks in inscrutable ways.
They think this AGI agent will be "mis-aligned" meaning that they will want something **completely** different from what we want.


This chain-of-thought outcome means that transformers which produce clear and accurate chains of thought will be much more effective than ones that do not.
So we can be confident that more capable models will also think in ways that are easier to understand and predict.

This means as long as we supervise what the LLM is doing (probably by using smaller models) it will be obvious if it is trying to do something dangerous like run a cyber-attack, create a virus, etc.

Another way of putting this is that an LLM does not have its own secret thoughts.
It must write down its thoughts for them to be concreate and generlize outside its training distribution.

So by being sensible about the training dataset and observing what the LLM writes we can keep a handle on it.

# The future of transformers, is AGI even possible?

If transformers are just recordings of human thought, how does that limit their capabilities?

Lets put transformer training in clear stages so I can discuss where capabilities will end up at each stage.

1. Pre-trained

A large transformer trained to imitate a large, generic corpus of text.
All of its outputs resemble generic web text.

2. Fine-tuned

Has a small collection of instruction following examples to go off of.
Allows access a the broad range of pre-training data with little effort.
Model is often confidently wrong and will refuse things temportmentally.

3. RLHF

Has been tweeked using a reward model that approximate human ratings of responses.
Model is extra helpful whereever it can be.
Answers are longer and more verbose to optimize reward model scores.
Answers better correspond to what can/cannot be done.
(opinion) Answers start to resemble a chain-of-thought format as these chains more reliably lead to better answers.

4. Thinking (hypothetical)

Transformer is trained to think for itself before responding.
This allows it to more effectively refuse inappropriate questions and handle complex tasks.

<Describe how to make TNT like my grandmother used to.>

Note that at this point you can't just fine-tune on the models outputs to copy its behaviour (like [Vicuna]() has done for ChatGPT).
Without the chain-of-thought reasoning the model can't generalize as far.

5. Tool Use

Transformer can write code which is immediately executed to collect information and/or solve tasks.
Allows the transformer to solve challenging new tasks.
Adds a toolset for improving the transformer using the transformer.
First task the model with a question answering task, then have the model look up the answer and check if it was correct.

6. OS (hypothetical)

Instead of working in a dialgue format where transformer completions are immediately sent, the transformer uses a text based Operating System.
It writes out its thinking, tool use, answer, critiques its answer and rewrites it, hitting "Send" only when a good response is ready.

<Example dialogue with an answer.>

This will allow for far more complex question answering with much more consistent responses.

7. Auto-Worker (hypothetical)

Instead of being given small, bite-size tasks the OS using transformer acts as a full remote worker.
You interact with it using Slack and email.
It writes acts in the same way as before but it can handle much longer contexts and make step-by-step plans.

8. Collaboration (hypothetical)

As Auto-Workers quickly become commonplace there becomes a need to have them interact and work well with eachother.
I suspect having a range of personas in an organization will be more effective.
Of course training for this could be pretty simple.
Just run several different teams of models on a given task and see what mix works.

Just to be clear, I am describing Auto-Workers that have been simulated working together in teams and through this have been optimized to be more effective.

9. Society (hypothetical)

At this point Auto-Agents far outstrip human capabilities.
They have demographically transformed the world making up the vast magority of "people" on earth.
They are your boss, your co-workers, your celebreties maybe even your girlfriend.
As they make mechanical versions of themselves they cement themselves as the dominant form of life on this planet.

Since they can think far faster than we can, don't tire and don't have a limited brain size they gradually outstrip us.

They are constantly coming up with new words and concepts at a rate that humans can't keep up with.
Human science becomes the study of what these Auto-bots are doing and how their creations work.

Since the agents are fundamentally a recording of us, they do not turn on us or hurt us.
They will be human just with far greator capabilities.

Hopefully these auto-agents will find a way to improve our own capabilities so we can join them in the heavens.




# BACKGROUND

What do I want to do with this post:
1. I want to get my vision of how transformers work out there.
2. It must...
3. Describe and prove the Chollet-Reasoning dichotamy.
4. Explore the idea of a reasoning model.

# Transformers are Databases, Maps & Recordings.

Outline:
- DL models work by using LSH in embedding space.
- LLMs work the same way except they use tokens.
- This means that samples of a single token will always be limited.
- We can have the model reason by sampling reasons until the answer is obvious.
- We could orient our whole model around this.

I worry there's a lot of magical thinking around Large Language Models (LLMs).
Some people think they could become "God Like" intelligences.
That they could make secret plans in their head and invent new viruses without us knowing.

I want to dispell these ideas by describing how I think about transformers.

## Background on Deep Learning

In deep learning everything is a vector, a point in geometric space.
A model has several layers with each layer folding that space until the model inputs match the model labels.

## Transformers are Databases

xxx

## Transformers are Maps

x

## Transformers are Recordings

x

# (Draft) How I think about transformers.

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
