---
aliases:
- /games/simulation/2020/07/08/An Avatar game with realistic physics
categories:
- games
- simulation
date: '2020-07-08'
description: Finding the physics of water bending.
image: https://raw.githubusercontent.com/Fraser-Greenlee/fastpages/master/images/katara_waterbend_arrows.gif
layout: post
title: An Avatar game with realistic physics

---

After watching [Avatar: The Last Airbender](https://www.imdb.com/title/tt0417299/) I wanted to experience bending the elements just like in the show.
Of course actually doing this is impossible but could a game give that feeling?

![GIF of katara water bending.]({{ site.baseurl }}/images/katara_waterbend.gif "See the smooth movement of the water.")

It turns out that you can achieve a compelling water bendning effect using Unity!
Here's the end result.

{% twitter https://twitter.com/i/status/1295012224793227264 %}

## So how did I do this?

Before jumping into 3D lets consider the problem in just 2 dimensions.
[Corona Labs](https://coronalabs.com) lets you make 2D cross-platform games and it comes with a realistic particle simulator.

It comes with this demo below, **click below** to try it!

<!-- {% raw %} -->
<figure class="iframe">
    <iframe src="/games/LiquidFun-ColorFaucet"></iframe>
</figure>
<!-- {% endraw %} -->

This gives some interaction with particles but doesn't create the smooth flows of water you see in the show.

It works by making all particles within the orange box match the box's velocity.
This is done by repeatedly running [`queryRegion`](https://docs.coronalabs.com/api/type/ParticleSystem/queryRegion.html) which sets particle velocity in a given region.
Notably this allows incrimenting particle velocity as well.

Lets picture the first GIF but with imagined forces on the water drawn as arrows.

![Katara water bending.]({{ site.baseurl }}/images/katara_waterbend_arrows.gif "The arrows denote forces on the water.")

Now to get a bending effect we can recreate the above GIF it with multiple `queryRegion` boxes.

Using the grid above, when a user taps the screen a ring of cells are updated with each pointing to the cursor.
To ensure the cursor is always in the middle of a grid cell the whole grid is shifted as the cursor moves between cells.

For cell values I make the magnitude's greater for further out cells as I found this better holds the particles together.
To get long streams of water I gradually decrease old cell values.

Below I show the cell values with white arrows (longer for greator velocity incriments).

**Try water bending below.**

<!-- {% raw %} -->
<figure class="iframe">
    <iframe src="/games/LiquidFun-ColorFaucet-Bending"></iframe>
</figure>
<!-- {% endraw %} -->

Then by making particles with different physical properties you get different materials.
Ice is a solid group of particles, green acid mixes colour with the blue water, slime is a sticky group of particles while mud is viscous.

{% include video.html url="/videos/water-materials.mp4" %}

{% include video.html url="/videos/firebend-combat.mp4" %}

{% include video.html url="/videos/water-fight.mp4" %}

Checkout the 2D source [here](https://github.com/Fraser-Greenlee/benders).

## 3D bending

Now that our 2D bending is pretty cool we've just got to extend it into 3D!

First we can use [ObiFluids](http://obi.virtualmethodstudio.com) to simulate particles in 3D.
Sadly it doesn't come with a native `queryRegion` method but we can just make one by partitioning space into a 3D grid.

When running the code iterates over every particle to find its region & adjusts the velocity in the same way as before.

This could clearly make a compelling VR game, unfortunatley I am too invested in an ML project right now to do more work.
If you would like any other implementation details feel free to reach out to me on [Twitter](http://twitter.com/FraserGreenlee).

{% twitter https://twitter.com/i/status/1295012224793227264 %}
