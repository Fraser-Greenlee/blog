# Picture-puzzle images

The picture levels (12–15) slice an image into tiles. To use your own images:

1. Drop image files into this folder, e.g. `fish.jpg`, `wave.png`.
2. List them in `manifest.json`:

   ```json
   ["fish.jpg", "wave.png"]
   ```

Each board picks one of the listed images at random and slices it into an
n×n grid. **Roughly square images work best**, and images with clear local
detail make individual tiles easy to tell apart.

If `manifest.json` is empty (or missing), the game falls back to procedurally
generated patterns, so picture levels always work with no assets.
